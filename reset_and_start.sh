#!/bin/bash

echo "🔄 Resetting golf betting app..."

# Kill any running app instances
echo "📱 Killing running app instances..."
pkill -f "python app.py" 2>/dev/null || true

# Remove database files
echo "🗑️  Removing old database files..."
rm -f golf_betting.db db.sqlite3

# Reseed the database
echo "🌱 Reseeding database..."
PYTHONPATH=. venv/bin/python services/seeder.py

# Start the app
echo "🚀 Starting the app..."
PYTHONPATH=. venv/bin/python app.py 