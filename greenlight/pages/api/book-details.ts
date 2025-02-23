import { NextApiRequest, NextApiResponse } from 'next';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { title, author } = req.query;

  if (!title || !author) {
    return res.status(400).json({ error: 'Missing title or author' });
  }

  try {
    const prompt = `Please provide detailed information about the book "${title}" by ${author}. Include:
1. Publisher/Imprint
2. Whether it was a New York Times bestseller
3. Key marketing strategies used to promote the book
4. A brief summary of the book

Format your response as JSON with these fields:
- imprint: string
- isNYTBestseller: boolean
- marketingStrategy: string (bullet points)
- summary: string

If you're not certain about any information, omit that field from the JSON response.`;

    const completion = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: "You are a knowledgeable literary agent's assistant with expertise in book publishing and marketing. Provide accurate information about books, their publication details, and marketing strategies."
        },
        {
          role: "user",
          content: prompt
        }
      ]
    });

    const content = completion.choices[0].message.content;
    const jsonStr = content.replace(/```json\n?|\n?```/g, '').trim();
    const bookDetails = JSON.parse(jsonStr);

    return res.status(200).json(bookDetails);
  } catch (error) {
    console.error('Error fetching book details:', error);
    return res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to fetch book details'
    });
  }
}
