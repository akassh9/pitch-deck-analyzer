'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Send } from 'lucide-react'
import { apiClient } from '../../lib/api-client'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import MarkdownIt from 'markdown-it'
import { TemplateSelector } from '../../components/TemplateSelector'
import TurndownService from 'turndown'

const md = new MarkdownIt()
const turndownService = new TurndownService()

export default function EditText() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState('default')
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

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)
  
    try {
      // Get HTML content and convert to markdown using TurnDown
      const html = editor?.getHTML() || ''
      console.log('Editor HTML content:', html)
      
      const markdown = turndownService.turndown(html)
      console.log('Converted Markdown:', markdown)
      
      localStorage.setItem('nextRoute', '/result')
      const result = await apiClient.generateMemo(markdown, selectedTemplate)
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
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="w-3/4 mx-auto space-y-6 pb-8">
        <h1 className="text-4xl font-serif">Edit Text</h1>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="h-[500px] p-4 bg-secondary rounded-md overflow-auto">
            <EditorContent editor={editor} />
          </div>
          <TemplateSelector
            selectedTemplate={selectedTemplate}
            onTemplateChange={setSelectedTemplate}
          />
          {error && (
            <div className="text-red-500 text-sm">
              {error}
            </div>
          )}
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