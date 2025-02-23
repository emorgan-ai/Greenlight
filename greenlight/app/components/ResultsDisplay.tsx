import { useState } from 'react';

interface BookDetails {
  title: string;
  author: string;
  imprint: string;
  publication_date: string;
  nyt_bestseller: boolean;
  copies_sold: string;
  marketing_strategy: string;
  reason?: string;
}

interface AnalysisResults {
  genre: string;
  tropes: string[];
  themes: string[];
  comparable_titles: BookDetails[];
}

interface ResultsDisplayProps {
  results: AnalysisResults;
}

export default function ResultsDisplay({ results }: ResultsDisplayProps) {
  const [expandedCard, setExpandedCard] = useState<number | null>(null);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Primary Analysis */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Genre</h3>
          <p className="text-gray-700">{results.genre}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Themes</h3>
          <ul className="list-disc list-inside text-gray-700">
            {results.themes.map((theme, index) => (
              <li key={index}>{theme}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Tropes */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Literary Tropes</h3>
        <div className="flex flex-wrap gap-2">
          {results.tropes.map((trope, index) => (
            <span
              key={index}
              className="px-3 py-1 rounded-full text-sm bg-primary-100 text-primary-800"
            >
              {trope}
            </span>
          ))}
        </div>
      </div>

      {/* Comparable Titles */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-gray-900">Comparable Titles</h3>
        <div className="grid gap-6">
          {results.comparable_titles.map((book, index) => (
            <div
              key={index}
              className="bg-white rounded-lg shadow overflow-hidden"
            >
              <button
                onClick={() => setExpandedCard(expandedCard === index ? null : index)}
                className="w-full text-left p-6"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <h4 className="text-lg font-medium text-gray-900">
                      {book.title}
                    </h4>
                    <p className="text-gray-600">by {book.author}</p>
                  </div>
                  <svg
                    className={`w-5 h-5 transform transition-transform ${
                      expandedCard === index ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
                {book.reason && (
                  <p className="mt-2 text-gray-600">{book.reason}</p>
                )}
              </button>

              {expandedCard === index && (
                <div className="px-6 pb-6 space-y-4 border-t border-gray-200 pt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h5 className="text-sm font-medium text-gray-500">Imprint</h5>
                      <p className="text-gray-900">{book.imprint}</p>
                    </div>
                    <div>
                      <h5 className="text-sm font-medium text-gray-500">Publication Date</h5>
                      <p className="text-gray-900">{book.publication_date}</p>
                    </div>
                    <div>
                      <h5 className="text-sm font-medium text-gray-500">NYT Bestseller</h5>
                      <p className="text-gray-900">
                        {book.nyt_bestseller ? 'Yes' : 'No'}
                      </p>
                    </div>
                    <div>
                      <h5 className="text-sm font-medium text-gray-500">Copies Sold</h5>
                      <p className="text-gray-900">{book.copies_sold}</p>
                    </div>
                  </div>
                  <div>
                    <h5 className="text-sm font-medium text-gray-500">Marketing Strategy</h5>
                    <p className="text-gray-900 mt-1">{book.marketing_strategy}</p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
