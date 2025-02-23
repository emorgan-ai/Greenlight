import { NextApiRequest, NextApiResponse } from 'next';
import { ObjectId } from 'mongodb';
import { getSubmission, updateSubmission } from '../../../lib/mongodb';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

async function analyzeManuscript(text: string, synopsis: string) {
  const currentYear = new Date().getFullYear();
  console.log('Starting manuscript analysis');
  try {
    const prompt = `Analyze this manuscript excerpt and synopsis. Provide two sets of comparable titles:

1. Basic Analysis:
- The likely genre
- 3-5 key themes
- Two sets of comparable titles:
  a) 3 "Best Comps" - The most similar books regardless of publication date
  b) 3 "Recent Comps" - The best matches published within the last 5 years (${currentYear-5} to ${currentYear})

2. For EACH comparable title in BOTH sections, include:
- Title and author
- Publication year
- Publishing house and imprint (if known)
- Estimated copies sold (provide a range if exact numbers unknown)
- Whether it was a NYT bestseller (if known)
- Key marketing strategies used (if known)
- Brief book summary
- Detailed explanation of why it's similar to the manuscript, including:
  * Genre and subgenre alignment
  * Similar themes and how they're explored
  * Voice and writing style comparisons
  * Target audience overlap
  * Similar narrative structures or storytelling techniques
  * Comparable character dynamics or relationships
  * Shared literary devices or tropes
  * Market positioning and reader appeal factors

Manuscript excerpt:
${text.substring(0, 2000)}...

Synopsis:
${synopsis}

Format your response as JSON with these fields:
{
  "genre": string,
  "themes": string[],
  "bestComps": [
    {
      "title": string,
      "author": string,
      "year": number,
      "reason": string,
      "publishingHouse": string,
      "imprint": string,
      "estimatedCopiesSold": string,
      "isNYTBestseller": boolean,
      "marketingStrategy": string,
      "summary": string
    }
  ],
  "recentComps": [
    {
      "title": string,
      "author": string,
      "year": number,
      "reason": string,
      "publishingHouse": string,
      "imprint": string,
      "estimatedCopiesSold": string,
      "isNYTBestseller": boolean,
      "marketingStrategy": string,
      "summary": string
    }
  ]
}

For both "bestComps" and "recentComps", ensure each "reason" field provides a comprehensive analysis that covers multiple aspects of similarity (at least 3-4 paragraphs). Focus on specific examples and detailed comparisons rather than general statements.

For "recentComps", make sure all books were published in ${currentYear-5} or later, even if slightly less similar matches than older books.`;

    console.log('Sending request to OpenAI');
    const completion = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: "You are a literary agent's assistant analyzing manuscript submissions. Provide detailed, professional analysis focusing on marketable aspects of the work. Always respond in valid JSON format with the specified fields. Include as much detail as possible about comparable titles, including sales figures, publishing details, and thorough similarity analysis with specific examples. Ensure recent comps are truly recent and relevant to current market conditions."
        },
        {
          role: "user",
          content: prompt
        }
      ]
    });

    console.log('Received response from OpenAI');
    const content = completion.choices[0].message.content;
    console.log('Raw response:', content);
    
    // Extract JSON from the response
    const jsonStr = content.replace(/```json\n?|\n?```/g, '').trim();
    const analysis = JSON.parse(jsonStr);
    
    console.log('Parsed analysis:', analysis);
    return analysis;
  } catch (error) {
    console.error('Error in analyzeManuscript:', error);
    throw error;
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { id } = req.query;

  if (!id || typeof id !== 'string') {
    return res.status(400).json({ error: 'Invalid submission ID' });
  }

  try {
    console.log('Processing submission:', id);

    // Validate ObjectId format
    if (!ObjectId.isValid(id)) {
      console.log('Invalid submission ID format:', id);
      return res.status(400).json({ error: 'Invalid submission ID format' });
    }

    // Get the submission
    console.log('Fetching submission from database');
    const submission = await getSubmission(id);
    if (!submission) {
      console.log('Submission not found:', id);
      return res.status(404).json({ error: 'Submission not found' });
    }

    // Check if already processed or currently processing
    if (submission.status === 'processing') {
      console.log('Submission is already being processed:', id);
      return res.status(200).json({ message: 'Processing in progress' });
    }

    if (submission.analysis) {
      console.log('Submission already processed:', id);
      return res.status(200).json({ message: 'Already processed', analysis: submission.analysis });
    }

    // Mark as processing
    await updateSubmission(id, { status: 'processing' });

    // Analyze the manuscript
    console.log('Starting analysis for submission:', id);
    const analysis = await analyzeManuscript(submission.text, submission.synopsis);
    console.log('Analysis complete:', analysis);

    // Update the submission with analysis
    console.log('Updating submission with analysis');
    await updateSubmission(id, {
      analysis,
      status: 'analyzed',
      analyzed_at: new Date()
    });

    return res.status(200).json({ success: true, analysis });
  } catch (error) {
    console.error('Error processing submission:', error);
    
    // Mark as error
    try {
      await updateSubmission(id as string, { status: 'error' });
    } catch (updateError) {
      console.error('Error updating submission status:', updateError);
    }

    return res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to process submission',
      details: error instanceof Error ? error.stack : undefined
    });
  }
}
