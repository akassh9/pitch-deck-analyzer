'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Send } from 'lucide-react'

export default function EditText() {
  const [editedText, setEditedText] = useState(
    'Your extracted text will appear here. You can edit it before analysis.',
  )
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const extractedText = localStorage.getItem('extractedText')
    if (extractedText) {
      setEditedText(extractedText)
      // Removed localStorage.removeItem('extractedText') to preserve the text
    } else {
      router.push('/')
    }
  }, [router])

  useEffect(() => {
    // Lock scroll on mount
    document.body.style.overflow = 'hidden'

    // Cleanup function to restore scroll when component unmounts
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await fetch('/api/generate-memo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: editedText }),
      })

      if (!response.ok) {
        throw new Error('Failed to generate memo')
      }

      const data = await response.json()
      if (data.success) {
        // Store the memo in localStorage instead of URL
        localStorage.setItem('memo', data.memo)
        router.push('/result')
      } else {
        throw new Error(data.error || 'Failed to generate memo')
      }
    } catch (error) {
      console.error('Error:', error)
      alert('An error occurred while generating the memo')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-screen bg-background text-foreground flex flex-col p-8">
      <div className="w-3/4 mx-auto flex flex-col mt-18">
        <h1 className="text-4xl font-serif mb-6">Edit Extracted Text</h1>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1">
          <textarea
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
            className="w-full h-[calc(100vh-300px)] p-4 bg-secondary text-secondary-foreground rounded-md mb-6 resize-none overflow-auto"
          />

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isLoading}
              className="bg-primary text-primary-foreground rounded-lg px-6 py-2 hover:bg-accent transition-colors flex items-center disabled:opacity-50"
            >
              <Send className="mr-2" size={20} />
              {isLoading ? 'Generating...' : 'Send for Analysis'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
