import { NextResponse } from 'next/server';

export async function GET() {
  const apiKey = process.env.UPTIMEROBOT_API_KEY;

  if (!apiKey) {
    return NextResponse.json(
      { error: 'UptimeRobot API key not configured. Add UPTIMEROBOT_API_KEY to your secrets.' },
      { status: 500 }
    );
  }

  try {
    const response = await fetch('https://api.uptimerobot.com/v2/getMonitors', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        api_key: apiKey,
        format: 'json',
        logs: '1',
        logs_limit: '10',
        response_times: '1',
        response_times_limit: '24',
        custom_uptime_ratios: '1-7-30-90',
      }),
      cache: 'no-store',
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch from UptimeRobot API' },
        { status: response.status }
      );
    }

    const data = await response.json();

    if (data.stat !== 'ok') {
      return NextResponse.json(
        { error: data.error?.message || 'UptimeRobot API error' },
        { status: 400 }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Monitoring API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch monitoring data' },
      { status: 500 }
    );
  }
}
