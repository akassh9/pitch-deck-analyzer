import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    try {
        const data = await request.json();
        const text = data.text;

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
        const backendResponse = await fetch(`${apiUrl}/api/generate-memo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
        });

        if (!backendResponse.ok) {
            const errorText = await backendResponse.text();
            throw new Error(errorText);
        }

        const backendData = await backendResponse.json();
        return NextResponse.json(backendData);
    } catch (error) {
        console.error('Error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to generate memo' },
            { status: 500 }
        );
    }
}