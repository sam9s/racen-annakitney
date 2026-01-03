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
    
    const isStreaming = body.stream === true;
    
    const response = await fetch(`${BACKEND_URL}/api/vapi/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });
    
    if (isStreaming && response.body) {
      const stream = response.body;
      return new NextResponse(stream, {
        status: response.status,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    }
    
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
    
  } catch (error) {
    console.error('[VAPI Custom LLM Proxy] Error:', error);
    return NextResponse.json(
      { error: 'Custom LLM proxy error' },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({ 
    status: 'VAPI Custom LLM endpoint ready',
    info: 'This endpoint replaces VAPI LLM with SOMERA engine'
  });
}
