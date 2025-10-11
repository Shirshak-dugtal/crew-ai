import sqlite3
import configparser
import os
import faiss
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer

# Load config
config = configparser.ConfigParser()
config.read('config.ini')
DB_PATH = config['DEFAULT'].get('DB_PATH', 'oncology_articles.db')
FAISS_INDEX_PATH = config['DEFAULT'].get('FAISS_INDEX_PATH', 'faiss_index.index')
METADATA_PATH = config['DEFAULT'].get('METADATA_PATH', 'faiss_metadata.json')


def get_articles():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, title, abstract FROM articles')
    rows = c.fetchall()
    conn.close()
    return rows


def main():
    articles = get_articles()
    if not articles:
        print('No articles found.')
        return
    
    print(f"Found {len(articles)} articles to embed...")
    
    # Use TF-IDF as a fallback embedding method (demo purposes)
    texts = [title + " " + (abstract or "") for _, title, abstract in articles]
    ids = [i for i, _, _ in articles]
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(max_features=768, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    vectors = tfidf_matrix.toarray().astype('float32')
    
    print(f"Created {vectors.shape[0]} vectors of dimension {vectors.shape[1]}")
    
    # Create FAISS index
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    faiss.write_index(index, FAISS_INDEX_PATH)
    
    # Save metadata mapping
    metadata = [{'id': i, 'title': t, 'abstract': a} for i, t, a in articles]
    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False)
    
    print(f"Embedded {len(texts)} articles using TF-IDF and saved FAISS index and metadata.")
    print("Note: Using TF-IDF embeddings as demo (Gemini quota exceeded)")


if __name__ == '__main__':
    main()
