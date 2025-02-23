import { MongoClient } from 'mongodb';

if (!process.env.MONGODB_URI) {
  throw new Error('Please add your Mongo URI to .env.local');
}

const uri = process.env.MONGODB_URI;
const options = {};

let client;
let clientPromise: Promise<MongoClient>;

if (process.env.NODE_ENV === 'development') {
  // In development mode, use a global variable so that the value
  // is preserved across module reloads caused by HMR (Hot Module Replacement).
  let globalWithMongo = global as typeof globalThis & {
    _mongoClientPromise?: Promise<MongoClient>;
  };

  if (!globalWithMongo._mongoClientPromise) {
    client = new MongoClient(uri, options);
    globalWithMongo._mongoClientPromise = client.connect();
  }
  clientPromise = globalWithMongo._mongoClientPromise;
} else {
  // In production mode, it's best to not use a global variable.
  client = new MongoClient(uri, options);
  clientPromise = client.connect();
}

export async function insertSubmission(data: any) {
  const client = await clientPromise;
  const db = client.db('greenlight');
  return db.collection('submissions').insertOne({
    ...data,
    created_at: new Date(),
    status: 'pending'
  });
}

export async function updateSubmission(id: string, data: any) {
  const client = await clientPromise;
  const db = client.db('greenlight');
  return db.collection('submissions').updateOne(
    { _id: id },
    { $set: { ...data, updated_at: new Date() } }
  );
}

export async function getSubmission(id: string) {
  const client = await clientPromise;
  const db = client.db('greenlight');
  return db.collection('submissions').findOne({ _id: id });
}

export async function insertEmailSignup(email: string, submissionId: string) {
  const client = await clientPromise;
  const db = client.db('greenlight');
  return db.collection('email_signups').insertOne({
    email,
    submission_id: submissionId,
    created_at: new Date()
  });
}

// Export a module-scoped MongoClient promise. By doing this in a
// separate module, the client can be shared across functions.
export default clientPromise;
