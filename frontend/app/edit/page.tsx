'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Send } from 'lucide-react'
import { apiClient } from '../../lib/api-client'
import { TemplateSelector } from '../../components/TemplateSelector'
import { createEditor, Descendant, Node as SlateNode, BaseEditor, Transforms, Editor } from 'slate'
import { Slate, Editable, withReact, ReactEditor } from 'slate-react'
import { withHistory, HistoryEditor } from 'slate-history'
import MarkdownIt from 'markdown-it'

// Initialize markdown parser
const md = new MarkdownIt();

// Define custom types for Slate
type CustomText = {
  text: string;
  bold?: boolean;
  italic?: boolean;
  code?: boolean;
}

type CustomElement = {
  type: 'paragraph' | 'heading-one' | 'heading-two' | 'heading-three' | 'bulleted-list' | 'numbered-list' | 'list-item' | 'block-quote';
  children: (CustomText | CustomElement)[];
}

// Extend the Slate types
declare module 'slate' {
  interface CustomTypes {
    Editor: BaseEditor & ReactEditor & HistoryEditor;
    Element: CustomElement;
    Text: CustomText;
  }
}

// Custom element types
const CustomElement = ({ attributes, children, element }) => {
  switch (element.type) {
    case 'paragraph':
      return <p {...attributes}>{children}</p>
    case 'heading-one':
      return <h1 className="text-2xl font-bold mt-4 mb-2" {...attributes}>{children}</h1>
    case 'heading-two':
      return <h2 className="text-xl font-bold mt-3 mb-2" {...attributes}>{children}</h2>
    case 'heading-three':
      return <h3 className="text-lg font-bold mt-3 mb-1" {...attributes}>{children}</h3>
    case 'bulleted-list':
      return <ul className="list-disc ml-5 my-2" {...attributes}>{children}</ul>
    case 'numbered-list':
      return <ol className="list-decimal ml-5 my-2" {...attributes}>{children}</ol>
    case 'list-item':
      return <li className="my-1" {...attributes}>{children}</li>
    case 'block-quote':
      return <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2" {...attributes}>{children}</blockquote>
    default:
      return <p {...attributes}>{children}</p>
  }
}

// Custom leaf types
const CustomLeaf = ({ attributes, children, leaf }) => {
  let el = <>{children}</>
  
  if (leaf.bold) {
    el = <strong>{el}</strong>
  }
  
  if (leaf.italic) {
    el = <em>{el}</em>
  }
  
  if (leaf.code) {
    el = <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">{el}</code>
  }
  
  return <span {...attributes}>{el}</span>
}

