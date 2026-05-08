#!/usr/bin/env bash
# Render build script — runs during deploy
set -o errexit

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build complete!"
echo "ℹ️  Database init & seeding will run at application startup."
