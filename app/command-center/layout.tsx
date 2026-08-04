import Image from 'next/image';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import SignOutButton from '@/app/components/SignOutButton';
import styles from './layout.module.css';

export default async function CommandCenterLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession(authOptions);

  return (
    <>
      <nav className={styles.nav}>
        <div className={styles.brand}>
          PROFIT<span className={styles.brandAccent}>ENGINE</span>
          <span className={styles.brandSub}>Command Center</span>
        </div>
        {session?.user && (
          <div className={styles.user}>
            {session.user.image && (
              <Image
                src={session.user.image}
                alt={session.user.name ?? 'User'}
                width={28}
                height={28}
                style={{ borderRadius: '50%', border: '1px solid #1f2a3a' }}
                priority={false}
              />
            )}
            <span className={styles.email}>{session.user.email}</span>
            <SignOutButton className={styles.signOut} />
          </div>
        )}
      </nav>
      {children}
    </>
  );
}
