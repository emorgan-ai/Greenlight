import { useState } from 'react';

interface EmailSignupProps {
  submissionId: string;
}

export default function EmailSignup({ submissionId }: EmailSignupProps) {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setStatus('loading');
    setMessage('');

    try {
      const response = await fetch('/api/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, submissionId }),
      });

      if (!response.ok) throw new Error('Failed to sign up');

      setStatus('success');
      setMessage("Thanks for signing up! We'll keep you updated on new AI tools for publishing.");
      setEmail('');
    } catch (error) {
      setStatus('error');
      setMessage('Failed to sign up. Please try again.');
    }
  };

  return (
    <div className="mt-8 p-6 bg-green-50 rounded-lg">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Stay Updated
      </h3>
      <p className="text-gray-600 mb-4">
        Sign up to receive updates about our AI tools for publishing.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
            required
          />
        </div>

        {message && (
          <div
            className={`p-4 rounded-md ${
              status === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}
          >
            {message}
          </div>
        )}

        <button
          type="submit"
          disabled={status === 'loading'}
          className="w-full px-4 py-2 text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
        >
          {status === 'loading' ? 'Signing up...' : 'Sign Up'}
        </button>
      </form>
    </div>
  );
}