// Convert markdown to Slate nodes
const markdownToSlate = (markdown) => {
  try {
    // If markdown is empty, return a single empty paragraph
    if (!markdown || markdown.trim() === '') {
      return [{ type: 'paragraph', children: [{ text: '' }] }];
    }

    // Convert markdown to HTML
    const html = md.render(markdown);
    
    // Create a temporary div to hold the HTML
    const div = document.createElement('div');
    div.innerHTML = html;
    
    // Function to process a DOM node to Slate node
    const processNode = (node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        return { text: node.textContent };
      }
      
      if (node.nodeType === Node.ELEMENT_NODE) {
        const el = node;
        let nodeType = 'paragraph';
        let nodeChildren = [];
        
        // Process children first
        if (el.childNodes.length > 0) {
          for (const child of Array.from(el.childNodes)) {
            const childNode = processNode(child);
            if (childNode) {
              if (Array.isArray(childNode)) {
                nodeChildren = [...nodeChildren, ...childNode];
              } else {
                nodeChildren.push(childNode);
              }
            }
          }
        } else {
          nodeChildren = [{ text: '' }];
        }
        
        // Determine node type based on tag
        switch (el.tagName.toLowerCase()) {
          case 'p':
            nodeType = 'paragraph';
            break;
          case 'h1':
            nodeType = 'heading-one';
            break;
          case 'h2':
            nodeType = 'heading-two';
            break;
          case 'h3':
          case 'h4':
          case 'h5':
          case 'h6':
            nodeType = 'heading-three';
            break;
          case 'ul':
            nodeType = 'bulleted-list';
            break;
          case 'ol':
            nodeType = 'numbered-list';
            break;
          case 'li':
            nodeType = 'list-item';
            break;
          case 'blockquote':
            nodeType = 'block-quote';
            break;
          case 'strong':
          case 'b':
            return nodeChildren.map(child => ({ ...child, bold: true }));
          case 'em':
          case 'i':
            return nodeChildren.map(child => ({ ...child, italic: true }));
          case 'code':
            return nodeChildren.map(child => ({ ...child, code: true }));
          case 'a':
            // Just return the text content for links
            return nodeChildren;
          case 'br':
            return { text: '\n' };
          default:
            // For unknown elements, just return their children
            return nodeChildren;
        }
        
        // Return the node with its type and children
        return { type: nodeType, children: nodeChildren };
      }
      
      return null;
    };
    
    // Process all top-level nodes
    const nodes = [];
    for (const child of Array.from(div.childNodes)) {
      const node = processNode(child);
      if (node) {
        if (Array.isArray(node)) {
          nodes.push({ type: 'paragraph', children: node });
        } else {
          nodes.push(node);
        }
      }
    }
    
    return nodes.length > 0 ? nodes : [{ type: 'paragraph', children: [{ text: '' }] }];
  } catch (error) {
    console.error('Error converting markdown to Slate:', error);
    return [{ type: 'paragraph', children: [{ text: markdown || '' }] }];
  }
};

// Convert Slate nodes to markdown
const slateToMarkdown = (nodes) => {
  try {
    let markdown = '';
    
    const processNode = (node) => {
      if (!node) return '';
      
      // Text node
      if (SlateNode.string(node) === node.text) {
        let text = node.text || '';
        
        // Apply formatting
        if (node.bold) text = `**${text}**`;
        if (node.italic) text = `*${text}*`;
        if (node.code) text = `\`${text}\``;
        
        return text;
      }
      
      // Element node
      switch (node.type) {
        case 'paragraph':
          return `${node.children.map(processNode).join('')}\n\n`;
        case 'heading-one':
          return `# ${node.children.map(processNode).join('')}\n\n`;
        case 'heading-two':
          return `## ${node.children.map(processNode).join('')}\n\n`;
        case 'heading-three':
          return `### ${node.children.map(processNode).join('')}\n\n`;
        case 'bulleted-list':
          return `${node.children.map(processNode).join('')}\n`;
        case 'numbered-list':
          return `${node.children.map((child, i) => {
            const childText = processNode(child);
            return childText.replace(/^- /, `${i + 1}. `);
          }).join('')}\n`;
        case 'list-item':
          return `- ${node.children.map(processNode).join('')}\n`;
        case 'block-quote':
          return `> ${node.children.map(processNode).join('')}\n\n`;
        default:
          return node.children ? node.children.map(processNode).join('') : '';
      }
    };
    
    // Process all nodes
    for (const node of nodes) {
      markdown += processNode(node);
    }
    
    return markdown.trim();
  } catch (error) {
    console.error('Error converting Slate to markdown:', error);
    return '';
  }
};

