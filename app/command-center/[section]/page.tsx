import { notFound, redirect } from 'next/navigation';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { canAccess } from '@/lib/role';

import { StatusPage } from '../StatusPage';
import { commandCenterStatus } from '../statusData';

export const dynamic = 'force-dynamic';

type Section = keyof typeof commandCenterStatus;

const sections = Object.keys(commandCenterStatus) as Section[];

export default async function Page({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    redirect('/sign-in');
  }

  if (!sections.includes(section as Section) || !canAccess(session.user.role ?? '', section)) {
    notFound();
  }

  return <StatusPage {...commandCenterStatus[section as Section]} />;
}
