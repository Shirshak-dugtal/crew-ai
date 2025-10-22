# 🔬 Oncology Article Crawler & Semantic Search

A comprehensive Python application that intelligently crawls oncology research articles from [Nature Oncology](https://www.nature.com/subjects/oncology), processes them with AI embeddings, and provides semantic search capabilities through an interactive web interface.

## ✨ Features

### 🕷️ Intelligent Web Scraping
- **Multi-source crawling**: Scrapes from Nature Oncology and related search pages
- **Robust extraction**: Multiple fallback strategies for titles, authors, abstracts, and publication dates
- **Smart filtering**: Automatic detection of oncology-relevant content using keyword heuristics
- **Duplicate prevention**: URL-based deduplication in SQLite database

### 🧠 AI-Powered Embeddings
- **Primary**: Google Gemini embeddings (models/embedding-001) for semantic understanding
- **Fallback**: TF-IDF vectorization (768-dimensional) for offline testing
- **Vector storage**: FAISS indexing for fast similarity search

### 🔍 Advanced Search Interface
- **Semantic search**: Natural language queries like "breast cancer immunotherapy"
- **Date filtering**: Search within specific publication date ranges
- **Combined search**: Semantic similarity + temporal filtering
- **Interactive UI**: Clean Streamlit web interface with expandable results

### ⚙️ Flexible Configuration
- **Config-driven**: All settings via `config.ini`
- **Environment support**: Virtual environment integration
- **Cross-platform**: Works on Windows (`run_all.bat`) and Unix (`run_all.sh`)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Gemini API key (optional - TF-IDF fallback available)

### Installation
1. **Clone and navigate to the project**:
   ```bash
   cd oncology_crawler
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key** (optional):
   Edit `config.ini` and add your Google Gemini API key:
   ```ini
   [DEFAULT]
   GOOGLE_API_KEY = your_api_key_here
   ```

### Running the Application

#### Option 1: Full Pipeline (Recommended)
```bash
# Windows
run_all.bat

# macOS/Linux
bash run_all.sh
```

This interactive script will:
- Check your environment setup
- Optionally scrape new articles
- Create/update embeddings and search index
- Launch the web interface at `http://localhost:8502`

#### Option 2: Manual Steps
```bash
# 1. Scrape articles
python scrape_articles.py

# 2. Create embeddings and search index
python embed_and_index.py

# 3. Launch web interface
python -m streamlit run app.py
```

## 📁 Project Structure

```
oncology_crawler/
├── app.py                 # Streamlit web interface
├── scrape_articles.py     # Article crawler and scraper
├── embed_and_index.py     # Embedding creation and FAISS indexing
├── semantic_search.py     # Search utilities (if present)
├── config.ini            # Configuration file
├── requirements.txt       # Python dependencies
├── run_all.sh            # Unix pipeline script
├── run_all.bat           # Windows pipeline script
├── oncology_articles.db   # SQLite database (created after scraping)
├── faiss_index.index     # FAISS vector index (created after embedding)
├── faiss_metadata.json   # Article metadata mapping
└── README.md             # This file
```

## 🔧 Configuration Options

Edit `config.ini` to customize:

```ini
[DEFAULT]
GOOGLE_API_KEY = your_gemini_api_key
DB_PATH = oncology_articles.db
FAISS_INDEX_PATH = faiss_index.index
METADATA_PATH = faiss_metadata.json
ARTICLES_URL = https://www.nature.com/subjects/oncology
```

