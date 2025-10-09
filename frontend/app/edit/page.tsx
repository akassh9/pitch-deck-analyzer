'use client'

import { useState, useEffect, type ChangeEvent, type FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { Send } from 'lucide-react'
import { apiClient } from '../../lib/api-client'
import { TemplateSelector } from '../../components/TemplateSelector'

export default function EditText() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [markdownText, setMarkdownText] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState('default')
  const [autoSelectedTemplate, setAutoSelectedTemplate] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const extractedText = localStorage.getItem('extractedText')
    const startupStage = localStorage.getItem('startupStage')

    if (extractedText) {
      setMarkdownText(extractedText)

      if (startupStage) {
        const normalizedStage = startupStage.toLowerCase().trim()
        const validStages = ['seed', 'seriesa', 'growth', 'default']

        if (validStages.includes(normalizedStage)) {
          setSelectedTemplate(normalizedStage)
          setAutoSelectedTemplate(true)
        } else {
          setSelectedTemplate('default')
        }
      }
    } else {
      router.push('/')
    }
  }, [router])

  const handleTextChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setMarkdownText(event.target.value)
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      localStorage.setItem('nextRoute', '/result')
      const result = await apiClient.generateMemo(markdownText, selectedTemplate)
      localStorage.setItem('job_id', result.job_id)
      router.push('/loading')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate memo')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="w-3/4 mx-auto space-y-6 pb-8">
        <h1 className="text-4xl font-serif">Edit Text</h1>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="memo-text" className="sr-only">
              Edit the extracted text
            </label>
            <textarea
              id="memo-text"
              value={markdownText}
              onChange={handleTextChange}
              placeholder="Edit the text here..."
              className="w-full h-[500px] resize-none rounded-md border border-border bg-secondary p-4 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
          <div className="space-y-2">
            <TemplateSelector
              selectedTemplate={selectedTemplate}
              onTemplateChange={(template) => {
                setSelectedTemplate(template)
                setAutoSelectedTemplate(false)
              }}
            />
            {autoSelectedTemplate && (
              <p className="text-sm text-muted-foreground italic">
                Template auto-selected based on startup stage analysis
              </p>
            )}
          </div>
          {error && <div className="text-sm text-red-500">{error}</div>}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center rounded-lg bg-primary px-6 py-2 text-primary-foreground transition-colors hover:bg-accent disabled:opacity-50"
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
