import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    try {
        const { selected_text } = await request.json();

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
        
        // Ensure HTML tags are preserved
        return new Response(JSON.stringify({
            validation_html: backendData.response_text,
            status: 'success'
        }), {
            headers: {
                'Content-Type': 'application/json',
            },
        });
    } catch (error) {
        console.error('Error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to validate text' },
            { status: 500 }
        );
    }
}