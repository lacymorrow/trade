import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
    // Skip authentication for API routes and public routes
    if (
        request.nextUrl.pathname.startsWith('/api/') ||
        request.nextUrl.pathname === '/login' ||
        request.nextUrl.pathname === '/health'
    ) {
        return NextResponse.next()
    }

    // Get the token from the cookie
    const token = request.cookies.get('auth-token')

    // If there's no token, redirect to login
    if (!token) {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    return NextResponse.next()
}

export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - api (API routes)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         * - public folder
         */
        '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
    ],
}
