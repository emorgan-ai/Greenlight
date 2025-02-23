'use client';

import { useState, useRef, FormEvent } from 'react';

interface UploadFormProps {
  onSubmit: (formData: FormData) => Promise<void>;
  isSubmitting?: boolean;
}

export default function UploadForm({ onSubmit, isSubmitting = false }: UploadFormProps) {
  const [synopsis, setSynopsis] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !synopsis) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('synopsis', synopsis);

    await onSubmit(formData);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        alert('Please upload a PDF file');
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        return;
      }
      if (file.size > 10 * 1024 * 1024) { // 10MB
        alert('File size must be less than 10MB');
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        return;
      }
      setSelectedFile(file);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="synopsis" className="block text-sm font-medium text-gray-700">
          Synopsis
        </label>
        <div className="mt-1">
          <textarea
            id="synopsis"
            name="synopsis"
            rows={4}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
            placeholder="Enter a brief synopsis of your manuscript..."
            value={synopsis}
            onChange={(e) => setSynopsis(e.target.value)}
            maxLength={1000}
            required
          />
        </div>
        <p className="mt-2 text-sm text-gray-500">
          {synopsis.length}/1000 characters
        </p>
      </div>

      <div>
        <label htmlFor="manuscript" className="block text-sm font-medium text-gray-700">
          Manuscript (PDF, max 10MB)
        </label>
        <div className="mt-1">
          <input
            ref={fileInputRef}
            type="file"
            id="manuscript"
            name="manuscript"
            accept="application/pdf"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-semibold
              file:bg-green-50 file:text-green-700
              hover:file:bg-green-100"
            required
          />
        </div>
        {selectedFile && (
          <p className="mt-2 text-sm text-gray-500">
            Selected file: {selectedFile.name}
          </p>
        )}
      </div>

      <div>
        <button
          type="submit"
          disabled={!selectedFile || !synopsis || isSubmitting}
          className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white 
            ${isSubmitting || !selectedFile || !synopsis
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500'
            }`}
        >
          {isSubmitting ? 'Analyzing...' : 'Analyze Manuscript'}
        </button>
      </div>
    </form>
  );
}
