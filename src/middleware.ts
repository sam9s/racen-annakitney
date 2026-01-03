import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  
  if (pathname.startsWith('/voice')) {
    const demoUser = process.env.VOICE_DEMO_USER;
    const demoPass = process.env.VOICE_DEMO_PASS;
    
    if (!demoUser || !demoPass) {
      return NextResponse.next();
    }
    
    const authHeader = request.headers.get('authorization');
    
    if (!authHeader || !authHeader.startsWith('Basic ')) {
      return new NextResponse('Authentication required', {
        status: 401,
        headers: {
          'WWW-Authenticate': 'Basic realm="SOMERA Voice Demo"',
        },
      });
    }
    
    const base64Credentials = authHeader.split(' ')[1];
    const credentials = atob(base64Credentials);
    const [username, password] = credentials.split(':');
    
    if (username !== demoUser || password !== demoPass) {
      return new NextResponse('Invalid credentials', {
        status: 401,
        headers: {
          'WWW-Authenticate': 'Basic realm="SOMERA Voice Demo"',
        },
      });
    }
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: '/voice/:path*',
};
