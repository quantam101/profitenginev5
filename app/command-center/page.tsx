import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { normalizeRole, ROLE_ACCESS } from '@/lib/role';

export const dynamic = 'force-dynamic';

export default async function CommandCenterRoot() {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    redirect('/sign-in');
  }
  const role = normalizeRole(session.user.role);
  const first = ROLE_ACCESS[role][0] ?? 'agents';
  redirect(`/command-center/${first}`);
}
