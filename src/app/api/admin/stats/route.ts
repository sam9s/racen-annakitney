import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { cookies } from 'next/headers';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8080';
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || '').split(',').map(e => e.trim().toLowerCase());
const DASHBOARD_EMAIL = process.env.DASHBOARD_EMAIL || '';

async function isAuthorized(): Promise<boolean> {
  const googleSession = await getServerSession(authOptions);
  if (googleSession?.user?.email) {
    const userEmail = googleSession.user.email.toLowerCase();
    if (ADMIN_EMAILS.includes(userEmail)) {
      return true;
    }
  }
  
  const cookieStore = await cookies();
  const adminToken = cookieStore.get('admin_token');
  if (adminToken?.value) {
    try {
      const decoded = Buffer.from(adminToken.value, 'base64').toString();
      const [email] = decoded.split(':');
      if (email.toLowerCase() === DASHBOARD_EMAIL.toLowerCase()) {
        return true;
      }
    } catch {
      // Invalid token
    }
  }
  
  return false;
}

export async function GET(request: NextRequest) {
  try {
    const authorized = await isAuthorized();
    if (!authorized) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const range = searchParams.get('range') || '7d';

    const response = await fetch(`${BACKEND_URL}/api/admin/stats?range=${range}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-Api-Key': process.env.INTERNAL_API_KEY || '',
      },
    });

    if (!response.ok) {
      console.error(`[Admin Stats] Backend returned status ${response.status}`);
      return NextResponse.json({ error: 'Backend error' }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('[Admin Stats] Error:', error);
    return NextResponse.json({ error: 'Failed to fetch stats' }, { status: 500 });
  }
}
