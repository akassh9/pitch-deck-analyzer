import React from 'react';

interface ValidationResult {
  title: string;
  snippet: string;
  link: string;
}

interface ValidationProps {
  results: ValidationResult[];
}

export const ValidationResults: React.FC<ValidationProps> = ({ results }) => {
  return (
    <div className="space-y-4">
      {results.length > 0 ? (
        results.map((result, index) => (
          <div
            key={index}
            className="p-4 bg-background border border-border rounded-md shadow-sm 
                       hover:bg-background/80 transition-colors"
          >
            <a
              href={result.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary font-semibold hover:underline"
            >
              {result.title}
            </a>
            <p className="mt-1 text-sm text-secondary-foreground/80">
              {result.snippet}
            </p>
          </div>
        ))
      ) : (
        <p className="text-secondary-foreground/80">
          No validation results found.
        </p>
      )}
    </div>
  );
};
