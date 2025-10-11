import requests
from bs4 import BeautifulSoup
import sqlite3
import configparser
import os
from datetime import datetime
from urllib.parse import urljoin

# Load config
config = configparser.ConfigParser()
config.read('config.ini')
DB_PATH = config['DEFAULT'].get('DB_PATH', 'oncology_articles.db')
ARTICLES_URL = config['DEFAULT'].get('ARTICLES_URL', 'https://www.nature.com/subjects/oncology')

# SQLite setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        authors TEXT,
        pub_date TEXT,
        abstract TEXT,
        url TEXT UNIQUE
    )''')
    conn.commit()
    conn.close()


def save_article(title, authors, pub_date, abstract, url):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''INSERT OR IGNORE INTO articles (title, authors, pub_date, abstract, url) VALUES (?, ?, ?, ?, ?)''',
                  (title, authors, pub_date, abstract, url))
        conn.commit()
    except Exception as e:
        print(f"Error saving article: {e}")
    finally:
        conn.close()


def parse_article(article_url):
    resp = requests.get(article_url, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Enhanced title extraction
    title_meta = soup.find('meta', {'property': 'og:title'})
    title = title_meta['content'] if title_meta and title_meta.has_attr('content') else ''
    if not title:
        title_tag = soup.find('h1', class_='c-article-title')
        title = title_tag.get_text(strip=True) if title_tag else ''
    if not title and soup.title:
        title = soup.title.string
        
    # Enhanced authors extraction
    authors = []
    author_selectors = [
        'li.c-article-author-list__item',
        'a[href^="/search?author="]', 
        '.article-author',
        '.c-article-author-list__item a',
        '.c-article-author-list .c-article-author-list__link'
    ]
    for sel in author_selectors:
        found = soup.select(sel)
        if found:
            authors = [a.get_text(strip=True) for a in found]
            break
    authors = ', '.join(authors)
    
    # Enhanced publication date
    pub_date = ''
    date_selectors = ['time[datetime]', 'meta[name="dc.date"]', 'meta[name="citation_publication_date"]']
    for sel in date_selectors:
        date_elem = soup.select_one(sel)
        if date_elem:
            pub_date = date_elem.get('datetime') or date_elem.get('content', '')
            break
    
    # Enhanced abstract extraction - try multiple strategies
    abstract = ''
    abstract_selectors = [
        'div#Abs1-content',  # Nature primary
        'div.c-article-section__content',  # Nature secondary
        'div.article__abstract',  # Generic
        'div[data-component="Abstract"]',  # Nature component
        'section[data-title="Abstract"]',  # Section based
        'div.Abstract',  # Class based
        'meta[name="description"]',  # Meta fallback
        'meta[property="og:description"]'  # Open graph fallback
    ]
    
    for sel in abstract_selectors:
        if sel.startswith('meta'):
            elem = soup.find('meta', {'name': sel.split('[')[1].split('=')[1].strip('"')}) or \
                   soup.find('meta', {'property': sel.split('[')[1].split('=')[1].strip('"')})
            if elem and elem.get('content'):
                abstract = elem['content']
                break
        else:
            elem = soup.select_one(sel)
            if elem:
                abstract = elem.get_text(separator=' ', strip=True)
                break
    
    # If still no abstract, try getting the first few paragraphs
    if not abstract or len(abstract) < 50:
        paragraphs = soup.select('div.c-article-body p, .article-body p, .main-content p')
        if paragraphs:
            combined_text = ' '.join([p.get_text(strip=True) for p in paragraphs[:3]])
            if len(combined_text) > len(abstract):
                abstract = combined_text
    
    return title.strip(), authors, pub_date, abstract


def is_oncology_article(url, title, abstract):
    # Heuristics: URL contains subject path, or keywords in title/abstract
    if '/articles/' in url and 'oncology' in url:
        return True
    keywords = ['oncology', 'tumor', 'tumour', 'cancer', 'carcinoma', 'neoplasm']
    text = (title + ' ' + abstract).lower()
    return any(k in text for k in keywords)


def crawl_articles():
    all_links = set()
    
    # Start with main oncology page
    base_urls = [
        ARTICLES_URL,
        'https://www.nature.com/search?q=oncology&order=relevance',
        'https://www.nature.com/search?q=cancer&order=relevance',
        'https://www.nature.com/search?q=tumor&order=relevance'
    ]
    
    for base_url in base_urls:
        print(f'Scraping from: {base_url}')
        try:
            resp = requests.get(base_url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find article links using multiple selectors
            selectors = [
                'a.c-card__link',
                'a[href*="/articles/"]',
                'h3 a[href*="/articles/"]',
                '.c-listing__item a[href*="/articles/"]'
            ]
            
            for selector in selectors:
                for a in soup.select(selector):
                    href = a.get('href')
                    if href and '/articles/' in href:
                        full_url = urljoin(base_url, href)
                        all_links.add(full_url)
                        
        except Exception as e:
            print(f'Error scraping {base_url}: {e}')
            continue
    
    # Also try to find pagination and scrape additional pages
    try:
        resp = requests.get(ARTICLES_URL, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Look for "Load more" or pagination links
        load_more = soup.find('button', text=lambda t: t and 'load more' in t.lower())
        pagination_links = soup.select('a[href*="page="], a[href*="?p="]')
        
        for page_num in range(2, 6):  # Try pages 2-5
            page_url = f"{ARTICLES_URL}?page={page_num}"
            try:
                resp = requests.get(page_url, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for a in soup.select('a[href*="/articles/"]'):
                        href = a.get('href')
                        if href:
                            all_links.add(urljoin(page_url, href))
            except:
                break
                
    except Exception as e:
        print(f'Error finding pagination: {e}')
    
    links = list(all_links)
    print(f'Found {len(links)} total candidate article links from all sources')
    
    saved_count = 0
    skipped_count = 0
    
    for i, url in enumerate(links, 1):
        print(f'Processing article {i}/{len(links)}...', end=' ')
        try:
            title, authors, pub_date, abstract = parse_article(url)
            if title and is_oncology_article(url, title, abstract):
                save_article(title, authors, pub_date, abstract, url)
                saved_count += 1
                print(f'✓ Saved: {title[:60]}...')
            else:
                skipped_count += 1
                print(f'✗ Skipped (not oncology): {url}')
        except Exception as e:
            print(f'✗ Failed: {e}')
            continue
    
    print(f'\n📊 SCRAPING COMPLETE:')
    print(f'✅ Saved: {saved_count} oncology articles')
    print(f'❌ Skipped: {skipped_count} non-oncology articles')
    print(f'🔗 Total processed: {len(links)} links')


if __name__ == '__main__':
    init_db()
    crawl_articles()
