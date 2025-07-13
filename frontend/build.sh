#!/bin/bash

# Build script for PowerStreamPlan frontend
# This script builds the Vue 3 application and copies it to the Flask static directory

set -e

echo "🏗️  Building PowerStreamPlan Frontend..."

# Navigate to frontend directory
cd "$(dirname "$0")"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Run type check
echo "🔍 Running type check..."
npm run type-check

# Build the application
echo "🚀 Building application..."
npm run build

echo "✅ Frontend build completed successfully!"
echo "📁 Output directory: ../power_stream_plan/static/dist/"

# Check if build was successful
if [ -d "../power_stream_plan/static/dist" ]; then
    echo "🎉 Build files are ready for production!"
else
    echo "❌ Build failed - output directory not found"
    exit 1
fi
