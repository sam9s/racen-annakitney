import { NextResponse } from 'next/server';

export async function GET() {
  const flaskUrl = process.env.FLASK_BACKEND_URL || 'http://localhost:8080';
  
  try {
    const flaskHealth = await fetch(`${flaskUrl}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
    });
    
    if (flaskHealth.ok) {
      const flaskData = await flaskHealth.json();
      return NextResponse.json({
        status: 'healthy',
        service: 'JoveHeal Application',
        components: {
          nextjs: 'healthy',
          flask: flaskData.status || 'healthy'
        }
      });
    } else {
      return NextResponse.json({
        status: 'degraded',
        service: 'JoveHeal Application',
        components: {
          nextjs: 'healthy',
          flask: 'unhealthy'
        }
      }, { status: 200 });
    }
  } catch (error) {
    return NextResponse.json({
      status: 'degraded',
      service: 'JoveHeal Application',
      components: {
        nextjs: 'healthy',
        flask: 'unreachable'
      },
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 200 });
  }
}
