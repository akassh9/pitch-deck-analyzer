'use client';

import { useState } from 'react';
import { Upload } from 'lucide-react';
import { useRouter } from 'next/navigation'; // Changed from 'next/router'

export default function Page() {
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const router = useRouter();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      console.log('Uploaded file:', selectedFile.name);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) return;

    setIsLoading(true);
    localStorage.removeItem('extractedText');
    
    router.push('/loading');
    
    const formData = new FormData();
    formData.append('pdf_file', file);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
      console.log('Attempting to upload to:', apiUrl); // Debug log
      
      const response = await fetch(`${apiUrl}/api/upload`, {
        method: 'POST',
        body: formData,
        credentials: 'include', // Add this line
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const data = await response.json();
      if (data.success) {
        localStorage.setItem('extractedText', data.text);
      } else {
        throw new Error(data.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert(error instanceof Error ? error.message : 'Upload failed');
      router.push('/');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header Section */}
      <header className="absolute bottom-20 right-20">
        <h1 className="text-6xl font-serif font-bold">Kecha</h1>
      </header>

      {/* Main Content Section */}
      <main className="flex-grow flex flex-col items-start justify-center ml-32">
        <h2 className="text-5xl font-serif mb-4">
          Harness the <span className="italic">raw.</span>
        </h2>
        <p className="text-muted-foreground text-sm max-w-md mb-8">
          Transforming startup evaluations with streamlined data intelligence.
        </p>

        {/* Upload Form */}
        <form onSubmit={handleSubmit} className="flex flex-col items-start gap-4">
          <label htmlFor="pdf-upload" className="cursor-pointer">
            <div className="flex items-center gap-2 bg-transparent border border-border rounded-md px-4 py-2 hover:bg-secondary transition-colors">
              <Upload className="w-4 h-4" />
              <span className="text-sm">{file ? file.name : 'Upload PDF'}</span>
            </div>
            <input
              type="file"
              id="pdf-upload"
              accept=".pdf"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>
          <button
            type="submit"
            disabled={isLoading || !file}
            className="bg-primary text-primary-foreground rounded-lg px-6 py-2 hover:bg-secondary disabled:opacity-50"
          >
            {isLoading ? 'Analyzing...' : 'Analyze Pitch Deck'}
          </button>
        </form>
      </main>
    </div>
  );
}
