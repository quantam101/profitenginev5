import { notFound } from 'next/navigation';

import { StatusPage } from '../StatusPage';
import { commandCenterStatus } from '../statusData';

type Section = keyof typeof commandCenterStatus;

const sections = Object.keys(commandCenterStatus) as Section[];

export function generateStaticParams() {
  return sections.map((section) => ({ section }));
}

export default async function Page({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  if (!sections.includes(section as Section)) {
    notFound();
  }
  return <StatusPage {...commandCenterStatus[section as Section]} />;
}
