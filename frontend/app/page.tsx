'use client';

import { useState } from 'react';
import { Upload } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { apiClient } from '../lib/api-client';

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
    
    try {
      console.log('Starting PDF upload process...'); // Debug log
      const result = await apiClient.uploadPdf(file);
      console.log('Upload successful, job_id received:', result.job_id); // Debug log
      
      // Store job_id in localStorage
      localStorage.setItem('job_id', result.job_id);
      console.log('Stored job_id in localStorage:', result.job_id); // Debug log
      
      // Set nextRoute to edit for initial text extraction
      localStorage.setItem('nextRoute', '/edit');
      console.log('Set nextRoute in localStorage to: /edit'); // Debug log
      
      // Verify localStorage values before navigation
      console.log('localStorage state before navigation:', {
        job_id: localStorage.getItem('job_id'),
        nextRoute: localStorage.getItem('nextRoute')
      }); // Debug log
      
      // Navigate to loading page
      console.log('Navigating to loading page...'); // Debug log
      router.push('/loading');
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
      <header className="absolute bottom-20 right-20">
        <h1 className="text-6xl font-serif font-bold">Kecha</h1>
      </header>
      <main className="flex-grow flex flex-col items-start justify-center ml-32">
        <h2 className="text-5xl font-serif mb-4">
          Harness the <span className="italic">raw.</span>
        </h2>
        <p className="text-muted-foreground text-sm max-w-md mb-8">
          Transforming startup evaluations with streamlined data intelligence.
        </p>
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
