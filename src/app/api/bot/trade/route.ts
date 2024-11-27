import { spawn } from 'child_process';
import { NextResponse } from 'next/server';

export async function POST() {
    try {
        // Run the bot with force-trade flag for a single analysis
        const botProcess = spawn('python3', ['run_crypto_bot.py', '--force-trade'], {
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        return new Promise((resolve, reject) => {
            let output = '';
            let tradeExecuted = false;

            botProcess.stdout.on('data', (data: Buffer) => {
                const chunk = data.toString();
                output += chunk;
                console.log('Bot output:', chunk);

                // Check if a trade was executed
                if (chunk.includes('Successfully executed')) {
                    tradeExecuted = true;
                }
            });

            botProcess.stderr.on('data', (data: Buffer) => {
                console.error('Bot error:', data.toString());
            });

            botProcess.on('close', (code: number) => {
                console.log(`Bot process exited with code ${code}`);

                if (code !== 0) {
                    reject(NextResponse.json({
                        error: 'Trade analysis failed',
                        details: output
                    }, { status: 500 }));
                } else {
                    resolve(NextResponse.json({
                        message: tradeExecuted
                            ? 'Trade executed successfully'
                            : 'Analysis complete - No trade opportunities found',
                        details: output
                    }));
                }
            });

            // Kill the process after 30 seconds if it hasn't completed
            setTimeout(() => {
                botProcess.kill();
                reject(NextResponse.json({
                    error: 'Trade analysis timeout',
                    details: output
                }, { status: 504 }));
            }, 30000);
        });
    } catch (error) {
        console.error('Error executing trade:', error);
        return NextResponse.json({
            error: 'Failed to execute trade',
            details: error.message
        }, { status: 500 });
    }
}
