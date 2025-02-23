'use client';

import { useEffect, useState } from 'react';
import ResultsDisplay from '@/components/ResultsDisplay';
import EmailSignup from '@/components/EmailSignup';

interface PageProps {
  params: {
    id: string;
  };
}

export default function ResultsPage({ params }: PageProps) {
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const pollResults = async () => {
      try {
        const response = await fetch(`/api/results/${params.id}`);
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || 'Failed to fetch results');
        }

        if (data.submission.status === 'completed') {
          setResults(data.submission.analysis);
          setLoading(false);
        } else if (data.submission.status === 'error') {
          setError('Analysis failed. Please try again.');
          setLoading(false);
        } else {
          // Continue polling if still processing
          setTimeout(pollResults, 2000);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        setLoading(false);
      }
    };

    pollResults();
  }, [params.id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-3/4 mx-auto mb-8"></div>
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3 mx-auto"></div>
          </div>
        </div>
        <p className="mt-8 text-gray-600">Analyzing your manuscript...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="bg-red-50 border border-red-200 rounded-md p-6">
          <h2 className="text-lg font-medium text-red-800 mb-2">Error</h2>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!results) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Manuscript Analysis Results
        </h1>
        <p className="text-gray-600">
          Here's what our AI analysis found about your manuscript
        </p>
      </div>

      <ResultsDisplay results={results} />
      <EmailSignup submissionId={params.id} />
    </div>
  );
}
