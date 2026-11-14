'use client';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function AutoRefresh({ every }: { every: number }) {
  const router = useRouter();
  useEffect(() => {
    const t = window.setInterval(() => router.refresh(), every);
    return () => window.clearInterval(t);
  }, [router, every]);
  return null;
}
