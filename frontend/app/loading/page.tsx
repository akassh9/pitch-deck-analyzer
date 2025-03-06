'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '../../lib/api-client';
import type { MemoResult } from '../../lib/api-client';

export default function LoadingPage() {
  const [progress, setProgress] = useState(0);
  const router = useRouter();

  useEffect(() => {
    const job_id = localStorage.getItem('job_id');
    const nextRoute = localStorage.getItem('nextRoute');
    console.log('Initial job_id from localStorage:', job_id); // Debug log
    console.log('Next route from localStorage:', nextRoute); // Debug log
    
    if (!job_id) {
      console.log('No job_id found in localStorage, redirecting to /'); // Debug log
      router.push('/');
      return;
    }
    
    const checkStatusInterval = setInterval(async () => {
      try {
        console.log('Checking job status for:', job_id); // Debug log
        const jobData = await apiClient.getJobStatus(job_id);
        console.log('Job data received:', jobData); // Debug log
        
        setProgress(jobData.progress || 0);
        
        if (jobData.status === 'completed') {
          // Store the nextRoute in a local variable to ensure it doesn't change
          const route = nextRoute || '/edit';
          console.log('Job completed. Next route determined as:', route); // Debug log
          console.log('Job result type:', typeof jobData.result); // Debug log
          console.log('Job result:', jobData.result); // Debug log
          
          if (route === '/result') {
            console.log('Processing as memo generation result for /result'); // Debug log
            // Handle memo generation result
            if (typeof jobData.result === 'object' && jobData.result !== null) {
              const memoResult = jobData.result as MemoResult;
              console.log('Storing memo result:', memoResult); // Debug log
              localStorage.setItem('memo', memoResult.memo || '');
              localStorage.setItem('template_used', memoResult.template_used || 'default');
              localStorage.setItem('startup_stage', memoResult.startup_stage || 'default');
              console.log('Stored memo data in localStorage'); // Debug log
            } else if (typeof jobData.result === 'string') {
              console.log('Result is a string, storing with default values'); // Debug log
              localStorage.setItem('memo', jobData.result);
              localStorage.setItem('template_used', 'default');
              localStorage.setItem('startup_stage', 'default');
            } else {
              console.error('Invalid result format:', jobData.result);
              localStorage.setItem('memo', 'Error: Invalid memo format received');
              localStorage.setItem('template_used', 'default');
              localStorage.setItem('startup_stage', 'default');
            }
          } else {
            console.log('Processing as text extraction result for /edit'); // Debug log
            // Handle text extraction result
            console.log('Storing extracted text for edit page'); // Debug log
            if (typeof jobData.result === 'object' && jobData.result !== null) {
              console.log('Result is an object with properties:', Object.keys(jobData.result)); // Debug log
              console.log('Result object details:', JSON.stringify(jobData.result)); // Debug log
              
              const cleanedText = (jobData.result as any).cleaned_text || '';
              const startupStage = (jobData.result as any).startup_stage || 'default';
              
              console.log('Extracted cleaned_text:', cleanedText ? cleanedText.substring(0, 50) + '...' : 'empty'); // Debug log
              console.log('Extracted startup_stage:', startupStage); // Debug log
              
              localStorage.setItem('extractedText', cleanedText);
              localStorage.setItem('startupStage', startupStage);
              console.log('Stored extractedText and startupStage in localStorage'); // Debug log
              console.log('localStorage values after setting:', {
                extractedText: localStorage.getItem('extractedText') ? 'present' : 'missing',
                startupStage: localStorage.getItem('startupStage')
              }); // Debug log
            } else if (typeof jobData.result === 'string') {
              console.log('Result is a string, storing as extractedText'); // Debug log
              localStorage.setItem('extractedText', jobData.result);
              localStorage.setItem('startupStage', 'default');
            } else {
              console.log('Result is neither object nor string, storing empty values'); // Debug log
              localStorage.setItem('extractedText', '');
              localStorage.setItem('startupStage', 'default');
            }
          }
          
          console.log('About to redirect to:', route); // Debug log
          console.log('localStorage state before redirect:', {
            extractedText: localStorage.getItem('extractedText'),
            startupStage: localStorage.getItem('startupStage'),
            memo: localStorage.getItem('memo'),
            template_used: localStorage.getItem('template_used'),
            job_id: localStorage.getItem('job_id'),
            nextRoute: localStorage.getItem('nextRoute')
          }); // Debug log
          
          // Clean up localStorage
          localStorage.removeItem('job_id');
          localStorage.removeItem('nextRoute');
          
          // Stop the interval before redirecting
          clearInterval(checkStatusInterval);
          
          // Redirect with a slight delay to ensure logs are visible
          console.log('Redirecting to:', route); // Debug log
          setTimeout(() => {
            router.push(route);
          }, 100);
        }        
        
        if (jobData.status === 'failed') {
          console.error('Job failed:', jobData.error); // Debug log
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
