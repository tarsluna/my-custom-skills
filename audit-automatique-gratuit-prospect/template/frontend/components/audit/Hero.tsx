import type { PublicAudit } from '@/lib/types';
import { meetingLong } from '@/lib/format';
import { hostOf, safeImg } from '@/lib/safe';
import { BusinessLogo } from './BusinessLogo';

export function Hero({ audit, sheets }: { audit: PublicAudit; sheets: { id: string; label: string }[] }) {
  const { business, contact, meetingAt, operator, copy } = audit;
  const when = meetingLong(meetingAt);
  const name = business.name.replace(/[.\s]+$/, '');
  const first = contact?.firstName?.trim();
  const logo = safeImg(operator.logoUrl);

  const eyebrow = first
    ? when
      ? `${first}, pour notre rendez-vous du ${when}.`
      : `${first}, en vue de notre rendez-vous.`
    : when
      ? `Pour notre rendez-vous du ${when}.`
      : 'En vue de notre rendez-vous.';

  const place = [business.professionLabel, business.city, hostOf(business.websiteUrl) ?? business.domain].filter(Boolean);
  const [before, after] = copy.title.includes(business.name) ? copy.title.split(business.name) : [copy.title, null];

  return (
    <section className="hero" data-m="hero">
      <div className="hero__stage">
        <header className="hero__bar">
          <div className="hero__marks">
            {logo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img className="hero__word" src={logo} alt={operator.name} />
            ) : (
              <span className="hero__word hero__word--text">{operator.name}</span>
            )}
            <i className="hero__x" aria-hidden="true">
              ×
            </i>
            <BusinessLogo name={business.name} logoUrl={business.logoUrl} />
          </div>
          <p className="hero__conf">Audit offert · Page privée</p>
        </header>

        <div className="hero__copy">
          <p className="hero__eyebrow">{eyebrow}</p>
          <h1 className={`d1 hero__title${name.length > 34 ? ' hero__title--long' : ''}`}>
            {before}
            {after !== null ? <span className="hero__name">{business.name}</span> : null}
            {after}
          </h1>
          <p className="hero__place">{place.join('  ·  ')}</p>
        </div>

        <div className="hero__foot">
          <div className="hero__ground" aria-hidden="true">
            <i />
          </div>
          <nav className="hero__sheets" aria-label="Sommaire de la page">
            {sheets.map((s, i) => (
              <a key={s.id} href={`#${s.id}`}>
                <b>{String(i + 1).padStart(2, '0')}</b>
                {s.label}
              </a>
            ))}
          </nav>
        </div>
      </div>
    </section>
  );
}
