#!/bin/bash

# Kill any process using port 3000
echo "Checking for processes on port 3000..."
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs -r kill -9

# Clean up Next.js cache
echo "Cleaning Next.js cache..."
rm -rf .next

# Start the development server
echo "Starting Next.js development server..."
npm run dev
