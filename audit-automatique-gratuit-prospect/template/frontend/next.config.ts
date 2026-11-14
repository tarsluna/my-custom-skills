import type { NextConfig } from 'next';

const privatePages = [
  { key: 'X-Robots-Tag', value: 'noindex, nofollow, noarchive' },
  { key: 'Referrer-Policy', value: 'no-referrer' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
];

const config: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  devIndicators: false,
  /* Le backend publie ses liens en /a/<jeton> : la page vit en /c/<jeton>. */
  async redirects() {
    return [{ source: '/a/:token', destination: '/c/:token', permanent: false }];
  },
  async headers() {
    return [
      { source: '/:path*', headers: privatePages },
      { source: '/((?!c/).*)', headers: [{ key: 'X-Frame-Options', value: 'DENY' }] },
      /* Aperçu dans votre CRM : FRAME_ANCESTORS=https://crm.exemple.fr. Par défaut, aucun cadre. */
      { source: '/c/:path*', headers: [{ key: 'Content-Security-Policy', value: `frame-ancestors ${process.env.FRAME_ANCESTORS?.trim() || "'none'"}` }] },
    ];
  },
};

export default config;
