import { NextResponse } from 'next/server';
import { API_CONFIG } from '../../../lib/config';

export async function POST(request: Request) {
    try {
        const { text } = await request.json();
        const backendResponse = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.validateSelection}`, {
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
            { error: error instanceof Error ? error.message : 'Failed to validate text' },
            { status: 500 }
        );
    }
}
