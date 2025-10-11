import os
import configparser
import sqlite3
import faiss
import numpy as np
import json
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import SQLDatabaseChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']

def main():
    config = load_config()
    os.environ['GOOGLE_API_KEY'] = config.get('GOOGLE_API_KEY', '')
    db_path = config.get('DB_PATH', 'oncology_articles.db')
    faiss_path = config.get('FAISS_INDEX_PATH', 'faiss_index.index')
    metadata_path = config.get('METADATA_PATH', 'faiss_metadata.json')
    # Load DB and FAISS
    db = SQLDatabase.from_uri(f'sqlite:///{db_path}')
    embedder = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    faiss_index = faiss.read_index(faiss_path)
    # load metadata file produced during embedding
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception:
        metadata = []

    texts = [m.get('title', '') for m in metadata]
    metadatas = [{'id': m.get('id'), 'abstract': m.get('abstract')} for m in metadata]
    vectorstore = FAISS(embedding_function=embedder, index=faiss_index, texts=texts, metadatas=metadatas)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    chain = SQLDatabaseChain(llm=llm, database=db, verbose=True)
    print("Type your query (or 'exit' to quit):")
    while True:
        query = input('> ')
        if query.lower() == 'exit':
            break
        # Semantic search
        docs = vectorstore.similarity_search(query, k=3)
        print("Top relevant articles:")
        for doc in docs:
            print(f"- {doc.page_content}")
        # Date filter via SQL
        if 'date' in query.lower() or 'published' in query.lower():
            print("Date-based results:")
            print(chain.run(query))

if __name__ == '__main__':
    main()
