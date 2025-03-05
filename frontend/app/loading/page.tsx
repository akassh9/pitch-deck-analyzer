'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '../../lib/api-client';

export default function LoadingPage() {
  const [progress, setProgress] = useState(0);
  const router = useRouter();

  useEffect(() => {
    const job_id = localStorage.getItem('job_id');
    if (!job_id) {
      router.push('/');
      return;
    }
    
    const checkStatusInterval = setInterval(async () => {
      try {
        const jobData = await apiClient.getJobStatus(job_id);
        
        setProgress(jobData.progress || 0);
        
        if (jobData.status === 'completed') {
          // Read the next route flag; default to '/edit' if not set
          const nextRoute = localStorage.getItem('nextRoute') || '/edit';
          
          // If the next route is '/result', store the memo with key 'memo'
          if (nextRoute === '/result') {
            localStorage.setItem('memo', jobData.result || '');
          } else {
            localStorage.setItem('extractedText', jobData.result || '');
          }
          
          localStorage.removeItem('job_id');
          localStorage.removeItem('nextRoute');
          clearInterval(checkStatusInterval);
          router.push(nextRoute);
        }        
        
        
        if (jobData.status === 'failed') {
          clearInterval(checkStatusInterval);
          alert(`An error occurred while processing the document: ${jobData.error || 'Unknown error'}`);
          router.push('/');
        }
      } catch (error) {
        console.error('Error fetching job status:', error);
      }
    }, 1000);
    
    return () => {
      clearInterval(checkStatusInterval);
    };
  }, [router]);
  

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
