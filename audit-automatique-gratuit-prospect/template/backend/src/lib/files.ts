import { randomBytes } from 'node:crypto';
import { mkdir, rename, rm, stat, writeFile, copyFile } from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';
import { cfg } from '../config.js';
import { query, type Db } from '../db/pool.js';

export type MediaKind = 'logo' | 'project' | 'competitor_image' | 'competitor_logo' | 'screenshot' | 'creative_original' | 'creative_display' | 'creative_blur' | 'creative_thumb';

export function auditRoot(auditId: string): string {
  return path.join(cfg().DATA_DIR, 'audits', auditId);
}
export function mediaDir(auditId: string): string {
  return path.join(auditRoot(auditId), 'media');
}
export function workDir(auditId: string, name: string): string {
  return path.join(auditRoot(auditId), 'work', name);
}

/** 128 bits aléatoires par fichier : un nom ne se déduit d'aucun autre. */
export function randomFileName(ext: string): string {
  return `${randomBytes(16).toString('hex')}.${ext.replace(/^\./, '').toLowerCase()}`;
}

export const CONTENT_TYPES: Record<string, string> = { png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', webp: 'image/webp', svg: 'image/svg+xml' };

export async function registerFile(
  auditId: string,
  kind: MediaKind,
  source: Buffer | { path: string; move: boolean },
  ext: string,
  options: { creativeId?: string | null; db?: Db } = {},
): Promise<{ fileName: string; path: string }> {
  const dir = mediaDir(auditId);
  await mkdir(dir, { recursive: true });
  const fileName = randomFileName(ext);
  const dest = path.join(dir, fileName);
  let bytes: number;
  if (Buffer.isBuffer(source)) {
    await writeFile(dest, source);
    bytes = source.length;
  } else {
    if (source.move) await rename(source.path, dest).catch(() => copyFile(source.path, dest));
    else await copyFile(source.path, dest);
    bytes = (await stat(dest)).size;
  }
  await query(
    'INSERT INTO media (file_name, audit_id, creative_id, kind, path, content_type, bytes) VALUES ($1,$2,$3,$4,$5,$6,$7)',
    [fileName, auditId, options.creativeId ?? null, kind, dest, CONTENT_TYPES[ext] ?? 'application/octet-stream', bytes],
    options.db,
  );
  return { fileName, path: dest };
}

/** Recopie une image téléchargée, ré-encodée et bornée : les URL distantes expirent. */
export async function saveImageBuffer(
  auditId: string,
  kind: MediaKind,
  buffer: Buffer,
  options: { maxSide: number; minSide?: number; creativeId?: string | null },
): Promise<{ fileName: string; path: string; width: number; height: number } | null> {
  const meta = await sharp(buffer, { failOn: 'error' }).metadata();
  const w = meta.width ?? 0;
  const h = meta.height ?? 0;
  if (!w || !h) return null;
  if (options.minSide && Math.max(w, h) < options.minSide) return null;
  const output = await sharp(buffer, { failOn: 'error' })
    .rotate()
    .resize({ width: options.maxSide, height: options.maxSide, fit: 'inside', withoutEnlargement: true })
    .jpeg({ quality: 84, mozjpeg: true })
    .toBuffer({ resolveWithObject: true });
  const saved = await registerFile(auditId, kind, output.data, 'jpg', { creativeId: options.creativeId });
  return { ...saved, width: output.info.width, height: output.info.height };
}

export async function purgeAuditFiles(auditId: string): Promise<void> {
  await rm(auditRoot(auditId), { recursive: true, force: true });
  await query('DELETE FROM media WHERE audit_id=$1', [auditId]);
}

/** Efface les fichiers d'une étape avant de la rejouer, pour ne pas laisser d'orphelins après une reprise. */
export async function removeMediaByKinds(auditId: string, kinds: MediaKind[]): Promise<void> {
  const rows = await query<{ path: string }>('DELETE FROM media WHERE audit_id=$1 AND kind = ANY($2) RETURNING path', [auditId, kinds]);
  await Promise.all(rows.rows.map((r) => rm(r.path, { force: true })));
}

export async function removeMedia(fileNames: string[]): Promise<void> {
  if (!fileNames.length) return;
  const rows = await query<{ path: string }>('DELETE FROM media WHERE file_name = ANY($1) RETURNING path', [fileNames]);
  await Promise.all(rows.rows.map((r) => rm(r.path, { force: true })));
}

/** Règle unique d'accès public : le fichier d'origine n'en fait jamais partie. */
export function isPubliclyServable(kind: MediaKind, creativeLocked: boolean | null): boolean {
  switch (kind) {
    case 'logo':
    case 'project':
    case 'competitor_image':
    case 'competitor_logo':
    case 'creative_blur':
      return true;
    case 'creative_display':
      return creativeLocked === false;
    default:
      return false;
  }
}

export function publicMediaUrl(token: string, fileName: string): string {
  return `${cfg().PUBLIC_BASE_URL}/media/${token}/${fileName}`;
}

export function adminMediaUrl(auditId: string, fileName: string): string {
  return `${cfg().PUBLIC_BASE_URL}/admin/media/${auditId}/${fileName}`;
}
