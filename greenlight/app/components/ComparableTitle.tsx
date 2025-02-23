'use client';

import { useState } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

interface Book {
  title: string;
  author: string;
  year?: number;
  reason?: string;
  imprint?: string;
  publishingHouse?: string;
  estimatedCopiesSold?: string;
  isNYTBestseller?: boolean;
  marketingStrategy?: string;
  summary?: string;
}

interface ComparableTitleProps {
  book: Book;
}

export default function ComparableTitle({ book }: ComparableTitleProps) {
  return (
    <div className="border rounded-lg bg-white p-6 space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900">
          {book.title} by {book.author}
        </h3>
        {book.year && (
          <p className="text-sm text-gray-500">Published in {book.year}</p>
        )}
      </div>

      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 text-sm">
        {book.publishingHouse && (
          <div>
            <dt className="font-medium text-gray-900">Publishing House</dt>
            <dd className="mt-1 text-gray-600">{book.publishingHouse}</dd>
          </div>
        )}
        
        {book.imprint && (
          <div>
            <dt className="font-medium text-gray-900">Imprint</dt>
            <dd className="mt-1 text-gray-600">{book.imprint}</dd>
          </div>
        )}

        {book.estimatedCopiesSold && (
          <div>
            <dt className="font-medium text-gray-900">Estimated Copies Sold</dt>
            <dd className="mt-1 text-gray-600">{book.estimatedCopiesSold}</dd>
          </div>
        )}

        {book.isNYTBestseller !== undefined && (
          <div>
            <dt className="font-medium text-gray-900">NYT Bestseller</dt>
            <dd className="mt-1 text-gray-600">
              {book.isNYTBestseller ? 'Yes' : 'No'}
            </dd>
          </div>
        )}
      </dl>

      {book.summary && (
        <div className="border-t pt-4">
          <h4 className="font-medium text-gray-900 mb-2">Book Summary</h4>
          <p className="text-gray-600 text-sm">{book.summary}</p>
        </div>
      )}

      {book.marketingStrategy && (
        <div className="border-t pt-4">
          <h4 className="font-medium text-gray-900 mb-2">Marketing Strategy</h4>
          <p className="text-gray-600 text-sm">{book.marketingStrategy}</p>
        </div>
      )}

      {book.reason && (
        <div className="border-t pt-4">
          <h4 className="font-medium text-gray-900 mb-2">Why It's Similar</h4>
          <p className="text-gray-600 text-sm whitespace-pre-wrap">{book.reason}</p>
        </div>
      )}
    </div>
  );
}
