import { NextApiRequest, NextApiResponse } from 'next';
import { clientPromise } from '../../lib/mongodb';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const results = {
    mongodb: { success: false, error: null },
    openai: { success: false, error: null },
    env: {
      hasMongoDB: !!process.env.MONGODB_URI,
      hasOpenAI: !!process.env.OPENAI_API_KEY,
      mongoDBLength: process.env.MONGODB_URI?.length || 0,
      openAILength: process.env.OPENAI_API_KEY?.length || 0,
    }
  };

  // Test MongoDB connection
  try {
    const client = await clientPromise;
    const db = client.db('greenlight');
    const collections = await db.listCollections().toArray();
    results.mongodb = {
      success: true,
      error: null,
      collections: collections.map(c => c.name)
    };
  } catch (error) {
    results.mongodb = {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }

  // Test OpenAI connection
  try {
    const completion = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "user",
          content: "Test connection. Respond with 'Connected successfully' if you receive this."
        }
      ]
    });
    results.openai = {
      success: true,
      error: null,
      response: completion.choices[0].message.content
    };
  } catch (error) {
    results.openai = {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }

  // Return results
  return res.status(200).json(results);
}
