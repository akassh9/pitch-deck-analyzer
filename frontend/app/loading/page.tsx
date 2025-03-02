'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LoadingPage() {
  const [progress, setProgress] = useState(0);
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  useEffect(() => {
    const job_id = localStorage.getItem('job_id');
    if (!job_id) {
      router.push('/');
      return;
    }
    
    const checkStatusInterval = setInterval(async () => {
      try {
        const response = await fetch(`${apiUrl}/api/status?job_id=${job_id}`);
        if (response.ok) {
          const data = await response.json();
          // Extract the nested job data
          const jobData = data.data;
          setProgress(jobData.progress);
          if (jobData.status === 'complete') {
            localStorage.setItem('extractedText', jobData.result);
            localStorage.removeItem('job_id');
            clearInterval(checkStatusInterval);
            router.push('/edit');
          }
          if (jobData.status === 'error') {
            clearInterval(checkStatusInterval);
            alert("An error occurred while processing the document.");
            router.push('/');
          }
        }
      } catch (error) {
        console.error('Error fetching job status:', error);
      }
    }, 1000);
    
    return () => {
      clearInterval(checkStatusInterval);
    };
  }, [router, apiUrl]);
  

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h2 className="text-2xl font-bold mb-2">Processing Your Document</h2>
          <p className="text-muted-foreground">Please wait while we prepare your content</p>
        </div>
        <div className="relative mb-6">
          <div className="w-full h-2 bg-secondary rounded-full">
            <div
              className="h-full bg-primary rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
        <p>{progress}% complete</p>
      </div>
    </div>
  );
}
