import { spawn } from 'child_process';
import { NextResponse } from 'next/server';

export async function GET() {
    try {
        // Run the Python script to get recent trades
        const result = await new Promise((resolve, reject) => {
            const process = spawn('python3', ['run_bot.py', '--get-trades']);

            let output = '';
            let error = '';

            process.stdout.on('data', (data) => {
                output += data.toString();
            });

            process.stderr.on('data', (data) => {
                error += data.toString();
            });

            process.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Process exited with code ${code}\nError: ${error}`));
                } else {
                    try {
                        resolve(JSON.parse(output));
                    } catch {
                        reject(new Error('Failed to parse trades data'));
                    }
                }
            });
        });

        return NextResponse.json(result);
    } catch (error) {
        console.error('Error fetching trades:', error);
        return NextResponse.json({
            error: error instanceof Error ? error.message : 'Failed to fetch trades'
        }, { status: 500 });
    }
}
