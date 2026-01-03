import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8080';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const range = searchParams.get('range') || '30d';
    
    const response = await fetch(`${BACKEND_URL}/api/admin/somera/export?range=${range}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to export SOMERA data');
    }
    
    const csvContent = await response.text();
    
    return new NextResponse(csvContent, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename=somera_transcripts_${new Date().toISOString().split('T')[0]}.csv`,
      },
    });
  } catch (error) {
    console.error('Error exporting SOMERA data:', error);
    return NextResponse.json(
      { error: 'Failed to export SOMERA data' },
      { status: 500 }
    );
  }
}
