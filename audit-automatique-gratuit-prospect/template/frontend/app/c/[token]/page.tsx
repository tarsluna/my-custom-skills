import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { getPublicAudit } from '@/lib/audits';
import { AuditPage } from '@/components/audit/AuditPage';
import { StatusScreen } from '@/components/audit/StatusScreen';
import { AutoRefresh } from '@/components/audit/AutoRefresh';
import { safeHref } from '@/lib/safe';
import '@/components/audit/audit.css';

export const dynamic = 'force-dynamic';

type Props = { params: Promise<{ token: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { token } = await params;
  const res = await getPublicAudit(token);
  const name = res.kind === 'ok' ? res.audit.business?.name : null;
  return {
    title: name ? `${name} · Audit` : 'Audit',
    robots: { index: false, follow: false, nocache: true, googleBot: { index: false, follow: false } },
    referrer: 'no-referrer',
  };
}

export default async function Page({ params }: Props) {
  const { token } = await params;
  const res = await getPublicAudit(token);

  if (res.kind === 'not_found') notFound();

  if (res.kind === 'unavailable') {
    return (
      <>
        <StatusScreen
          tag="Un instant"
          title="Votre audit revient dans un instant."
          body="Cette page se recharge seule."
          progress
        />
        <AutoRefresh every={15000} />
      </>
    );
  }

  const { audit } = res;

  if (audit.status === 'processing') {
    const name = audit.business?.name && audit.business.name !== audit.business.domain ? audit.business.name : null;
    return (
      <>
        <StatusScreen
          tag="Relevé en cours"
          title={name ? `Nous préparons votre audit, ${name}.` : 'Nous préparons votre audit.'}
          body="Votre site, vos concurrents, vos créatives : tout se prépare. Cette page se recharge seule."
          progress
        />
        <AutoRefresh every={8000} />
      </>
    );
  }

  if (audit.status === 'failed') {
    const booking = safeHref(audit.bookingUrl);
    return (
      <StatusScreen
        tag="Audit"
        title={audit.business?.name && audit.business.name !== audit.business.domain ? `Votre audit est en préparation, ${audit.business.name}.` : 'Votre audit est en préparation.'}
        body="Nous le terminons à la main. Vous le recevrez avant notre rendez-vous."
        action={booking ? { href: booking, label: 'Voir mon rendez-vous' } : undefined}
      />
    );
  }

  return <AuditPage audit={audit} />;
}
