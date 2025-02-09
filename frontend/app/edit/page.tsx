'use client';
import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

export default function Edit() {
  const [editedText, setEditedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const searchParams = useSearchParams();
  
  useEffect(() => {
    const text = searchParams.get('text');
    if (text) {
      setEditedText(decodeURIComponent(text));
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch('/api/generate-memo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: editedText }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate memo');
      }

      const data = await response.json();
      if (data.success) {
        window.location.href = `/result?memo=${encodeURIComponent(data.memo)}`;
      } else {
        throw new Error(data.error || 'Failed to generate memo');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred while generating the memo');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Review Extracted Text</h1>
        <form onSubmit={handleSubmit}>
          <textarea
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
            className="w-full h-96 p-4 bg-secondary text-foreground rounded-lg border border-border"
            placeholder="Loading extracted text..."
          />
          <div className="mt-4 flex justify-end">
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
            >
              {isLoading ? 'Generating...' : 'Generate Memo'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}