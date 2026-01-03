import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8080';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    const authHeader = request.headers.get('Authorization');
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    
    const vapiSecret = request.headers.get('x-vapi-secret');
    if (vapiSecret) {
      headers['x-vapi-secret'] = vapiSecret;
    }
    
    const response = await fetch(`${BACKEND_URL}/api/vapi/webhook`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });
    
    const data = await response.json();
    
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('[VAPI Webhook Proxy] Error:', error);
    return NextResponse.json(
      { error: 'Webhook proxy error' },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({ status: 'VAPI webhook endpoint ready' });
}
