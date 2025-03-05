'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Send } from 'lucide-react'
import { apiClient } from '../../lib/api-client'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()

export default function EditText() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const editor = useEditor({
    extensions: [
      StarterKit,
    ],
    editorProps: {
      attributes: {
        class: 'prose prose-slate dark:prose-invert max-w-none prose-headings:font-serif prose-p:font-sans prose-li:font-sans outline-none',
      },
    },
  })

  useEffect(() => {
    const extractedText = localStorage.getItem('extractedText')
    if (extractedText) {
      // Convert markdown to HTML and set content
      const html = md.render(extractedText)
      editor?.commands.setContent(html)
    } else {
      router.push('/')
    }
  }, [editor, router])

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)
  
    try {
      // Get HTML content and convert back to markdown
      // For now, we'll just send the original markdown stored in localStorage
      const originalMarkdown = localStorage.getItem('extractedText') || ''
      
      localStorage.setItem('nextRoute', '/result')
      const result = await apiClient.generateMemo(originalMarkdown)
      localStorage.setItem('job_id', result.job_id)
      router.push('/loading')
    } catch (error) {
      console.error('Memo generation error:', error)
      setError(error instanceof Error ? error.message : 'Failed to generate memo')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-screen bg-background text-foreground flex flex-col p-8">
      <div className="w-3/4 mx-auto flex flex-col mt-18">
        <h1 className="text-4xl font-serif mb-6">Edit Text</h1>
        <form onSubmit={handleSubmit} className="flex flex-col flex-1">
          <div className="w-full h-[calc(100vh-300px)] p-4 bg-secondary rounded-md mb-6 overflow-auto">
            <EditorContent editor={editor} />
          </div>
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