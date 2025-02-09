import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get('pdf_file') as File;

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
    console.log('Attempting to upload to:', `${apiUrl}/api/upload`);

    const newFormData = new FormData();
    newFormData.append('pdf_file', file);

    const backendResponse = await fetch(`${apiUrl}/api/upload`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
      body: newFormData,
    });

    console.log('Backend response status:', backendResponse.status);

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.error('Backend error:', errorText);
      throw new Error(errorText);
    }

    const data = await backendResponse.json();
    console.log('Backend response data:', data);

    return NextResponse.json(data);
  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Upload failed' },
      { status: 500 }
    );
  }
}