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
    <div className="validation-container p-4 bg-gray-900 rounded-lg shadow-lg">
      <h3 className="text-xl font-bold mb-4 text-blue-300">Validation Results</h3>
      {results.length > 0 ? (
        results.map((result, index) => (
          <div key={index} className="validation-card p-4 bg-gray-800 rounded-lg mb-2">
            <a
              href={result.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 font-semibold hover:underline"
            >
              {result.title}
            </a>
            <p className="text-gray-300 mt-1">{result.snippet}</p>
          </div>
        ))
      ) : (
        <p className="text-gray-300">No validation results found.</p>
      )}
    </div>
  );
};