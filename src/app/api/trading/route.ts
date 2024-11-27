import { spawn } from 'child_process';
import { headers } from 'next/headers';
import { NextResponse } from 'next/server';

const CRON_SECRET = process.env.CRON_SECRET;
const UI_SECRET = process.env.UI_SECRET || 'development-secret';

export async function POST(req: Request) {
    try {
        // Get authorization header
        const headersList = await headers();
        const authorization = await headersList.get('authorization');

        // Check if it's a cron job or UI request
        if (!authorization) {
            return new NextResponse('Unauthorized', { status: 401 });
        }

        // Handle both cron job and UI authentication
        const isValidCron = authorization === `Bearer ${CRON_SECRET}`;
        const isValidUI = authorization === `Bearer ${UI_SECRET}`;

        if (!isValidCron && !isValidUI) {
            return new NextResponse('Unauthorized', { status: 401 });
        }

        // Run the trading bot with a single analysis flag
        const result = await new Promise((resolve, reject) => {
            const bot = spawn('python3', ['run_bot.py', '--single-run']);

            let output = '';
            let error = '';

            bot.stdout.on('data', (data) => {
                output += data.toString();
            });

            bot.stderr.on('data', (data) => {
                error += data.toString();
            });

            // Set a timeout of 2 minutes
            const timeout = setTimeout(() => {
                bot.kill();
                reject(new Error('Bot execution timed out'));
            }, 120000);

            bot.on('close', (code) => {
                clearTimeout(timeout);
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

    } catch (error: unknown) {
        console.error('Error running trading bot:', error);
        return NextResponse.json({
            success: false,
            error: error instanceof Error ? error.message : 'An unknown error occurred'
        }, { status: 500 });
    }
}