export default function EditText() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [markdownText, setMarkdownText] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState('default')
  const [autoSelectedTemplate, setAutoSelectedTemplate] = useState(false)
  const router = useRouter()
  
  // Create a Slate editor
  const editor = useMemo(() => withHistory(withReact(createEditor())), [])
  
  // Initial value for the editor
  const [initialValue] = useState<CustomElement[]>([
    {
      type: 'paragraph',
      children: [{ text: 'Loading content...' }],
    },
  ])

  // Function to update editor content
  const updateEditorContent = useCallback((content: CustomElement[]) => {
    // Clear the editor
    Transforms.delete(editor, {
      at: {
        anchor: Editor.start(editor, []),
        focus: Editor.end(editor, []),
      },
    })
    
    // Insert the new content
    Transforms.insertNodes(editor, content)
  }, [editor])

  // Load data from localStorage
  useEffect(() => {
    console.log('Edit page mounted, checking localStorage...')
    
    const extractedText = localStorage.getItem('extractedText')
    const startupStage = localStorage.getItem('startupStage')
    
    console.log('localStorage values:', {
      extractedText: extractedText ? `${extractedText.substring(0, 50)}...` : null,
      startupStage: startupStage || 'not found'
    })
    
    if (extractedText) {
      console.log('Setting text from localStorage')
      setMarkdownText(extractedText)
      
      // Set the template based on the LLM-determined stage
      if (startupStage) {
        const normalizedStage = startupStage.toLowerCase().trim()
        console.log(`Raw startup stage: '${startupStage}'`)
        console.log(`Normalized startup stage: '${normalizedStage}'`)
        
        // Check if it's a valid stage
        const validStages = ['seed', 'seriesa', 'growth', 'default']
        if (validStages.includes(normalizedStage)) {
          console.log(`Setting template to valid stage: ${normalizedStage}`)
          setSelectedTemplate(normalizedStage)
          setAutoSelectedTemplate(true)
        } else {
          console.log(`Invalid stage '${normalizedStage}', using default`)
          setSelectedTemplate('default')
        }
      } else {
        console.log('No startup stage found, using default template')
      }
    } else {
      console.log('No extracted text found, redirecting to home')
      router.push('/')
    }
  }, [router]);
  
  // Update editor content when available
  useEffect(() => {
    const extractedText = localStorage.getItem('extractedText');
    if (extractedText && editor) {
      try {
        // Convert markdown to Slate nodes
        const nodes = markdownToSlate(extractedText);
        
        // Update the editor content directly
        setTimeout(() => {
          updateEditorContent(nodes as CustomElement[]);
          console.log('Editor content updated with markdown');
        }, 100); // Small delay to ensure editor is initialized
      } catch (error) {
        console.error('Error updating editor content:', error);
      }
    }
  }, [editor, updateEditorContent]);

  const handleEditorChange = (value) => {
    try {
      // Convert Slate value to markdown
      const markdown = slateToMarkdown(value)
      
      // Update the markdown text state
      setMarkdownText(markdown)
      console.log('Updated markdown text from editor')
      
      // Log a preview of the markdown for debugging
      if (markdown.length > 0) {
        console.log('Markdown preview:', markdown.substring(0, Math.min(100, markdown.length)) + '...')
      }
    } catch (error) {
      console.error('Error updating markdown from editor:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)
  
    try {
      console.log('Submitting text for memo generation with template:', selectedTemplate)
      console.log('Markdown text length:', markdownText.length)
      
      // Log a preview of what's being sent to the API
      if (markdownText.length > 0) {
        console.log('Sending markdown preview:', markdownText.substring(0, Math.min(100, markdownText.length)) + '...')
      } else {
        console.warn('Warning: Empty markdown text being sent to API')
      }
      
      localStorage.setItem('nextRoute', '/result')
      
      // Use the markdown text for API submission
      const result = await apiClient.generateMemo(markdownText, selectedTemplate)
      
      localStorage.setItem('job_id', result.job_id)
      console.log('Memo generation job created, job_id:', result.job_id)
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
            <Slate
              editor={editor}
              initialValue={initialValue}
              onChange={handleEditorChange}
            >
              <Editable
                className="h-full prose prose-slate dark:prose-invert max-w-none focus:outline-none"
                renderElement={props => <CustomElement {...props} />}
                renderLeaf={props => <CustomLeaf {...props} />}
                placeholder="Edit the text here..."
              />
            </Slate>
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