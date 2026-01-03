import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8080';
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchWithRetry(url: string, options: RequestInit, retries: number = MAX_RETRIES): Promise<Response> {
  let lastError: Error | null = null;
  
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      console.log(`[Chat API] Attempt ${attempt}/${retries} to reach backend at: ${url}`);
      const response = await fetch(url, options);
      return response;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('Unknown error');
      console.error(`[Chat API] Attempt ${attempt} failed: ${lastError.message}`);
      
      if (attempt < retries) {
        console.log(`[Chat API] Waiting ${RETRY_DELAY_MS}ms before retry...`);
        await sleep(RETRY_DELAY_MS);
      }
    }
  }
  
  throw lastError;
}

export async function POST(request: NextRequest) {
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
    
    const response = await fetchWithRetry(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-Api-Key': process.env.INTERNAL_API_KEY || '',
      },
      body: JSON.stringify(secureBody),
    });

    if (!response.ok) {
      console.error(`[Chat API] Backend returned status ${response.status}`);
      const errorText = await response.text();
      console.error(`[Chat API] Backend error: ${errorText}`);
      return NextResponse.json(
        { error: 'Backend error', response: 'I apologize, but I encountered an issue. Please try again.' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`[Chat API] All retry attempts failed: ${errorMessage}`);
    return NextResponse.json(
      { error: 'Failed to process request', response: 'I apologize, but I encountered an issue. Please try again in a moment.' },
      { status: 503 }
    );
  }
}
