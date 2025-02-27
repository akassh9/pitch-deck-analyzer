'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const steps = [
  'Parsing PDF content...',
  'Extracting text from pages...',
  'Cleaning up blank spaces...',
  'Removing redundant content...',
  'Improving text readability...',
  'Preparing content for analysis...'
];

export default function LoadingPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  useEffect(() => {
    const job_id = localStorage.getItem('job_id');
    if (!job_id) {
      router.push('/');
      return;
    }
    const stepDuration = 2500;
    const progressIncrement = 100 / steps.length;
    
    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
      setProgress((prev) => Math.min(prev + progressIncrement, 100));
    }, stepDuration);
    
    const checkStatusInterval = setInterval(async () => {
      try {
        const response = await fetch(`${apiUrl}/api/status?job_id=${job_id}`);
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'complete') {
            localStorage.setItem('extractedText', data.result);
            localStorage.removeItem('job_id');
            clearInterval(checkStatusInterval);
            clearInterval(stepInterval);
            router.push('/edit');
          }
        }
      } catch (error) {
        console.error('Error fetching job status:', error);
      }
    }, 1000);
    
    return () => {
      clearInterval(checkStatusInterval);
      clearInterval(stepInterval);
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
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div
              key={step}
              className={`flex items-center space-x-3 transition-opacity duration-300 ${index > currentStep ? 'opacity-40' : 'opacity-100'}`}
            >
              {index <= currentStep ? (
                <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                  <svg className="w-4 h-4 text-primary-foreground" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                    <path d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              ) : (
                <div className="w-6 h-6 rounded-full border-2 border-secondary" />
              )}
              <span className={`${index === currentStep ? 'text-primary font-medium' : ''}`}>
                {step}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
