import { NextApiRequest, NextApiResponse } from 'next';
import { insertSubmission } from '../../lib/mongodb';
import { validatePDF, extractTextFromPDF } from '../../lib/pdf';

export const config = {
  api: {
    bodyParser: false,
  },
};

import formidable from 'formidable';
import { createReadStream } from 'fs';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  console.log('[API] POST /api/upload - Start');

  try {
    const form = formidable({});
    const [fields, files] = await form.parse(req);

    console.log('[API] Form data received:', {
      fields: Object.keys(fields),
      files: Object.keys(files),
    });

    const synopsis = fields.synopsis?.[0];
    const file = files.file?.[0];

    if (!synopsis || !file) {
      console.log('[API] Missing required fields:', { synopsis: !!synopsis, file: !!file });
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Read file buffer
    console.log('[API] Reading file buffer');
    const fileStream = createReadStream(file.filepath);
    const chunks: Buffer[] = [];
    
    for await (const chunk of fileStream) {
      chunks.push(Buffer.from(chunk));
    }
    
    const buffer = Buffer.concat(chunks);

    // Validate PDF
    console.log('[API] Validating PDF');
    try {
      await validatePDF(buffer);
    } catch (error) {
      console.error('[API] PDF validation error:', error);
      return res.status(400).json({
        error: error instanceof Error ? error.message : 'Invalid PDF file',
      });
    }

    // Extract text from PDF
    console.log('[API] Extracting text from PDF');
    let text;
    try {
      text = await extractTextFromPDF(buffer);
      console.log('[API] Extracted text length:', text.length);
    } catch (error) {
      console.error('[API] Text extraction error:', error);
      return res.status(500).json({ error: 'Failed to extract text from PDF' });
    }

    // Insert submission record
    console.log('[API] Inserting submission to MongoDB');
    let submission;
    try {
      submission = await insertSubmission({
        synopsis,
        text,
        file_name: file.originalFilename || 'unnamed.pdf',
        file_size: file.size,
        status: 'uploaded',
        created_at: new Date(),
      });
      console.log('[API] Submission created successfully:', submission.insertedId);
    } catch (error) {
      console.error('[API] Database error:', error);
      return res.status(500).json({ error: 'Failed to save submission' });
    }

    // Trigger analysis in the background
    console.log('[API] Triggering analysis');
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/process/${submission.insertedId}`, {
      method: 'POST',
    }).catch(error => {
      console.error('[API] Error triggering analysis:', error);
    });

    return res.status(200).json({
      success: true,
      submissionId: submission.insertedId,
    });
  } catch (error) {
    console.error('[API] Unexpected error:', error);
    return res.status(500).json({
      error: error instanceof Error ? error.message : 'Upload failed',
    });
  }
}
