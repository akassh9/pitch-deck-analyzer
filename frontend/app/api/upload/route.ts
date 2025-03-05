import { NextResponse } from 'next/server';
import { API_CONFIG } from '../../../lib/config';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get('pdf_file') as File;

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    console.log('Attempting to upload to:', `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.upload}`);

    const newFormData = new FormData();
    newFormData.append('file', file);

    const backendResponse = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.upload}`, {
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