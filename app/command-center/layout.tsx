import Image from 'next/image';
import Link from 'next/link';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { normalizeRole, type Role, ROLE_ACCESS } from '@/lib/role';
import SignOutButton from '@/app/components/SignOutButton';
import ThemeToggle from '@/app/components/ThemeToggle';
import styles from './layout.module.css';

function sectionNav(role: Role) {
  return ROLE_ACCESS[role].map((section) => (
    <Link key={section} className={styles.sectionLink} href={`/command-center/${section}`}>
      {section}
    </Link>
  ));
}

export default async function CommandCenterLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession(authOptions);
  const role = normalizeRole(session?.user?.role);

  return (
    <>
      <nav className={styles.nav}>
        <div className={styles.brand}>
          PROFIT<span className={styles.brandAccent}>ENGINE</span>
          <span className={styles.brandSub}>Command Center</span>
          <span className={styles.roleBadge}>{role}</span>
        </div>
        {session?.user && (
          <div className={styles.user}>
            {session.user.image && (
              <Image
                src={session.user.image}
                alt={session.user.name ?? 'User'}
                width={28}
                height={28}
                style={{ borderRadius: '50%', border: '1px solid var(--c2-border)' }}
                priority={false}
              />
            )}
            <span className={styles.email}>{session.user.email}</span>
            <ThemeToggle />
            <SignOutButton className={styles.signOut} />
          </div>
        )}
      </nav>
      <div className={styles.sectionNav}>{sectionNav(role)}</div>
      {children}
    </>
  );
}
