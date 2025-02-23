import Link from 'next/link';

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto text-center">
      <div className="bg-white rounded-lg shadow-sm p-8 mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          AI-Powered Manuscript Analysis
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Upload your manuscript and get instant insights on genre, themes, and comparable titles
        </p>
        <Link
          href="/upload"
          className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Get Started
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="text-primary-600 mb-4">
            <svg className="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Upload Manuscript
          </h3>
          <p className="text-gray-600">
            Submit your manuscript (up to 10 pages) and a brief synopsis
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="text-primary-600 mb-4">
            <svg className="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            AI Analysis
          </h3>
          <p className="text-gray-600">
            Get instant insights powered by GPT-4 Turbo
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="text-primary-600 mb-4">
            <svg className="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Comp Titles
          </h3>
          <p className="text-gray-600">
            Discover relevant comparable titles with detailed market insights
          </p>
        </div>
      </div>
    </div>
  );
}
