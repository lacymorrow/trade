import { spawn } from 'child_process';
import { headers } from 'next/headers';
import { NextResponse } from 'next/server';

const CRON_SECRET = process.env.CRON_SECRET;

export async function POST(req: Request) {
    try {
        // Verify cron job secret
        const headersList = headers();
        const authorization = headersList.get('authorization');

        if (!authorization || authorization !== `Bearer ${CRON_SECRET}`) {
            return new NextResponse('Unauthorized', { status: 401 });
        }

        // Run the trading bot
        const result = await new Promise((resolve, reject) => {
            const bot = spawn('python3', ['run_bot.py']);

            let output = '';
            let error = '';

            bot.stdout.on('data', (data) => {
                output += data.toString();
            });

            bot.stderr.on('data', (data) => {
                error += data.toString();
            });

            bot.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Bot exited with code ${code}\nError: ${error}`));
                } else {
                    resolve(output);
                }
            });
        });

        return NextResponse.json({
            success: true,
            message: 'Trading bot executed successfully',
            output: result
        });

    } catch (error) {
        console.error('Error running trading bot:', error);
        return NextResponse.json({
            success: false,
            error: error.message
        }, { status: 500 });
    }
}
