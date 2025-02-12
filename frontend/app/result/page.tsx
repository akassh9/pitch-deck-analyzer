'use client';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Add a helper function to extract and split content
function extractThinkContent(text: string): { mainContent: string; thinkContent: string | null } {
    if (!text) {
        console.log('Received empty text in extractThinkContent');
        return { mainContent: '', thinkContent: null };
    }
    
    // Log whether the text includes think tags
    console.log('Text includes <think>?', text.includes('<think>'));
    console.log('Text includes </think>?', text.includes('</think>'));

    // Match exactly <think>...</think>
    const pattern = /<think>([\s\S]+?)<\/think>/i;
    const match = text.match(pattern);

    if (match) {
        const thinkContent = match[1].trim();
        const mainContent = text.replace(pattern, '').trim();
        console.log('Think content found:', {
            thinkContentPreview: thinkContent.substring(0, 100),
            mainContentPreview: mainContent.substring(0, 100)
        });
        return { mainContent, thinkContent };
    }

    console.log('No think tags found. Content preview:', text.substring(0, 100));
    return { mainContent: text, thinkContent: null };
}

async function validateText(text: string): Promise<string> {
    const response = await fetch('/api/validate-selection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
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
    const memo = searchParams.get('memo') || '';
    const [validationHtml, setValidationHtml] = useState<string>('');
    const [selectedText, setSelectedText] = useState<string>('');
    const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);

    const handleTextSelection = () => {
        const selection = window.getSelection();
        if (selection) {
            setSelectedText(selection.toString());
        }
    };

    const handleValidateClick = async () => {
        try {
            const html = await validateText(selectedText);
            console.log('Raw API response:', html);
            
            // Ensure we're working with decoded HTML before processing
            const decodedHtml = html
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&#x3C;/g, '<')
                .replace(/&#x3E;/g, '>');
                
            setValidationHtml(decodedHtml);
        } catch (error) {
            console.error('Validation error:', error);
            setValidationHtml('<p>Failed to load validation results.</p>');
        }
    };

    // Use memo as a fallback if validationHtml is empty
    const contentToExtract = validationHtml.trim() ? validationHtml : memo;
    const { mainContent, thinkContent } = extractThinkContent(contentToExtract);
    
    console.log('Extracted content:', {
        hasThinkContent: !!thinkContent,
        mainContentLength: mainContent?.length,
        thinkContentLength: thinkContent?.length
    });

    return (
        <div className="min-h-screen bg-background text-foreground p-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-2xl font-bold">Investment Memo</h1>
                    <Link
                        href="/"
                        className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg"
                    >
                        Analyze Another Deck
                    </Link>
                </div>
                <div 
                    className="bg-secondary p-6 rounded-lg"
                    onMouseUp={handleTextSelection}
                >
                    <div className="prose prose-invert max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {memo}
                        </ReactMarkdown>
                    </div>
                </div>
                <button
                    onClick={handleValidateClick}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg mt-4"
                    disabled={!selectedText}
                >
                    Validate Selection
                </button>
                <div className="mt-6 prose prose-invert max-w-none">
                    {/* Main content */}
                    <div className="mb-4">
                        <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                                p: ({ children }) => <p className="whitespace-pre-wrap">{children}</p>
                            }}
                        >
                            {mainContent}
                        </ReactMarkdown>
                    </div>
                    
                    {/* Think content (Model Reasoning) */}
                    {thinkContent && (
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
                                    <ReactMarkdown 
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            p: ({ children }) => <p className="whitespace-pre-wrap">{children}</p>
                                        }}
                                    >
                                        {thinkContent}
                                    </ReactMarkdown>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}