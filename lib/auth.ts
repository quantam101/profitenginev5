import { type NextAuthOptions } from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';

type Role = 'admin' | 'operator' | 'auditor';

function resolveRole(email: string): Role {
  const admins = new Set((process.env.ADMIN_EMAILS ?? '').split(',').map((s) => s.trim()).filter(Boolean));
  const operators = new Set((process.env.OPERATOR_EMAILS ?? '').split(',').map((s) => s.trim()).filter(Boolean));
  if (admins.has(email)) return 'admin';
  if (operators.has(email)) return 'operator';
  return 'auditor';
}

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  pages: {
    signIn: '/sign-in',
  },
  session: {
    strategy: 'jwt',
  },
  callbacks: {
    async jwt({ token }) {
      if (token.email) {
        token.role = resolveRole(token.email as string);
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user && token.sub) {
        session.user.id = token.sub;
        session.user.role = (token.role as Role) ?? 'auditor';
      }
      return session;
    },
  },
};
