import { redirect } from 'next/navigation';
import { isAdmin } from '@/lib/session';
import { LoginForm } from '@/components/admin/LoginForm';

export const dynamic = 'force-dynamic';

export default async function LoginPage() {
  if (await isAdmin()) redirect('/admin');
  return (
    <main className="adm-login">
      <h1 className="adm-login__title">Audits</h1>
      <LoginForm />
    </main>
  );
}
