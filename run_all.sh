#!/bin/bash
# Run the full oncology article pipeline

set -e

echo "🔬 Starting Oncology Article Crawler & Search System"
echo "=================================================="

# Check if virtual environment Python exists
PYTHON_PATH="D:/crew/.venv/Scripts/python.exe"
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Error: Virtual environment not found at $PYTHON_PATH"
    echo "Please run: python -m venv .venv and install requirements"
    exit 1
fi

# Load GOOGLE_API_KEY from config.ini (simple parser)
GOOGLE_API_KEY=$(awk -F '=' '/GOOGLE_API_KEY/ {gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2}' config.ini | tr -d '"')
export GOOGLE_API_KEY

echo "🔑 API Key configured"

# Check current database status
echo "📊 Checking current database..."
ARTICLE_COUNT=$($PYTHON_PATH -c "import sqlite3; conn = sqlite3.connect('oncology_articles.db'); c = conn.cursor(); c.execute('CREATE TABLE IF NOT EXISTS articles (id INTEGER PRIMARY KEY, title TEXT, authors TEXT, pub_date TEXT, abstract TEXT, url TEXT UNIQUE)'); c.execute('SELECT COUNT(*) FROM articles'); print(c.fetchone()[0]); conn.close()" 2>/dev/null || echo "0")
echo "📚 Current articles in database: $ARTICLE_COUNT"

# Step 1: Scrape articles (optional - ask user)
echo ""
read -p "🕷️  Do you want to scrape NEW articles? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🕷️  Scraping new oncology articles..."
    $PYTHON_PATH scrape_articles.py
    NEW_COUNT=$($PYTHON_PATH -c "import sqlite3; conn = sqlite3.connect('oncology_articles.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM articles'); print(c.fetchone()[0]); conn.close()")
    echo "✅ Scraping complete! Total articles: $NEW_COUNT"
else
    echo "⏭️  Skipping scraping, using existing $ARTICLE_COUNT articles"
fi

# Step 2: Embed and index articles
echo ""
echo "🧠 Creating embeddings and updating vector database..."
$PYTHON_PATH embed_and_index.py

if [ $? -eq 0 ]; then
    echo "✅ Vector database updated successfully!"
else
    echo "❌ Error creating embeddings. Check your configuration."
    exit 1
fi

# Step 3: Launch Streamlit app
echo ""
echo "🚀 Starting Streamlit web application..."
echo "📱 The app will open at: http://localhost:8502"
echo "🔍 You can search through your oncology research database!"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Use the virtual environment Python to run Streamlit
$PYTHON_PATH -m streamlit run app.py
