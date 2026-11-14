import type { PublicAudit } from '@/lib/types';
import { dayCount, km } from '@/lib/format';
import { safeHref, safeImg } from '@/lib/safe';
import { SheetHead } from './Sheet';

const roundUp = (n: number) => {
  const step = n > 200 ? 100 : n > 60 ? 50 : 20;
  return Math.ceil(n / step) * step;
};

/** Les repères trop proches se superposent en hauteur, jamais sur la distance réelle. */
function pinLevels(distances: Array<number | null>, max: number): number[] {
  const order = distances.map((d, i) => ({ d, i })).filter((x): x is { d: number; i: number } => x.d != null).sort((a, b) => a.d - b.d);
  const levels = new Array<number>(distances.length).fill(0);
  const lastAt: number[] = [];
  for (const { d, i } of order) {
    const x = (d / max) * 100;
    let lvl = 0;
    while (lastAt[lvl] !== undefined && x - lastAt[lvl] < 7) lvl += 1;
    lastAt[lvl] = x;
    levels[i] = lvl;
  }
  return levels;
}

function ScaleBar({ radius, distances, origin }: { radius: number | null; distances: Array<number | null>; origin: string }) {
  const known = distances.filter((d): d is number => d != null);
  const max = radius ?? (known.length ? roundUp(Math.max(...known)) : 100);
  const segments = 4;
  const levels = pinLevels(distances, max);
  return (
    <div className="scale" role="img" aria-label={`Échelle des distances, jusqu’à ${max} kilomètres autour de ${origin}`}>
      <div className="scale__bar">
        {Array.from({ length: segments }).map((_, i) => (
          <i key={i} className={i % 2 === 0 ? 'on' : ''} />
        ))}
        {distances.map((d, i) =>
          d == null ? null : (
            <span key={i} className="scale__pin" style={{ left: `${Math.min(100, (d / max) * 100)}%`, ['--lvl' as string]: levels[i] }}>
              {i + 1}
            </span>
          ),
        )}
      </div>
      <div className="scale__nums" aria-hidden="true">
        <span>0</span>
        <span>{Math.round(max / 2)}</span>
        <span>{max} km</span>
      </div>
      <p className="scale__origin">0 km : {origin}</p>
    </div>
  );
}

export function Competitors({ audit, n, total }: { audit: PublicAudit; n: number; total: number }) {
  const { business, competitors } = audit;
  const { radiusKm, widened, insights, items } = competitors;
  const origin = business.city ?? business.region ?? business.name;

  const title =
    items.length === 0
      ? 'Vos concurrents n’investissent pas encore près de vous.'
      : radiusKm == null
        ? 'Les concurrents qui investissent déjà, partout dans le pays.'
        : widened
          ? `Les concurrents qui investissent déjà, dans un rayon de ${radiusKm}\u00A0km.`
          : 'Vos concurrents qui investissent déjà près de vous.';

  const reach =
    radiusKm == null
      ? 'Relevé étendu à tout le pays.'
      : widened
        ? `Relevé étendu à ${radiusKm}\u00A0km autour de ${origin}.`
        : `Relevé dans un rayon de ${radiusKm}\u00A0km autour de ${origin}.`;

  return (
    <section id="concurrents" className="sheet sheet--ink">
      <div className="wrap">
        <SheetHead
          n={n}
          total={total}
          business={business.name}
          title={title}
          lead={items.length === 0 ? 'Aucune publicité active d’une entreprise de votre métier dans cette zone. La place est libre.' : undefined}
        />

        {items.length > 0 ? (
          <>
            <div className="reach">
              <div>
                <p className="mono-tag">Rayon réellement atteint</p>
                <p className="d3 reach__value">{reach}</p>
              </div>
              <ScaleBar radius={radiusKm} distances={items.map((c) => c.distanceKm)} origin={origin} />
            </div>

            <ol className="rivals">
              {items.map((c, i) => {
                const img = safeImg(c.imageUrl);
                const link = safeHref(c.adLibraryUrl);
                const logo = safeImg(c.logoUrl);
                const dist = km(c.distanceKm);
                const days = dayCount(c.activeDays);
                return (
                  <li key={`${c.pageName}-${i}`} className="rival" data-m="up">
                    <div className="rival__tag">
                      <b>{i + 1}</b>
                      <span>Publicité active</span>
                    </div>
                    {img ? (
                      <figure className="rival__ad">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={img} alt={`Publicité de ${c.pageName}`} loading="lazy" />
                      </figure>
                    ) : null}
                    <div className="rival__who">
                      {logo ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={logo} alt="" className="rival__logo" loading="lazy" />
                      ) : null}
                      <div>
                        <h3 className="d4">{c.pageName}</h3>
                        {c.city ? <p className="rival__city">{c.city}</p> : null}
                      </div>
                    </div>
                    <dl className="dims">
                      {dist ? (
                        <div>
                          <dt>Distance</dt>
                          <dd>{dist}</dd>
                        </div>
                      ) : null}
                      {days ? (
                        <div>
                          <dt>En diffusion</dt>
                          <dd>{days}</dd>
                        </div>
                      ) : null}
                    </dl>
                    <div className="rival__copy">
                      {c.title ? <p className="rival__head">{c.title}</p> : null}
                      <p className="rival__body">{c.body}</p>
                    </div>
                    <div className="rival__why">
                      <p className="mono-tag">Pourquoi cela compte</p>
                      <p>{c.why}</p>
                    </div>
                    {link ? (
                      <a className="btn btn--line btn--sm" href={link} target="_blank" rel="noopener noreferrer">
                        Voir dans la bibliothèque publicitaire
                      </a>
                    ) : null}
                  </li>
                );
              })}
              {insights.length > 0 ? (
                <li className="insights" style={{ ['--s3' as string]: 3 - (items.length % 3), ['--s2' as string]: 2 - (items.length % 2) }}>
                  <p className="mono-tag">Ce que ce relevé nous dit</p>
                  <ul>
                    {insights.map((t) => (
                      <li key={t} className="d3" data-m="up">
                        {t}
                      </li>
                    ))}
                  </ul>
                </li>
              ) : null}
            </ol>
          </>
        ) : null}
      </div>
    </section>
  );
}
