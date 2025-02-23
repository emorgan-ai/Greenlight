'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import UploadForm from '@/components/UploadForm';

export default function UploadPage() {
  const router = useRouter();
  const [error, setError] = useState('');

  const handleSubmit = async (formData: FormData) => {
    try {
      setError('');
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
        headers: {
          // Remove Content-Type header to let the browser set it with the boundary
          // for multipart/form-data
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Upload failed with status ${response.status}`);
      }

      router.push(`/results/${data.submissionId}`);
    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred during upload');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Upload Your Manuscript
        </h1>
        <p className="text-gray-600">
          Submit up to 10 pages of your manuscript along with a brief synopsis for AI analysis
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      <UploadForm onSubmit={handleSubmit} />
    </div>
  );
}
