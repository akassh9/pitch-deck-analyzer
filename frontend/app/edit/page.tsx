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

  // A simple custom function to strip markdown syntax
  function stripMarkdown(markdownText: string): string {
    return markdownText
      .replace(/(\*\*|__)(.*?)\1/g, '$2')    // bold/italic
      .replace(/(\*|_)(.*?)\1/g, '$2')         // italic
      .replace(/!\[.*?\]\(.*?\)/g, '')          // images
      .replace(/\[(.*?)\]\(.*?\)/g, '$1')        // links
      .replace(/^\s*>+\s?/gm, '')               // blockquotes
      .replace(/^\s*[-+*]\s+/gm, '')            // unordered list markers
      .replace(/^\s*\d+\.\s+/gm, '')             // ordered list markers
      .replace(/`{1,3}([^`]*)`{1,3}/g, '$1');    // inline code
  }

  useEffect(() => {
    const extractedText = localStorage.getItem('extractedText')
    if (extractedText) {
      const plainText = stripMarkdown(extractedText)
      setEditedText(plainText)
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'
      const response = await fetch(`${apiUrl}/api/generate-memo`, {
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
            className="w-full h-[calc(100vh-300px)] p-4 bg-secondary text-secondary-foreground rounded-md mb-6 resize-none overflow-auto font-serif"
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