import { notFound, redirect } from 'next/navigation';
import { isAdmin } from '@/lib/session';
import { adminDetail } from '@/lib/admin';
import { AuditDetail } from '@/components/admin/AuditDetail';

export const dynamic = 'force-dynamic';

export default async function AuditDetailPage({ params }: { params: Promise<{ id: string }> }) {
  if (!(await isAdmin())) redirect('/admin/login');
  const { id } = await params;
  const audit = await adminDetail(id);
  if (!audit) notFound();
  return <AuditDetail initial={audit} />;
}
