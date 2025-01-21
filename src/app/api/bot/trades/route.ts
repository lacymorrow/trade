import { NextResponse } from 'next/server';

export async function GET() {
	try {
		console.log('Fetching trades from:', process.env.NEXT_PUBLIC_BACKEND_URL);

		const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/trades`, {
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${process.env.UI_SECRET || 'development-secret'}`
			}
		});

		if (!response.ok) {
			console.error('Error response from backend:', {
				status: response.status,
				statusText: response.statusText
			});
			const errorText = await response.text();
			console.error('Error details:', errorText);

			throw new Error(`Backend error: ${response.status} ${response.statusText}`);
		}

		const data = await response.json();
		console.log('Trades data received:', data);

		if (!data.success) {
			throw new Error(data.error?.message || 'Failed to fetch trades from backend');
		}

		return NextResponse.json(data);
	} catch (error) {
		console.error('Error fetching trades:', error);
		return NextResponse.json({
			success: false,
			error: {
				code: 'FETCH_ERROR',
				message: error instanceof Error ? error.message : 'Failed to fetch trades',
				details: error instanceof Error ? error.stack : undefined
			}
		}, { status: 500 });
	}
}
