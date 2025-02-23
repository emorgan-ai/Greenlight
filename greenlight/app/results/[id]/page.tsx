'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import ComparableTitle from '../../components/ComparableTitle';

interface Book {
  title: string;
  author: string;
  year?: number;
  reason?: string;
  publishingHouse?: string;
  imprint?: string;
  estimatedCopiesSold?: string;
  isNYTBestseller?: boolean;
  marketingStrategy?: string;
  summary?: string;
}

interface Submission {
  _id: string;
  synopsis: string;
  text: string;
  file_name: string;
  file_size: number;
  status: 'uploaded' | 'processing' | 'analyzed' | 'error';
  created_at: string;
  analysis?: {
    genre?: string;
    themes?: string[];
    bestComps?: Book[];
    recentComps?: Book[];
  };
}

export default function ResultsPage() {
  const params = useParams();
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [isPolling, setIsPolling] = useState(true);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        console.log('Fetching results for ID:', params.id);
        const response = await fetch(`/api/results/${params.id}`);
        console.log('Response status:', response.status);
        
        const data = await response.json();
        console.log('Response data:', data);

        if (!response.ok) {
          throw new Error(data.error || 'Failed to fetch results');
        }

        setSubmission(data);

        // If no analysis yet and status isn't error, trigger processing
        if (!data.analysis && data.status !== 'error' && data.status !== 'processing') {
          console.log('No analysis found, triggering processing...');
          fetch(`/api/process/${params.id}`, {
            method: 'POST',
          }).catch(error => {
            console.error('Error triggering analysis:', error);
          });
        }

        // Stop polling if we have analysis or if there's an error
        if (data.analysis || data.status === 'error') {
          console.log('Analysis complete or error occurred, stopping polling');
          setIsPolling(false);
        }
      } catch (err) {
        console.error('Error fetching results:', err);
        setError(err instanceof Error ? err.message : 'Failed to load results');
        setIsPolling(false);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    if (params.id) {
      fetchResults();
    }

    // Poll for updates every 5 seconds if needed
    let interval: NodeJS.Timeout;
    if (isPolling) {
      interval = setInterval(() => {
        if (params.id) {
          console.log('Polling for updates...');
          fetchResults();
        }
      }, 5000);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [params.id, isPolling]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Analyzing Your Manuscript
          </h1>
          <p className="text-gray-600">
            Please wait while we process your submission...
          </p>
          <div className="mt-8 flex justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <h1 className="text-xl font-semibold text-red-800 mb-2">Error</h1>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!submission) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <h1 className="text-xl font-semibold text-yellow-800 mb-2">Submission Not Found</h1>
          <p className="text-yellow-600">The requested submission could not be found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Manuscript Analysis Results
        </h1>
        <p className="text-gray-600">
          Here's what we found in your submission
        </p>
      </div>

      <div className="space-y-8">
        {/* File Info */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Submission Details</h2>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">File Name</dt>
              <dd className="mt-1 text-sm text-gray-900">{submission.file_name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Submission Date</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(submission.created_at).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        </div>

        {/* Synopsis */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Synopsis</h2>
          <p className="text-gray-600 whitespace-pre-wrap">{submission.synopsis}</p>
        </div>

        {/* Analysis Results */}
        {submission.analysis ? (
          <>
            {/* Genre */}
            {submission.analysis.genre && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Genre</h2>
                <p className="text-gray-600">{submission.analysis.genre}</p>
              </div>
            )}

            {/* Themes */}
            {submission.analysis.themes && submission.analysis.themes.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Themes</h2>
                <ul className="list-disc list-inside space-y-2">
                  {submission.analysis.themes.map((theme, index) => (
                    <li key={index} className="text-gray-600">{theme}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Best Comps */}
            {submission.analysis.bestComps && submission.analysis.bestComps.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Best Comparable Titles</h2>
                <div className="space-y-6">
                  {submission.analysis.bestComps.map((book, index) => (
                    <ComparableTitle key={index} book={book} />
                  ))}
                </div>
              </div>
            )}

            {/* Recent Comps */}
            {submission.analysis.recentComps && submission.analysis.recentComps.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Comparable Titles</h2>
                <p className="text-sm text-gray-500 mb-4">Published within the last 5 years</p>
                <div className="space-y-6">
                  {submission.analysis.recentComps.map((book, index) => (
                    <ComparableTitle key={index} book={book} />
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <p className="text-yellow-600">
              {submission.status === 'error' ? (
                'An error occurred while analyzing your manuscript. Please try uploading again.'
              ) : (
                'Analysis is in progress. This page will automatically update when the analysis is complete.'
              )}
            </p>
            {submission.status !== 'error' && (
              <div className="mt-4 flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500"></div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
