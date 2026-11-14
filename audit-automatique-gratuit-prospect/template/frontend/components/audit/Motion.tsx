'use client';
import { useEffect } from 'react';

/* Tout le mouvement est lié au défilement : un seul calcul, une seule variable --p par élément. */
export function Motion() {
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const root = document.documentElement;
    root.classList.add('m-on');

    const els = Array.from(document.querySelectorAll<HTMLElement>('[data-m]'));
    const live = new Set<HTMLElement>();
    const smooth = (x: number) => x * x * (3 - 2 * x);
    const clamp = (x: number) => Math.min(1, Math.max(0, x));

    const compute = (el: HTMLElement) => {
      const vh = window.innerHeight;
      const rect = el.getBoundingClientRect();
      if (el.dataset.m === 'hero') {
        const span = rect.height - vh;
        const p = span > 0 ? clamp(-rect.top / span) : 0;
        el.style.setProperty('--p', p.toFixed(4));
        return;
      }
      const from = vh * Number(el.dataset.mFrom ?? 0.98);
      const to = vh * Number(el.dataset.mTo ?? 0.62);
      el.style.setProperty('--p', smooth(clamp((from - rect.top) / (from - to))).toFixed(4));
    };

    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          const el = e.target as HTMLElement;
          if (e.isIntersecting) {
            live.add(el);
            compute(el);
          } else {
            live.delete(el);
            compute(el);
          }
        }
      },
      { rootMargin: '25% 0px 25% 0px' },
    );
    els.forEach((el) => {
      compute(el);
      io.observe(el);
    });

    let raf = 0;
    const onScroll = () => {
      if (raf) return;
      raf = window.requestAnimationFrame(() => {
        raf = 0;
        live.forEach(compute);
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      io.disconnect();
      if (raf) window.cancelAnimationFrame(raf);
    };
  }, []);
  return null;
}
