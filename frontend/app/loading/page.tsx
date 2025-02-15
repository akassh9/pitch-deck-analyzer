'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { CircularProgress } from '@mui/material'

const steps = [
  'Parsing PDF content...',
  'Extracting text from pages...',
  'Cleaning up blank spaces...',
  'Removing redundant content...',
  'Improving text readability...',
  'Preparing content for analysis...'
]

export default function LoadingPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)
  const router = useRouter()

  useEffect(() => {
    const stepDuration = 1500 // 1.5 seconds per step
    const progressIncrement = 100 / steps.length

    // Check for extracted text periodically
    const checkExtractedText = setInterval(() => {
      const extractedText = localStorage.getItem('extractedText')
      if (extractedText) {
        clearInterval(checkExtractedText)
        router.push('/edit')
      }
    }, 1000) // Check every second

    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev === steps.length - 1) {
          return prev // Stay on last step until text is ready
        }
        return prev + 1
      })

      setProgress((prev) => {
        const next = prev + progressIncrement
        return next > 100 ? 100 : next
      })
    }, stepDuration)

    // Cleanup intervals on unmount
    return () => {
      clearInterval(stepInterval)
      clearInterval(checkExtractedText)
    }
  }, [router])

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
              className={`flex items-center space-x-3 transition-opacity duration-300 ${
                index > currentStep ? 'opacity-40' : 'opacity-100'
              }`}
            >
              {index <= currentStep ? (
                <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                  <svg
                    className="w-4 h-4 text-primary-foreground"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              ) : (
                <div className="w-6 h-6 rounded-full border-2 border-secondary" />
              )}
              <span
                className={`${
                  index === currentStep ? 'text-primary font-medium' : ''
                }`}
              >
                {step}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}