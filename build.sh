#!/bin/bash
echo "Building TraderAdmin..."

cd frontend
npm ci
npm run build
cd ..

wails build

echo "Build complete! Output in build/bin directory." 