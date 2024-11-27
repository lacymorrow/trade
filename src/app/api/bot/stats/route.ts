import { NextResponse } from 'next/server';

// These would typically come from a database
let startTime: Date | null = null;
let totalTrades = 0;
let profitLoss = 0;

export async function GET() {
    try {
        // Calculate uptime
        const uptime = startTime
            ? formatUptime(new Date().getTime() - startTime.getTime())
            : '0:00:00';

        return NextResponse.json({
            uptime,
            totalTrades,
            profitLoss,
        });
    } catch (error) {
        console.error('Error fetching bot stats:', error);
        return NextResponse.json({ error: 'Failed to fetch bot stats' }, { status: 500 });
    }
}

function formatUptime(ms: number): string {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    return `${hours}:${String(minutes % 60).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
}
