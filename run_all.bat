@echo off
REM Run the full oncology article pipeline on Windows

echo 🔬 Starting Oncology Article Crawler ^& Search System
echo ==================================================

REM Check if virtual environment Python exists
set PYTHON_PATH=D:\crew\.venv\Scripts\python.exe
if not exist "%PYTHON_PATH%" (
    echo ❌ Error: Virtual environment not found at %PYTHON_PATH%
    echo Please run: python -m venv .venv and install requirements
    pause
    exit /b 1
)

REM Load GOOGLE_API_KEY from config.ini
for /f "tokens=2 delims==" %%i in ('findstr "GOOGLE_API_KEY" config.ini') do set GOOGLE_API_KEY=%%i
echo 🔑 API Key configured

REM Check current database status
echo 📊 Checking current database...
for /f %%i in ('"%PYTHON_PATH%" -c "import sqlite3; conn = sqlite3.connect('oncology_articles.db'); c = conn.cursor(); c.execute('CREATE TABLE IF NOT EXISTS articles (id INTEGER PRIMARY KEY, title TEXT, authors TEXT, pub_date TEXT, abstract TEXT, url TEXT UNIQUE)'); c.execute('SELECT COUNT(*) FROM articles'); print(c.fetchone()[0]); conn.close()" 2^>nul') do set ARTICLE_COUNT=%%i
if not defined ARTICLE_COUNT set ARTICLE_COUNT=0
echo 📚 Current articles in database: %ARTICLE_COUNT%

REM Step 1: Scrape articles (optional)
echo.
set /p SCRAPE="🕷️  Do you want to scrape NEW articles? (y/N): "
if /i "%SCRAPE%"=="y" (
    echo 🕷️  Scraping new oncology articles...
    "%PYTHON_PATH%" scrape_articles.py
    if errorlevel 1 (
        echo ❌ Error during scraping
        pause
        exit /b 1
    )
    for /f %%i in ('"%PYTHON_PATH%" -c "import sqlite3; conn = sqlite3.connect('oncology_articles.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM articles'); print(c.fetchone()[0]); conn.close()"') do set NEW_COUNT=%%i
    echo ✅ Scraping complete! Total articles: !NEW_COUNT!
) else (
    echo ⏭️  Skipping scraping, using existing %ARTICLE_COUNT% articles
)

REM Step 2: Embed and index articles
echo.
echo 🧠 Creating embeddings and updating vector database...
"%PYTHON_PATH%" embed_and_index.py

if errorlevel 1 (
    echo ❌ Error creating embeddings. Check your configuration.
    pause
    exit /b 1
)
echo ✅ Vector database updated successfully!

REM Step 3: Launch Streamlit app
echo.
echo 🚀 Starting Streamlit web application...
echo 📱 The app will open at: http://localhost:8502
echo 🔍 You can search through your oncology research database!
echo.
echo Press Ctrl+C to stop the application
echo.

REM Use the virtual environment Python to run Streamlit
"%PYTHON_PATH%" -m streamlit run app.py

pause