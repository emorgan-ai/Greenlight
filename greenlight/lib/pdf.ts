import { PDFDocument } from 'pdf-lib';
import pdf from 'pdf-parse';

export async function validatePDF(buffer: Buffer) {
  try {
    // Try to load the PDF to verify it's valid
    const pdfDoc = await PDFDocument.load(buffer);
    const pageCount = pdfDoc.getPageCount();

    if (pageCount > 10) {
      throw new Error('PDF must be 10 pages or less');
    }

    return true;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Invalid PDF file');
  }
}

export async function extractTextFromPDF(buffer: Buffer) {
  try {
    const data = await pdf(buffer);
    return data.text;
  } catch (error) {
    console.error('Error extracting text from PDF:', error);
    throw new Error('Failed to extract text from PDF');
  }
}
