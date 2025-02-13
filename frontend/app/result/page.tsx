'use client';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function extractThinkContent(text: string): { mainContent: string; thinkContent: string | null } {
  if (!text) {
    return { mainContent: '', thinkContent: null };
  }
  const pattern = /<think>([\s\S]+?)<\/think>/i;
  const match = text.match(pattern);
  if (match) {
    const thinkContent = match[1].trim();
    const mainContent = text.replace(pattern, '').trim();
    return { mainContent, thinkContent };
  }
  return { mainContent: text, thinkContent: null };
}

async function validateText(text: string): Promise<string> {
  const response = await fetch('http://localhost:5000/validate_selection', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selected_text: text }),
  });

  if (!response.ok) {
    throw new Error('Failed to validate text');
  }

  const data = await response.json();
  return data.validation_html;
}

export default function Result() {
  const searchParams = useSearchParams();
  const memoParam = searchParams.get('memo') || '';
  
  // Separate <think> content from the memo
  const { mainContent: memoMain, thinkContent: memoThink } = extractThinkContent(memoParam);

  // State variables
  const [validationHtml, setValidationHtml] = useState('');
  const [isValidationExpanded, setIsValidationExpanded] = useState(false);
  const [isMemoExpanded, setIsMemoExpanded] = useState(true); // Memo starts expanded
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);

  async function handleValidateClick() {
    const selection = window.getSelection()?.toString() || '';
    if (!selection) {
      console.warn('No text selected.');
      return;
    }
    try {
      const html = await validateText(selection);
      setValidationHtml(html);
      setIsValidationExpanded(true);
    } catch (error) {
      console.error('Validation error:', error);
      setValidationHtml('<p>Failed to load validation results.</p>');
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="max-w-4xl mx-auto">

        {/* Top Bar */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold">Investment Memo</h1>
          <Link
            href="/"
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg"
          >
            Analyze Another Deck
          </Link>
        </div>

        {/* Validate Selection Button */}
        <button
          onClick={handleValidateClick}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg mt-4"
        >
          Validate Selection
        </button>

        {/* Validation Results Box */}
        {validationHtml && (
          <div className="mt-4 border border-gray-700 rounded-lg">
            <button
              onClick={() => setIsValidationExpanded(!isValidationExpanded)}
              className="w-full p-4 text-left bg-gray-800 hover:bg-gray-700 rounded-t-lg flex justify-between items-center"
            >
              <span className="font-semibold">Validation Results</span>
              <span>{isValidationExpanded ? '▼' : '▶'}</span>
            </button>
            {isValidationExpanded && (
              <div
                className="p-4 bg-gray-900 rounded-b-lg"
                dangerouslySetInnerHTML={{ __html: validationHtml }}
              />
            )}
          </div>
        )}

        {/* Investment Memo Box (Collapsible) */}
        <div className="mt-6 border border-gray-700 rounded-lg">
          <button
            onClick={() => setIsMemoExpanded(!isMemoExpanded)}
            className="w-full p-4 text-left bg-gray-800 hover:bg-gray-700 rounded-t-lg flex justify-between items-center"
          >
            <span className="font-semibold">Investment Memo Text</span>
            <span>{isMemoExpanded ? '▼' : '▶'}</span>
          </button>
          {isMemoExpanded && (
            <div
              className="p-4 bg-gray-900 rounded-b-lg"
              style={{
                userSelect: 'text',
                WebkitUserSelect: 'text',
                MozUserSelect: 'text',
                msUserSelect: 'text',
              }}
            >
              <div className="prose prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {memoMain}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>

        {/* Model Reasoning Box */}
        {memoThink && (
          <div className="mt-4 border border-gray-700 rounded-lg">
            <button
              onClick={() => setIsThinkingExpanded(!isThinkingExpanded)}
              className="w-full p-4 text-left bg-gray-800 hover:bg-gray-700 rounded-t-lg flex justify-between items-center"
            >
              <span className="font-semibold">Model Reasoning</span>
              <span>{isThinkingExpanded ? '▼' : '▶'}</span>
            </button>
            {isThinkingExpanded && (
              <div className="p-4 bg-gray-900 rounded-b-lg">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {memoThink}
                </ReactMarkdown>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}