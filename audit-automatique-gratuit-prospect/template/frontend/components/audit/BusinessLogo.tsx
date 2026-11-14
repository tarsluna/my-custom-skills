'use client';

import { safeImg } from '@/lib/safe';
import { initials } from '@/lib/format';
import { usePlate } from './usePlate';

/* Le logo posé sur une plaque de la couleur de fond de son propre site : il reste lisible sans être redessiné. */
export function BusinessLogo({
  name,
  logoUrl,
  size = 'md',
}: {
  name: string;
  logoUrl: string | null | undefined;
  size?: 'sm' | 'md' | 'lg';
}) {
  const src = safeImg(logoUrl);
  const plate = usePlate(src);
  return (
    <span className={`plate plate--${size}`} style={plate ? { background: plate } : undefined}>
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt={`Logo ${name}`} />
      ) : (
        <span className="plate__mono" aria-label={name}>
          {initials(name)}
        </span>
      )}
    </span>
  );
}
