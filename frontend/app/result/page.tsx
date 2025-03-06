'use client'

import { useState, useEffect } from "react"
import { ArrowLeft, ChevronDown, ChevronUp, Send } from "lucide-react"
import Link from "next/link"
import { apiClient } from "../../lib/api-client"
import { ValidationResults } from "../../components/ValidationResults"
import dynamic from 'next/dynamic'

// Dynamically import ReactMarkdown with SSR disabled
const ReactMarkdown = dynamic(() => import('react-markdown'), {
  ssr: false,
})

export default function ResultsPage() {
  const [generatedMemo, setGeneratedMemo] = useState("")
  const [templateUsed, setTemplateUsed] = useState("")
  const [startupStage, setStartupStage] = useState("")
  
  interface ValidationResult {
    title: string;
    snippet: string;
    link: string;
  }
  
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);  
  const [modelReasoning, setModelReasoning] = useState("")
  const [isValidationOpen, setIsValidationOpen] = useState(false)
  const [isReasoningOpen, setIsReasoningOpen] = useState(false)

  useEffect(() => {
    async function processText() {
      try {
        console.log('Processing stored data...'); // Debug log
        
        const memo = localStorage.getItem("memo");
        const template = localStorage.getItem("template_used");
        const stage = localStorage.getItem("startup_stage");
        
        console.log('Retrieved from localStorage:', { memo, template, stage }); // Debug log
        
        if (!memo) {
          console.error('No memo found in localStorage');
          return;
        }
        
        // If the memo contains <think> tags, extract them
        const thinkRegex = /<think>([\s\S]*?)<\/think>/i;
        const match = memo.match(thinkRegex);
        
        if (match) {
          const reasoning = match[1].trim();
          // Remove the <think> block from the memo
          const cleanedMemo = memo.replace(thinkRegex, "").trim();
          console.log('Extracted reasoning:', reasoning); // Debug log
          console.log('Cleaned memo:', cleanedMemo); // Debug log
          
          setGeneratedMemo(cleanedMemo);
          setModelReasoning(reasoning);
        } else {
          console.log('No reasoning found, using full memo'); // Debug log
          setGeneratedMemo(memo);
        }
        
        setTemplateUsed(template || 'default');
        setStartupStage(stage || 'default');
        
      } catch (error) {
        console.error('Error processing memo:', error);
        setGeneratedMemo('Error: Failed to process memo');
      }
    }

    processText();
  }, []);

  const handleValidateClick = async () => {
    const selection = window.getSelection()?.toString() || "";
    if (!selection) {
      alert("Please select some text to validate.");
      return;
    }
    try {
      const results = await apiClient.validateSelection(selection);
      setValidationResults(results);
      setIsValidationOpen(true);
    } catch (error) {
      console.error("Validation error:", error);
      alert("Validation failed. Please try again.");
    }
  }

  return (
    <div className="h-screen bg-background text-foreground flex flex-col p-8">
      <div className="w-3/4 mx-auto flex flex-col mt-18">
        {/* Top bar with Back link on the left and two buttons on the right */}
        <div className="flex items-center justify-between mb-8">
          <div className="space-y-4">
            <Link
              href="/edit"
              className="text-primary hover:text-primary-foreground transition-colors flex items-center"
            >
              <ArrowLeft className="mr-2" size={20} />
              Back to Edit Text
            </Link>
            <h1 className="text-4xl font-serif">Analysis Results</h1>
          </div>
          <div className="flex space-x-4">
            <button
              onClick={handleValidateClick}
              className="bg-primary text-primary-foreground rounded-lg px-6 py-2 hover:bg-accent transition-colors flex items-center"
            >
              <Send className="mr-2" size={20} />
              Validate Selection
            </button>
            <Link
              href="/"
              className="bg-primary text-primary-foreground rounded-lg px-6 py-2 hover:bg-accent transition-colors flex items-center"
            >
              <Send className="mr-2" size={20} />
              Analyze New Pitch Deck
            </Link>
          </div>
        </div>

        {/* Metadata box - REMOVED */}

        {/* Validation Results box */}
        <div className="bg-secondary p-6 rounded-lg mb-6 border border-border">
          <button
            onClick={() => setIsValidationOpen(!isValidationOpen)}
            className="flex items-center justify-between w-full text-left"
          >
            <h2 className="text-2xl font-serif">Validation Results</h2>
            {isValidationOpen ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
          </button>

          {isValidationOpen && (
            <div className="mt-4">
              <ValidationResults results={validationResults} />
            </div>
          )}
        </div>

        {/* Generated Memo box */}
        <div className="bg-secondary p-6 rounded-lg mb-6">
          <h2 className="text-2xl font-serif mb-4">Generated Memo</h2>
          <div className="prose prose-slate dark:prose-invert max-w-none 
            prose-headings:font-serif 
            prose-p:font-sans 
            prose-li:font-sans">
            {typeof window !== 'undefined' && (
              <ReactMarkdown>{generatedMemo || 'No memo content available.'}</ReactMarkdown>
            )}
          </div>
        </div>

        {/* Model Reasoning box */}
        {modelReasoning && (
          <div className="bg-secondary p-6 rounded-lg mb-6">
            <button
              onClick={() => setIsReasoningOpen(!isReasoningOpen)}
              className="flex items-center justify-between w-full text-left"
            >
              <h2 className="text-2xl font-serif">Model Reasoning</h2>
              {isReasoningOpen ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
            </button>
            {isReasoningOpen && (
              <div className="prose prose-slate dark:prose-invert max-w-none mt-4
                prose-headings:font-serif 
                prose-p:font-sans 
                prose-li:font-sans">
                {typeof window !== 'undefined' && (
                  <ReactMarkdown>{modelReasoning}</ReactMarkdown>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
