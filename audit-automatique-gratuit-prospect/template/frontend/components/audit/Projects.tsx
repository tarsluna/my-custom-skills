import type { PublicAudit } from '@/lib/types';
import { hostOf, safeHref, safeImg } from '@/lib/safe';
import { SheetHead } from './Sheet';

/* Rangées éditoriales : même hauteur d'image dans une rangée, aucune case orpheline. */
const LAYOUTS: Record<number, number[]> = {
  3: [7, 5, 12],
  4: [7, 5, 6, 6],
  5: [7, 5, 4, 4, 4],
  6: [7, 5, 3, 3, 3, 3],
  7: [7, 5, 4, 4, 4, 6, 6],
};

export function Projects({ audit, n, total }: { audit: PublicAudit; n: number; total: number }) {
  const { business, projects } = audit;
  const list = projects.slice(0, 7);

  return (
    <section id="projets" className="sheet sheet--stone">
      <div className="wrap">
        <SheetHead
          n={n}
          total={total}
          business={business.name}
          title={audit.copy.projectsTitle}
          lead={audit.copy.projectsLead}
        />
        <ul className={`works works--${Math.min(list.length, 7)}`}>
          {list.map((p, i) => {
            const src = safeImg(p.imageUrl);
            const link = safeHref(p.sourceUrl);
            const body = (
              <>
                <figure className="work__img" data-m="rise">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  {src ? <img src={src} alt={p.title} loading="lazy" /> : null}
                </figure>
                <div className="work__meta">
                  <h3>{p.title}</h3>
                  <p>
                    {p.location ? <span>{p.location}</span> : null}
                    {link ? <span className="work__src">Source : {hostOf(link)}</span> : null}
                  </p>
                </div>
              </>
            );
            return (
              <li key={`${p.title}-${i}`} className={`work work--w${LAYOUTS[list.length]?.[i] ?? 6}`}>
                {link ? (
                  <a href={link} target="_blank" rel="noopener noreferrer">
                    {body}
                  </a>
                ) : (
                  body
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
