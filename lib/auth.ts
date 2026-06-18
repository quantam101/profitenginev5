import { type NextAuthOptions } from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';

const googleClientId = process.env.GOOGLE_CLIENT_ID;
const googleClientSecret = process.env.GOOGLE_CLIENT_SECRET;
const nextAuthSecret = process.env.NEXTAUTH_SECRET;

export const authReady = Boolean(googleClientId && googleClientSecret && nextAuthSecret);

export const authOptions: NextAuthOptions = {
  secret: nextAuthSecret,
  providers: authReady
    ? [
        GoogleProvider({
          clientId: googleClientId as string,
          clientSecret: googleClientSecret as string,
        }),
      ]
    : [],
  pages: {
    signIn: '/sign-in',
  },
  session: {
    strategy: 'jwt',
  },
  callbacks: {
    async session({ session, token }) {
      if (session.user && token.sub) {
        (session.user as { id?: string }).id = token.sub;
      }
      return session;
    },
  },
};
