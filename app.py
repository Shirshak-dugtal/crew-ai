import streamlit as st
import configparser
import os
import sqlite3
import faiss
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

@st.cache_resource
def load_stuff():
    config = configparser.ConfigParser()
    config.read('config.ini')
    db_path = config['DEFAULT'].get('DB_PATH', 'oncology_articles.db')
    faiss_path = config['DEFAULT'].get('FAISS_INDEX_PATH', 'faiss_index.index')
    metadata_path = config['DEFAULT'].get('METADATA_PATH', 'faiss_metadata.json')
    
    # Load FAISS index
    index = None
    metadata = []
    try:
        index = faiss.read_index(faiss_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        st.error(f"Error loading index: {e}")
        index = None
        
    return db_path, index, metadata

def search_similar(query, index, metadata, k=3):
    if not metadata:
        return []
    
    # Create TF-IDF vectorizer from existing texts
    texts = [m.get('title', '') + " " + (m.get('abstract', '') or "") for m in metadata]
    vectorizer = TfidfVectorizer(max_features=768, stop_words='english')
    vectorizer.fit(texts)
    
    # Vectorize query
    query_vector = vectorizer.transform([query]).toarray().astype('float32')
    
    # Ensure query vector has the right dimensions
    if query_vector.shape[1] != index.d:
        # Pad or truncate to match index dimensions
        if query_vector.shape[1] < index.d:
            # Pad with zeros
            padding = np.zeros((1, index.d - query_vector.shape[1]), dtype=np.float32)
            query_vector = np.hstack([query_vector, padding])
        else:
            # Truncate
            query_vector = query_vector[:, :index.d]
    
    # Search in FAISS
    distances, indices = index.search(query_vector, k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(metadata):
            results.append({
                'title': metadata[idx].get('title', ''),
                'abstract': metadata[idx].get('abstract', ''),
                'distance': distances[0][i]
            })
    return results


def search_by_date(db_path, date_filter, k=5):
    """Search articles by date range"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    start_date, end_date = date_filter
    c.execute('''SELECT title, abstract, pub_date FROM articles 
                 WHERE pub_date BETWEEN ? AND ? 
                 ORDER BY pub_date DESC LIMIT ?''', (start_date, end_date, k))
    
    results = []
    for title, abstract, pub_date in c.fetchall():
        results.append({
            'title': title,
            'abstract': abstract or 'No abstract available',
            'distance': 0,  # No distance for date-based search
            'date': pub_date
        })
    
    conn.close()
    return results


def search_combined(query, index, metadata, date_filter, k=5):
    """Search by both content similarity and date range"""
    # First get semantic results
    semantic_results = search_similar(query, index, metadata, k*2)  # Get more to filter by date
    
    # Filter by date if provided
    if date_filter:
        start_date, end_date = date_filter
        filtered_results = []
        
        # Load date info from database
        import sqlite3
        conn = sqlite3.connect('oncology_articles.db')
        c = conn.cursor()
        c.execute('SELECT id, pub_date FROM articles WHERE pub_date BETWEEN ? AND ?', (start_date, end_date))
        valid_dates = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        
        # Filter semantic results by date
        for result in semantic_results:
            # Find the article ID that matches this title in metadata
            for i, meta in enumerate(metadata):
                if meta.get('title') == result['title']:
                    article_id = meta.get('id')
                    if article_id in valid_dates:
                        result['date'] = valid_dates[article_id]
                        filtered_results.append(result)
                        break
        
        return filtered_results[:k]
    
    return semantic_results[:k]


def main():
    st.title('🔬 Oncology Article Semantic Search')
    st.markdown("*Search through oncology research articles using semantic similarity*")
    
    db_path, faiss_index, metadata = load_stuff()
    
    if faiss_index is None:
        st.error('FAISS index not found. Run embed/index step first.')
        return
        
    st.success(f"Loaded {len(metadata)} articles for search")
    
    # Search interface with date filters
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input('🔍 Enter your research question:', placeholder="e.g., breast cancer immunotherapy")
    
    with col2:
        search_mode = st.selectbox('Search by:', ['Content', 'Date Range', 'Both'])
    
    # Date filter options
    date_filter = None
    if search_mode in ['Date Range', 'Both']:
        st.markdown("#### 📅 Date Filter")
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input('From:', value=None)
        with date_col2:
            end_date = st.date_input('To:', value=None)
        
        if start_date and end_date:
            date_filter = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    if st.button('Search') and (query or date_filter):
        k = 5  # Show top 5 most relevant articles
        with st.spinner('Searching...'):
            if search_mode == 'Date Range':
                results = search_by_date(db_path, date_filter, k)
            elif search_mode == 'Both':
                results = search_combined(query, faiss_index, metadata, date_filter, k)
            else:
                results = search_similar(query, faiss_index, metadata, k)
            
        if results:
            # Dynamic title based on search mode
            if search_mode == 'Date Range':
                search_title = f"Articles from {start_date} to {end_date}" if start_date and end_date else "Date Range Search"
            elif search_mode == 'Both':
                search_title = f"'{query}' articles from {start_date} to {end_date}" if start_date and end_date else f"'{query}' with date filter"
            else:
                search_title = f"'{query}'" if query else "Search Results"
            
            st.markdown(f"### 📋 Articles about: *{search_title}*")
            for i, result in enumerate(results, 1):
                # More detailed result display
                title = result['title']
                abstract = result['abstract'] or "No abstract available"
                
                with st.expander(f"**{title[:100]}{'...' if len(title) > 100 else ''}**", expanded=(i==1)):
                    st.markdown(f"### {title}")
                    
                    # Show publication date if available
                    if 'pub_date' in result and result['pub_date']:
                        st.markdown(f"**📅 Published:** {result['pub_date']}")
                    
                    # Abstract with better formatting
                    if abstract and len(abstract) > 50:
                        st.markdown("#### Summary")
                        st.write(abstract)
                    elif abstract:
                        st.write(abstract)
                    else:
                        st.info("No detailed abstract available for this article.")
                    
                    # Show relevance indicator only for content-based searches
                    if search_mode != 'Date Range' and 'distance' in result:
                        similarity = 1/(1+result['distance'])
                        if similarity > 0.5:
                            st.success("🎯 Highly Relevant")
                        elif similarity > 0.3:
                            st.info("📄 Relevant")
                        else:
                            st.warning("📑 Somewhat Related")
        else:
            st.warning("No articles found for your search.")
            st.info("💡 **Try different terms like:** 'immunotherapy', 'tumor markers', 'cancer treatment', or 'oncology research'")
    
    elif query:
        st.info("👆 Click the Search button to find relevant articles")
    
    # Show sample articles
    if st.checkbox("Show all articles in database"):
        st.markdown("### 📚 All Articles")
        for i, article in enumerate(metadata, 1):
            st.markdown(f"**{i}.** {article.get('title', 'No title')}")


if __name__ == '__main__':
    main()
