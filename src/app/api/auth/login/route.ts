import { NextResponse } from 'next/server'

const UI_SECRET = process.env.UI_SECRET || 'development-secret'

export async function POST(request: Request) {
    try {
        const { username, password } = await request.json()

        // In a real application, you would validate against a database
        // For now, we'll use a simple check
        if (username === 'admin' && password === 'admin') {
            // Create the response
            const response = NextResponse.json({ success: true })

            // Set the auth cookie
            response.cookies.set('auth-token', UI_SECRET, {
                httpOnly: true,
                secure: process.env.NODE_ENV === 'production',
                sameSite: 'strict',
                maxAge: 60 * 60 * 24 // 24 hours
            })

            return response
        }

        return NextResponse.json(
            { error: 'Invalid credentials' },
            { status: 401 }
        )
    } catch (error) {
        console.error('Login error:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
}
