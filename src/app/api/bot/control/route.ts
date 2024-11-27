import { spawn } from 'child_process';
import { NextResponse } from 'next/server';

let botProcess: any = null;
let startTime: Date | null = null;
let totalTrades = 0;
let profitLoss = 0;

export async function POST(request: Request) {
    try {
        const { action } = await request.json();

        if (action === 'start' && !botProcess) {
            // Start the bot process with appropriate flags
            const args = ['run_crypto_bot.py'];

            // Add test mode flag if needed
            // args.push('--test');

            // Force trade mode
            args.push('--force-trade');

            // Specific symbols (optional)
            // args.push('--symbols', 'BTC', 'ETH', 'SOL');

            botProcess = spawn('python3', args, {
                stdio: ['pipe', 'pipe', 'pipe'],
            });

            startTime = new Date();

            // Handle bot output
            botProcess.stdout.on('data', (data: Buffer) => {
                const output = data.toString();
                console.log('Bot output:', output);

                // Parse trade information from output
                if (output.includes('Successfully executed')) {
                    totalTrades++;
                    // Extract P/L information if available in the output
                    const plMatch = output.match(/P\/L: \$([0-9.-]+)/);
                    if (plMatch) {
                        profitLoss += parseFloat(plMatch[1]);
                    }
                }
            });

            botProcess.stderr.on('data', (data: Buffer) => {
                console.error('Bot error:', data.toString());
            });

            botProcess.on('close', (code: number) => {
                console.log(`Bot process exited with code ${code}`);
                botProcess = null;
                startTime = null;
            });

            return NextResponse.json({ status: 'started' });
        }

        if (action === 'stop' && botProcess) {
            botProcess.kill();
            botProcess = null;
            startTime = null;
            return NextResponse.json({ status: 'stopped' });
        }

        return NextResponse.json({ status: 'no action taken' });
    } catch (error) {
        console.error('Error controlling bot:', error);
        return NextResponse.json({ error: 'Failed to control bot' }, { status: 500 });
    }
}
