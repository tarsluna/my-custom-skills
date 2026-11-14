import type { PublicAudit } from '@/lib/types';
import { safeImg } from '@/lib/safe';
import { SheetHead, Ground } from './Sheet';
import { Phone } from './Phone';

export function Assistant({ audit, n, total }: { audit: PublicAudit; n: number; total: number }) {
  const { business, setter, token, copy } = audit;
  return (
    <section id="assistant" className="sheet sheet--dusk">
      <div className="wrap assistant">
        <div className="assistant__copy">
          <SheetHead
            n={n}
            total={total}
            business={business.name}
            title={copy.assistantTitle}
            lead={copy.assistantLead}
          />
          <ul className="notes">
            {copy.assistantNotes.map((note) => (
              <li key={note.tag} data-m="up">
                <span className="mono-tag">{note.tag}</span>
                <p>{note.text}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className="assistant__phone">
          <Phone
            token={token}
            businessName={business.name}
            logoUrl={safeImg(business.logoUrl)}
            firstMessage={setter.firstProspectMessage}
            suggested={setter.suggestedReplies}
          />
          <Ground note="Sur le téléphone de vos clients" />
        </div>
      </div>
    </section>
  );
}
