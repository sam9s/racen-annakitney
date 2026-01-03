import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8080';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const range = searchParams.get('range') || '30d';
    
    const response = await fetch(`${BACKEND_URL}/api/admin/somera/calls?range=${range}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch SOMERA calls');
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching SOMERA calls:', error);
    return NextResponse.json(
      { error: 'Failed to fetch SOMERA calls' },
      { status: 500 }
    );
  }
}
