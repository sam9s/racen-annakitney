import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

const DASHBOARD_EMAIL = process.env.DASHBOARD_EMAIL || '';
const DASHBOARD_PASSWORD = process.env.DASHBOARD_PASSWORD || '';

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return NextResponse.json({ error: 'Email and password required' }, { status: 400 });
    }

    const emailMatch = email.toLowerCase().trim() === DASHBOARD_EMAIL.toLowerCase().trim();
    const passwordMatch = password === DASHBOARD_PASSWORD;

    if (emailMatch && passwordMatch) {
      const token = Buffer.from(`${email}:${Date.now()}`).toString('base64');
      
      const cookieStore = await cookies();
      cookieStore.set('admin_token', token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7,
        path: '/',
      });

      return NextResponse.json({ 
        success: true, 
        user: { email: email.toLowerCase().trim(), name: 'Dashboard Admin' } 
      });
    }

    return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
  } catch (error) {
    console.error('[Admin Login] Error:', error);
    return NextResponse.json({ error: 'Login failed' }, { status: 500 });
  }
}

export async function DELETE() {
  try {
    const cookieStore = await cookies();
    cookieStore.delete('admin_token');
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('[Admin Logout] Error:', error);
    return NextResponse.json({ error: 'Logout failed' }, { status: 500 });
  }
}
