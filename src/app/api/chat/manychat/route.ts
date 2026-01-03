import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8080';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    console.log('[ManyChat API] Received request:', JSON.stringify(body));
    
    const response = await fetch(`${BACKEND_URL}/api/chat/manychat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      console.error(`[ManyChat API] Backend returned status ${response.status}`);
      return NextResponse.json({
        version: "v2",
        content: {
          messages: [{ type: "text", text: "Sorry, I'm having trouble right now. Please try again." }],
          actions: [],
          quick_replies: []
        }
      });
    }

    const data = await response.json();
    console.log('[ManyChat API] Response:', JSON.stringify(data));
    return NextResponse.json(data);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`[ManyChat API] Error: ${errorMessage}`);
    return NextResponse.json({
      version: "v2",
      content: {
        messages: [{ type: "text", text: "I'm having trouble connecting. Please try again in a moment." }],
        actions: [],
        quick_replies: []
      }
    });
  }
}
