# Greenlight - Literary Agent Submission Analysis Tool

A web-based tool for literary agents to analyze manuscript submissions using AI. Built with Next.js, MongoDB, and OpenAI GPT.

## Features

- PDF manuscript upload (max 10 pages)
- Synopsis submission
- AI-powered analysis using GPT-4 Turbo
- Comparable titles analysis with detailed metadata
- Email signup for updates
- Green-accented modern UI

## Technical Stack

- Frontend: Next.js + Tailwind CSS
- Backend: Next.js API Routes
- Database: MongoDB Atlas
- AI: OpenAI GPT-4 Turbo
- Deployment: Vercel

## Setup Instructions

1. Install Node.js and npm
```bash
# For macOS, install Homebrew first:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then install Node.js:
brew install node
```

2. Install project dependencies
```bash
npm install
```

3. Set up environment variables
```bash
cp .env.example .env.local
# Edit .env.local with your API keys and configuration
```

4. Run development server
```bash
npm run dev
```

5. Build for production
```bash
npm run build
```

## Environment Variables

Create a `.env.local` file with the following variables:

```env
MONGODB_URI=your_mongodb_connection_string
OPENAI_API_KEY=your_openai_api_key
OPENAI_ORG_ID=your_openai_org_id
```

## Project Structure

```
greenlight/
├── src/
│   ├── app/
│   │   ├── upload/
│   │   │   └── page.tsx
│   │   ├── results/
│   │   │   └── page.tsx
│   │   └── api/
│   │       ├── upload/
│   │       ├── process/
│   │       ├── signup/
│   │       └── results/
│   ├── components/
│   │   ├── UploadForm.tsx
│   │   ├── ResultsDisplay.tsx
│   │   └── EmailSignup.tsx
│   └── lib/
│       ├── mongodb.ts
│       ├── openai.ts
│       └── pdf.ts
├── public/
├── .env.local
├── package.json
└── tailwind.config.js
```

## Development Status

- [ ] Phase 1: Next.js Frontend
- [ ] Phase 2: API Backend
- [ ] Phase 3: Advanced AI Processing
- [ ] Phase 4: Email Signup Feature
- [ ] Phase 5: Optimization & Deployment
