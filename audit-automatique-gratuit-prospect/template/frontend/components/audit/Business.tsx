import type { PublicAudit } from '@/lib/types';
import { swatches } from '@/lib/palette';
import { hostOf, safeHref } from '@/lib/safe';
import { SheetHead } from './Sheet';

function ChainDim({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="chain">
      <p className="chain__label">{label}</p>
      <ul className="chain__row">
        {items.map((t) => (
          <li key={t} style={{ flexGrow: Math.max(6, t.length) }}>
            <span>{t}</span>
            <i aria-hidden="true" />
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Business({ audit, n, total }: { audit: PublicAudit; n: number; total: number }) {
  const { business } = audit;
  const zone = [business.city, business.region].filter(Boolean).join(', ');
  const site = safeHref(business.websiteUrl);
  const tints = swatches(business.palette);

  return (
    <section id="business" className="sheet sheet--stone">
      <div className="wrap">
        <SheetHead n={n} total={total} business={business.name} title={audit.copy.businessTitle} />

        <div className="understood">
          <p className="understood__summary d3" data-m="up">
            {business.summary || [business.name, business.professionLabel].filter(Boolean).join(', ')}
          </p>

          <div className="cartouche" data-m="up">
            <p className="cartouche__head">
              <span>Fiche</span>
              <span>Audit {audit.operator.name}</span>
            </p>
            <dl>
              <div>
                <dt>Entreprise</dt>
                <dd className="cartouche__name">{business.name}</dd>
              </div>
              {business.professionLabel ? (
                <div>
                  <dt>Métier</dt>
                  <dd>{business.professionLabel}</dd>
                </div>
              ) : null}
              {zone ? (
                <div>
                  <dt>Zone</dt>
                  <dd>{zone}</dd>
                </div>
              ) : null}
              {site ? (
                <div>
                  <dt>Site</dt>
                  <dd>
                    <a href={site} target="_blank" rel="noopener noreferrer">
                      {hostOf(site)}
                    </a>
                  </dd>
                </div>
              ) : null}
            </dl>
            {tints.length ? (
              <div className="swatches">
                <p>Votre palette, relevée sur votre site</p>
                <ul>
                  {tints.map((s) => (
                    <li key={s.key}>
                      <i style={{ background: s.hex }} />
                      <span>{s.hex}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </div>

        <ChainDim label="Spécialités" items={business.specialties} />
        <ChainDim label="Réalisations" items={business.projectTypes} />
      </div>
    </section>
  );
}
