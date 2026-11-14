import { randomBytes } from 'node:crypto';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';
import { OUTPUT_SIZE } from './concepts.js';
import type { CreativeFormat } from './types.js';

/** Recadre et met à l'échelle exacte du format, en sRGB opaque. */
export async function normalizeImage(rawPath: string, format: CreativeFormat): Promise<Buffer> {
  const { width, height } = OUTPUT_SIZE[format];
  return sharp(rawPath, { failOn: 'none' })
    .rotate()
    .resize(width, height, { fit: 'cover', position: 'centre', kernel: 'lanczos3' })
    .removeAlpha()
    .toColourspace('srgb')
    .png()
    .toBuffer();
}

function randomName(prefix: string, ext: string): string {
  return `${prefix}${randomBytes(12).toString('hex')}.${ext}`;
}

/** Trois fichiers aux noms indépendants, pour qu'on ne puisse pas déduire l'original du dérivé flouté. */
export function outputNames(index: number): { image: string; blur: string; thumb: string } {
  const prefix = `c${String(index).padStart(2, '0')}-`;
  return { image: randomName(prefix, 'jpg'), blur: randomName(prefix, 'webp'), thumb: randomName(prefix, 'webp') };
}

/**
 * Dérivé réellement flouté : l'image passe par une miniature de 24 pixels de large,
 * ce qui détruit définitivement toute lettre, puis remonte en dégradé doux. Un léger
 * grain évite les aplats en escalier.
 */
export async function writeBlur(image: Buffer, file: string): Promise<void> {
  const meta = await sharp(image).metadata();
  const w = 720;
  const h = Math.round((w * (meta.height ?? 900)) / (meta.width ?? 720));
  const tiny = await sharp(image).resize({ width: 24, kernel: 'cubic' }).removeAlpha().png().toBuffer();
  const grain = await sharp({
    create: { width: w, height: h, channels: 3, background: { r: 128, g: 128, b: 128 }, noise: { type: 'gaussian', mean: 128, sigma: 10 } },
  })
    .png()
    .toBuffer();
  await sharp(tiny)
    .resize(w, h, { kernel: 'cubic' })
    .blur(26)
    .modulate({ saturation: 1.18, brightness: 1.03 })
    .composite([{ input: grain, blend: 'soft-light' }])
    .webp({ quality: 74 })
    .toFile(file);
}

export async function writeFinal(image: Buffer, dir: string, index: number): Promise<{ imagePath: string; blurPath: string; thumbPath: string }> {
  await fs.mkdir(dir, { recursive: true });
  const names = outputNames(index);
  const imagePath = path.join(dir, names.image);
  const blurPath = path.join(dir, names.blur);
  const thumbPath = path.join(dir, names.thumb);
  await sharp(image).jpeg({ quality: 92, mozjpeg: true, chromaSubsampling: '4:4:4' }).toFile(imagePath);
  await writeBlur(image, blurPath);
  await sharp(image).resize({ width: 540, kernel: 'lanczos3' }).webp({ quality: 82 }).toFile(thumbPath);
  return { imagePath, blurPath, thumbPath };
}
