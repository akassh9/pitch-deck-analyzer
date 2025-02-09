'use client';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useState } from 'react';

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

    const handleTextSelection = () => {
        const selection = window.getSelection();
        if (selection) {
            setSelectedText(selection.toString());
        }
    };

    const handleValidateClick = async () => {
        try {
            const html = await validateText(selectedText);
            setValidationHtml(html);
        } catch (error) {
            console.error('Validation error:', error);
            setValidationHtml('<p>Failed to load validation results.</p>');
        }
    };

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
                <div className="bg-secondary p-6 rounded-lg">
                    <pre className="whitespace-pre-wrap" onMouseUp={handleTextSelection}>{memo}</pre>
                </div>
                <button
                    onClick={handleValidateClick}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg mt-4"
                >
                    Validate Selection
                </button>
                <div dangerouslySetInnerHTML={{ __html: validationHtml }} />
            </div>
        </div>
    );
}