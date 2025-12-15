import feedparser
import pandas as pd
from datetime import datetime
import time

def fetch_general_news():
    """
    Fetches news from multiple RSS feeds and returns a combined list of dictionaries.
    """
    rss_feeds = {
        "Investing.com": "https://www.investing.com/rss/news.rss",
        "CNBC Top News": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "WSJ Markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
    }
    
    all_news = []
    
    for source_name, url in rss_feeds.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # Top 5 from each
                # Parse date
                published = "N/A"
                if hasattr(entry, 'published'):
                    published = entry.published
                elif hasattr(entry, 'updated'):
                    published = entry.updated
                
                # Check for image (media_content or enclosures)
                image_url = None
                if 'media_content' in entry:
                     image_url = entry.media_content[0]['url']
                elif 'media_thumbnail' in entry:
                    image_url = entry.media_thumbnail[0]['url']
                
                all_news.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": source_name,
                    "published": published,
                    "summary": entry.summary if hasattr(entry, 'summary') else "",
                    "image": image_url
                })
        except Exception as e:
            print(f"Error fetching {source_name}: {e}")
            continue
            
    # Sort? RSS dates are strings, parsing them properly is better but complex due to formats.
    # We'll just return the list mixed for now, or shuffle? 
    # Usually users want 'fresh' from each source. 
    # Let's simple return the list.
    return all_news

if __name__ == "__main__":
    # Test
    news = fetch_general_news()
    print(f"Fetched {len(news)} items.")
    for n in news[:3]:
        print(n)
