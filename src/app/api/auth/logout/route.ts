import { NextResponse } from 'next/server'

export async function POST() {
    const response = NextResponse.json({ success: true })

    // Remove the auth cookie
    response.cookies.set('auth-token', '', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 0 // Expire immediately
    })

    return response
}
