import { NextRequest } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8080';

const ALLOWED_ORIGINS = [
  'https://jove.sam9scloud.in',
  'https://joveheal.com',
  'https://www.joveheal.com',
];

function getCorsHeaders(origin: string | null) {
  const headers: Record<string, string> = {
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  };
  
  if (origin && (ALLOWED_ORIGINS.includes(origin) || origin.includes('.kajabi.com') || origin.includes('.mykajabi.com'))) {
    headers['Access-Control-Allow-Origin'] = origin;
  } else if (origin && (origin.includes('replit.dev') || origin.includes('replit.app'))) {
    headers['Access-Control-Allow-Origin'] = origin;
  } else {
    headers['Access-Control-Allow-Origin'] = ALLOWED_ORIGINS[0];
  }
  
  return headers;
}

export async function OPTIONS(request: NextRequest) {
  const origin = request.headers.get('origin');
  return new Response(null, {
    status: 204,
    headers: getCorsHeaders(origin),
  });
}

export async function POST(request: NextRequest) {
  const origin = request.headers.get('origin');
  const corsHeaders = getCorsHeaders(origin);
  
  try {
    const body = await request.json();
    
    const session = await getServerSession(authOptions);
    
    const secureBody = {
      ...body,
      verified_user: session?.user ? {
        email: session.user.email,
        name: session.user.name,
        image: session.user.image,
      } : null,
      user: undefined,
    };
    
    const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-Api-Key': process.env.INTERNAL_API_KEY || '',
      },
      body: JSON.stringify(secureBody),
    });

    if (!response.ok) {
      console.error(`[Chat Stream API] Backend returned status ${response.status}`);
      return new Response(
        JSON.stringify({ error: 'Backend error' }),
        { 
          status: response.status, 
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders,
          } 
        }
      );
    }

    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        ...corsHeaders,
      },
    });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`[Chat Stream API] Error: ${errorMessage}`);
    return new Response(
      JSON.stringify({ error: 'Failed to process request' }),
      { 
        status: 503, 
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders,
        } 
      }
    );
  }
}
