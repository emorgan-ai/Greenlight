'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-100">
      <main className="max-w-4xl mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-8">
            Welcome to Greenlight
          </h1>
          <p className="text-xl text-gray-600 mb-12">
            AI-powered manuscript analysis for literary agents
          </p>
          
          <Link
            href="/upload"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Get Started
          </Link>
        </div>

        <div className="mt-20 grid grid-cols-1 gap-8 md:grid-cols-2">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              For Literary Agents
            </h2>
            <p className="text-gray-600">
              Save time by letting our AI analyze manuscripts for genre fit, market potential,
              and writing quality. Get instant insights to help with your decision-making process.
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              How It Works
            </h2>
            <ol className="text-gray-600 space-y-2">
              <li>1. Upload your manuscript (PDF, max 10 pages)</li>
              <li>2. Provide a brief synopsis</li>
              <li>3. Get AI-powered analysis and insights</li>
              <li>4. Make informed decisions faster</li>
            </ol>
          </div>
        </div>
      </main>
    </div>
  );
}
