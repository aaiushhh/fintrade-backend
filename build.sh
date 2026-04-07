#!/usr/bin/env bash
# Render build script — runs during deploy
set -o errexit

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🗃️  Running database migrations..."
python -c "
import asyncio
from app.db.database import init_db
asyncio.run(init_db())
print('Tables created successfully')
"

echo "🌱 Seeding default roles and admin..."
python -m app.db.seed

echo "✅ Build complete!"
