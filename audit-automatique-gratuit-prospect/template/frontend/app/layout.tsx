import type { Metadata, Viewport } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const display = Inter({ subsets: ['latin'], weight: ['300', '400'], variable: '--font-display', display: 'swap' });
const body = Inter({ subsets: ['latin'], weight: ['400', '500'], variable: '--font-body', display: 'swap' });
const code = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500'], variable: '--font-code', display: 'swap' });

export const metadata: Metadata = {
  title: 'Audit',
  robots: { index: false, follow: false, nocache: true },
  referrer: 'no-referrer',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  themeColor: '#0f1115',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={`${display.variable} ${body.variable} ${code.variable}`}>
      <body>{children}</body>
    </html>
  );
}
