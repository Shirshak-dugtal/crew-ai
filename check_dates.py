import sqlite3
import json

# Check date information in database
conn = sqlite3.connect('oncology_articles.db')
c = conn.cursor()

# Check what date information we have
c.execute('SELECT COUNT(*) FROM articles WHERE pub_date IS NOT NULL AND pub_date != ""')
with_dates = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM articles')
total = c.fetchone()[0]

print(f'Articles with dates: {with_dates}/{total}')

# Sample of date formats
c.execute('SELECT title, pub_date FROM articles WHERE pub_date IS NOT NULL AND pub_date != "" LIMIT 5')
samples = c.fetchall()
print('\nSample dates:')
for title, date in samples:
    print(f'Date: {date} | Title: {title[:50]}...')

conn.close()