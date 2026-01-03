import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

const DASHBOARD_EMAIL = process.env.DASHBOARD_EMAIL || '';
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || '').split(',').map(e => e.trim().toLowerCase());

export async function GET() {
  try {
    const googleSession = await getServerSession(authOptions);
    if (googleSession?.user?.email) {
      const userEmail = googleSession.user.email.toLowerCase();
      if (ADMIN_EMAILS.includes(userEmail)) {
        return NextResponse.json({
          authenticated: true,
          authType: 'google',
          user: {
            email: googleSession.user.email,
            name: googleSession.user.name || 'Admin',
          }
        });
      }
    }

    const cookieStore = await cookies();
    const adminToken = cookieStore.get('admin_token');
    if (adminToken?.value) {
      try {
        const decoded = Buffer.from(adminToken.value, 'base64').toString();
        const [email] = decoded.split(':');
        if (email.toLowerCase() === DASHBOARD_EMAIL.toLowerCase()) {
          return NextResponse.json({
            authenticated: true,
            authType: 'password',
            user: {
              email: email,
              name: 'Dashboard Admin',
            }
          });
        }
      } catch {
        // Invalid token
      }
    }

    return NextResponse.json({ authenticated: false });
  } catch (error) {
    console.error('[Admin Session] Error:', error);
    return NextResponse.json({ authenticated: false });
  }
}
