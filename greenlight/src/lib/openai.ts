import OpenAI from 'openai';

if (!process.env.OPENAI_API_KEY) {
  throw new Error('Missing OPENAI_API_KEY environment variable');
}

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  organization: process.env.OPENAI_ORG_ID,
});

export interface AnalysisResult {
  genre: string;
  tropes: string[];
  themes: string[];
  comparable_titles: string[];
}

export interface BookMetadata {
  title: string;
  author: string;
  imprint: string;
  publication_date: string;
  nyt_bestseller: boolean;
  copies_sold: string;
  marketing_strategy: string;
}

export async function analyzeManuscript(text: string, synopsis: string): Promise<AnalysisResult> {
  const prompt = `Analyze the following book text and synopsis. Identify the genre, themes, and three comparable published books.
  
Text: ${text.substring(0, 8000)}...

Synopsis: ${synopsis}

Provide the analysis in the following JSON format:
{
  "genre": "Genre name",
  "tropes": ["Trope 1", "Trope 2", "Trope 3"],
  "themes": ["Theme 1", "Theme 2", "Theme 3"],
  "comparable_titles": ["Title 1", "Title 2", "Title 3"]
}`;

  const response = await openai.chat.completions.create({
    model: 'gpt-4-turbo-preview',
    messages: [{ role: 'user', content: prompt }],
    temperature: 0.7,
    response_format: { type: 'json_object' }
  });

  return JSON.parse(response.choices[0].message.content || '{}') as AnalysisResult;
}

export async function getBookMetadata(title: string): Promise<BookMetadata> {
  const prompt = `Provide detailed publication information for the book '${title}'. Include the following information in JSON format:
{
  "title": "Full title",
  "author": "Author name",
  "imprint": "Publishing house/imprint",
  "publication_date": "YYYY-MM-DD",
  "nyt_bestseller": true/false,
  "copies_sold": "Approximate number",
  "marketing_strategy": "Brief summary of launch marketing strategy"
}`;

  const response = await openai.chat.completions.create({
    model: 'gpt-4-turbo-preview',
    messages: [{ role: 'user', content: prompt }],
    temperature: 0.7,
    response_format: { type: 'json_object' }
  });

  return JSON.parse(response.choices[0].message.content || '{}') as BookMetadata;
}

// Cache book metadata in memory to reduce API calls
const metadataCache = new Map<string, BookMetadata & { timestamp: number }>();
const CACHE_DURATION = parseInt(process.env.CACHE_DURATION_HOURS || '24') * 60 * 60 * 1000;

export async function getCachedBookMetadata(title: string): Promise<BookMetadata> {
  const cached = metadataCache.get(title);
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached;
  }

  const metadata = await getBookMetadata(title);
  metadataCache.set(title, { ...metadata, timestamp: Date.now() });
  return metadata;
}
