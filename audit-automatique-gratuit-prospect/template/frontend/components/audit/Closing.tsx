import type { PublicAudit } from '@/lib/types';
import { meetingLong } from '@/lib/format';
import { safeHref, safeImg } from '@/lib/safe';
import { SheetHead } from './Sheet';
import { Teaser } from './Teaser';

export function Closing({ audit, n, total }: { audit: PublicAudit; n: number; total: number }) {
  const { business, meetingAt, bookingUrl, operator, copy } = audit;
  const when = meetingLong(meetingAt);
  const booking = safeHref(bookingUrl);
  const logo = safeImg(operator.logoUrl);

  return (
    <>
      <section id="suite" className="sheet sheet--ink">
        <div className="wrap">
          <SheetHead n={n} total={total} business={business.name} title={copy.nextTitle} />
          <Teaser items={copy.teaser} sentence={copy.lockedSentence} />
        </div>
      </section>

      <section className="fin">
        <div className="fin__copy">
          <h2 className="d1">{copy.closing}</h2>
          {when ? (
            <p className="fin__when">
              <span className="mono-tag">Notre rendez-vous</span>
              <span className="d3">{when.charAt(0).toUpperCase() + when.slice(1)}</span>
            </p>
          ) : booking ? (
            <a className="btn" href={booking} target="_blank" rel="noopener noreferrer">
              Choisir mon rendez-vous
            </a>
          ) : null}
        </div>
      </section>

      <footer className="foot">
        {logo ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img className="foot__word" src={logo} alt={operator.name} />
        ) : (
          <p className="foot__word--text">{operator.name}</p>
        )}
        {operator.motto ? <p className="d2 foot__motto">{operator.motto}</p> : null}
        <div className="foot__legal">
          <p>Cette page a été préparée pour {business.name}. Elle est privée.</p>
          <p>{copy.footerLegal}</p>
        </div>
      </footer>
    </>
  );
}
