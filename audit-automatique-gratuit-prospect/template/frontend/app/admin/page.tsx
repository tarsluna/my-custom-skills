import { redirect } from 'next/navigation';
import { isAdmin } from '@/lib/session';
import { adminList, adminStats } from '@/lib/admin';
import { AdminHome } from '@/components/admin/AdminHome';

export const dynamic = 'force-dynamic';

export default async function AdminPage() {
  if (!(await isAdmin())) redirect('/admin/login');
  const [audits, stats] = await Promise.all([adminList(null, null), adminStats()]);
  return <AdminHome initialAudits={audits ?? []} initialStats={stats} backendDown={audits === null} />;
}
