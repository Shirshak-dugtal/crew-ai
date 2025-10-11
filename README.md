# Oncology Article Crawler & Semantic Search App (Gemini-Powered)

This Python application crawls oncology-specific articles from [Nature Oncology](https://www.nature.com/subjects/oncology), extracts metadata, stores it in SQLite, embeds titles using Gemini embeddings, and enables natural language queries via LangChain and Google Gemini.

## Features
- Scrapes oncology articles (title, author, date, abstract)
- Stores metadata in SQLite
- Embeds titles with Gemini (models/embedding-001) and FAISS
- Semantic search and date filtering via LangChain
- Configurable via `config.ini`
- Shell script to run the full pipeline

## Setup
1. Fill in your Google Gemini API key in `config.ini`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the pipeline:
   ```bash
   bash run_all.sh
   ```

## Configuration
Edit `config.ini` for API keys and paths.

## Tech Stack
- Python, requests, BeautifulSoup4, Selenium (fallback)
- sqlite3, FAISS, LangChain, GoogleGenerativeAIEmbeddings
- configparser

## License
MIT
