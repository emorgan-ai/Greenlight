import { PDFDocument } from 'pdf-lib';
import pdfParse from 'pdf-parse';

export async function validatePDF(buffer: Buffer) {
  try {
    const pdfDoc = await PDFDocument.load(buffer);
    const pageCount = pdfDoc.getPageCount();
    
    if (pageCount > Number(process.env.MAX_PAGES || 10)) {
      throw new Error(`PDF exceeds maximum page limit of ${process.env.MAX_PAGES || 10} pages`);
    }

    const fileSizeInMB = buffer.length / (1024 * 1024);
    if (fileSizeInMB > Number(process.env.MAX_FILE_SIZE_MB || 10)) {
      throw new Error(`File size exceeds maximum limit of ${process.env.MAX_FILE_SIZE_MB || 10}MB`);
    }

    return true;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Invalid PDF: ${error.message}`);
    }
    throw new Error('Invalid PDF file');
  }
}

export async function extractTextFromPDF(buffer: Buffer): Promise<string> {
  try {
    const data = await pdfParse(buffer);
    return data.text;
  } catch (error) {
    throw new Error('Failed to extract text from PDF');
  }
}
