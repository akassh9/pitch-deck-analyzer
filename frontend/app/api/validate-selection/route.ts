import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    try {
        const data = await request.json();
        const selected_text = data.selected_text;

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
        const backendResponse = await fetch(`${apiUrl}/validate_selection`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ selected_text }),
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
            { error: error instanceof Error ? error.message : 'Failed to validate text' },
            { status: 500 }
        );
    }
}