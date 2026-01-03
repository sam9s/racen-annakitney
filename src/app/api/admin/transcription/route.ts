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

export async function POST(request: NextRequest) {
  try {
    const authorized = await isAuthorized();
    if (!authorized) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const formData = await request.formData();
    const file = formData.get('file') as File;
    const outputName = formData.get('outputName') as string || 'transcript';

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    const maxSize = 200 * 1024 * 1024;
    if (file.size > maxSize) {
      return NextResponse.json({ error: 'File too large. Maximum size is 200MB.' }, { status: 400 });
    }

    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    const flaskFormData = new FormData();
    flaskFormData.append('file', new Blob([buffer]), file.name);
    flaskFormData.append('outputName', outputName);

    const response = await fetch(`${BACKEND_URL}/api/transcribe`, {
      method: 'POST',
      headers: {
        'X-Internal-Api-Key': process.env.INTERNAL_API_KEY || '',
      },
      body: flaskFormData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Transcription] Backend returned status ${response.status}: ${errorText}`);
      try {
        const errorJson = JSON.parse(errorText);
        return NextResponse.json({ error: errorJson.error || 'Transcription failed' }, { status: response.status });
      } catch {
        return NextResponse.json({ error: 'Transcription failed' }, { status: response.status });
      }
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('[Transcription] Error:', error);
    return NextResponse.json({ error: 'Transcription failed' }, { status: 500 });
  }
}
