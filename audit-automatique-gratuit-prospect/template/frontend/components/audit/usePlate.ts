'use client';

import { useEffect, useState } from 'react';

const lumOf = (r: number, g: number, b: number) => (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;

function cssColorLum(value: string): number | null {
  const m = value.trim().match(/^#([0-9a-f]{6})$/i);
  if (!m) return null;
  const n = parseInt(m[1], 16);
  return lumOf((n >> 16) & 255, (n >> 8) & 255, n & 255);
}

/**
 * Un logo clair sur un fond relevé clair (ou l'inverse) disparaîtrait.
 * Si le logo est transparent et trop proche de sa plaque, on passe à l'autre matière.
 * En cas d'image non lisible (CORS), la plaque par défaut reste en place.
 */
export function usePlate(src: string | null): string | undefined {
  const [plate, setPlate] = useState<string>();

  useEffect(() => {
    setPlate(undefined);
    if (!src) return;
    let alive = true;
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      if (!alive) return;
      try {
        const size = 48;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        if (!ctx) return;
        ctx.drawImage(img, 0, 0, size, size);
        const data = ctx.getImageData(0, 0, size, size).data;
        let sum = 0;
        let solid = 0;
        for (let i = 0; i < data.length; i += 4) {
          if (data[i + 3] < 40) continue;
          sum += lumOf(data[i], data[i + 1], data[i + 2]);
          solid += 1;
        }
        const total = size * size;
        if (solid === 0 || solid > total * 0.92) return; // Un logo opaque porte déjà son propre fond.
        const logoLum = sum / solid;
        const host = document.querySelector('.audit');
        const plateLum = host ? cssColorLum(getComputedStyle(host).getPropertyValue('--biz-plate')) : null;
        if (plateLum === null || Math.abs(logoLum - plateLum) >= 0.22) return;
        setPlate(logoLum > 0.5 ? '#100F0D' : '#EFE9DD');
      } catch {
        /* Image non lisible : on garde la plaque de l’entreprise. */
      }
    };
    img.src = src;
    return () => {
      alive = false;
    };
  }, [src]);

  return plate;
}
