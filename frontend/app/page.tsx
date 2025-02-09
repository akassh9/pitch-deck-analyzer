'use client';

import { useState } from 'react';
import { Upload } from "lucide-react"

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      console.log('File selected:', selectedFile.name);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) return;

    setIsLoading(true);
    const formData = new FormData();
    formData.append('pdf_file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const data = await response.json();
      if (data.success) {
        window.location.href = `/edit?text=${encodeURIComponent(data.text)}`;
      } else {
        throw new Error(data.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="p-6">
        <nav className="flex justify-between items-start">
          {/* Left side */}
          <div className="flex flex-col">
            <div className="text-sm text-muted-foreground">
              <p>India</p>
            </div>
          </div>

          {/* Right side */}
          {/* Removed as requested */}
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="text-center mb-8">
          <h1 className="text-2xl mb-2">Nivesha</h1>
          <div className="max-w-md mx-auto">
            <p className="text-4xl mb-4">Grounded in Insights, Driven by Growth</p>
            <p className="text-muted-foreground text-sm">
              Transforming startup evaluations with streamlined data intelligence.
            </p>
          </div>
        </div>

        {/* Upload Button */}
        <div className="mt-8">
          <form onSubmit={handleSubmit}>
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
              className="w-full bg-blue-600 text-white py-3 rounded-lg disabled:opacity-50 mt-4"
            >
              {isLoading ? 'Analyzing...' : 'Analyze Pitch Deck'}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

