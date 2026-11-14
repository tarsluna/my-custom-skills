import type { CSSProperties } from 'react';
import type { CreativeItem, Format, PageCopy, PublicAudit } from '@/lib/types';
import { safeImg } from '@/lib/safe';
import { SheetHead } from './Sheet';

const RATIO: Record<Format, number> = { '4:5': 0.8, '9:16': 0.5625, '1:1': 1 };
const WORD = ['zéro', 'une', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix'];

const ratio = (f: Format) => ({ ['--r' as string]: RATIO[f] ?? 0.8 }) as CSSProperties;
const num = (i: number) => String(i).padStart(2, '0');
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

const euros = (n: number) => `${n}\u00a0€`;

function Cost({ value, label }: { value: number; label: string }) {
  return (
    <p className="cost">
      <span className="cost__value">{euros(value)}</span>
      <span className="cost__label">{label}</span>
    </p>
  );
}

function VisibleCreative({ c, column, copy }: { c: CreativeItem; column: number; copy: PageCopy }) {
  const src = safeImg(c.imageUrl);
  return (
    <article className="crea" style={{ gridColumn: column, gridRow: '1 / span 2' }}>
      <div className="crea__stand" style={ratio(c.format)}>
        <p className="crea__label">
          <span>{num(c.index)}</span>
          <span>{c.concept}</span>
          <span>{c.format}</span>
        </p>
        <figure className="crea__frame" data-m="rise">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {src ? <img src={src} alt={c.headline ?? c.concept} loading="lazy" /> : null}
        </figure>
      </div>
      <div className="crea__text">
        {c.estimatedCostEur !== null ? <Cost value={c.estimatedCostEur} label={copy.costLabel} /> : null}
        <p className="crea__note">{copy.conceptNote}</p>
        {c.headline ? <h3 className="d4">{c.headline}</h3> : null}
        {c.primaryText ? <p className="crea__body">{c.primaryText}</p> : null}
        {c.bullets?.length ? (
          <ul className="crea__bullets">
            {c.bullets.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
        ) : null}
      </div>
    </article>
  );
}

function LockedTile({ c, copy }: { c: CreativeItem; copy: PageCopy }) {
  const src = safeImg(c.imageUrl);
  return (
    <figure className="vault__tile" style={ratio(c.format)}>
      {/* L'image est déjà floutée par le serveur : aucune retouche ici. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      {src ? <img src={src} alt="" loading="lazy" /> : null}
      {c.estimatedCostEur !== null ? (
        <figcaption className="vault__cost">
          <b>{euros(c.estimatedCostEur)}</b>
          <span>{copy.costLabelShort}</span>
        </figcaption>
      ) : null}
    </figure>
  );
}

/** Deux rangées de même hauteur : chaque image garde son format exact, sans recadrage. */
function balanceRows(items: CreativeItem[]): CreativeItem[][] {
  const a: CreativeItem[] = [];
  const b: CreativeItem[] = [];
  let sa = 0;
  let sb = 0;
  for (const c of [...items].sort((x, y) => RATIO[y.format] - RATIO[x.format])) {
    if (sa <= sb) {
      a.push(c);
      sa += RATIO[c.format];
    } else {
      b.push(c);
      sb += RATIO[c.format];
    }
  }
  return [a, b].filter((r) => r.length);
}

export function Creatives({ audit, n, total }: { audit: PublicAudit; n: number; total: number }) {
  const { business, creatives, copy } = audit;
  const sorted = [...creatives].sort((a, b) => a.index - b.index);
  const visible = sorted.filter((c) => !c.locked);
  const locked = sorted.filter((c) => c.locked);
  const rows = balanceRows(locked);
  const costs = creatives.map((c) => c.estimatedCostEur).filter((v): v is number => v !== null);
  const average = costs.length ? Math.round(costs.reduce((sum, v) => sum + v, 0) / costs.length) : 0;

  return (
    <section id="creatives" className="sheet sheet--ink">
      <div className="wrap">
        <SheetHead
          n={n}
          total={total}
          business={business.name}
          title={copy.creativesTitle}
          lead={copy.creativesLead}
        />

        {average ? (
          <div className="cost-summary" data-m="up">
            <p className="cost-summary__value">{euros(average)}</p>
            <p className="cost-summary__label">{copy.costAverageLabel}</p>
          </div>
        ) : null}

        {visible.length ? (
          <div className="crea-row" style={{ ['--n' as string]: Math.min(visible.length, 3) }}>
            {visible.slice(0, 3).map((c, i) => (
              <VisibleCreative key={c.id} c={c} column={i + 1} copy={copy} />
            ))}
            <div className="crea-row__ground" data-m="draw" aria-hidden="true">
              <i />
            </div>
          </div>
        ) : null}

        {locked.length ? (
          <div className="vault">
            <div className="vault__wall">
              {rows.map((row, i) => (
                <div className="vault__row" key={i}>
                  {row.map((c) => (
                    <LockedTile key={c.id} c={c} copy={copy} />
                  ))}
                </div>
              ))}
            </div>
            <div className="vault__veil">
              <p className="mono-tag vault__tag">{cap(WORD[locked.length] ?? String(locked.length))} autres créatives</p>
              <p className="d2 vault__line">{copy.lockedSentence}</p>
              <p className="crea__note vault__note">{copy.conceptNote}</p>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
