import requests
from bs4 import BeautifulSoup


def web_search(query, num_results=2):
    """Perform a web search and return summarized results"""
    print(f"🔍 Searching web for: {query}")
    
    try:
        # Use DuckDuckGo search (no API key required)
        search_url = f"https://duckduckgo.com/html/?q={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"🌐 Requesting: {search_url}")
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"📥 Response status: {response.status_code}, length: {len(response.content)}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Try multiple selectors for DuckDuckGo results
        result_selectors = [
            'a[class*="result"]',  # More flexible class matching
            '.result__a',          # Original selector
            'h2 a',               # Generic result links
            '.web-result__title-link',  # Alternative DDG format
            '.result-title a',     # Another possible format
            'a[data-testid*="result"]'  # Test ID approach
        ]
        
        found_results = []
        for selector in result_selectors:
            found_results = soup.select(selector)[:num_results]
            if found_results:
                print(f"✅ Found {len(found_results)} results using selector: {selector}")
                break
            else:
                print(f"❌ No results with selector: {selector}")
        
        if not found_results:
            print("❌ No results found with any selector. HTML preview:")
            print(str(soup)[:500] + "...")
            # Try to find any links that might be results
            all_links = soup.find_all('a', href=True)
            print(f"Found {len(all_links)} total links")
            return [{"title": "Search Failed", "snippet": "No search results found - DuckDuckGo may be blocking requests or changed structure", "url": "", "content": ""}]
        
        for result in found_results:
            title = result.get_text(strip=True)
            url = result.get('href', '')
            
            # Handle relative URLs
            if url.startswith('/'):
                url = f"https://duckduckgo.com{url}"
            elif url.startswith('//'):
                url = f"https:{url}"
            
            # Skip DuckDuckGo internal links
            if 'duckduckgo.com' in url and '/y.js' in url:
                continue
                
            # Get snippet - try multiple approaches
            snippet = ""
            try:
                snippet_elem = result.find_next('a', class_='result__snippet')
                if not snippet_elem:
                    # Try finding nearby text
                    parent = result.find_parent()
                    if parent:
                        snippet_elem = parent.find_next('span') or parent.find_next('p')
                
                if snippet_elem:
                    snippet = snippet_elem.get_text(strip=True)
            except:
                snippet = ""
            
            if title and url and len(url) > 10:  # Basic URL validation
                print(f"📄 Found result: {title}...")
                # Fetch actual content from the page
                content = fetch_page_content(url)
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'content': content
                })
        
        print(f"✅ Found {len(results)} search results with content")
        return results
        
    except Exception as e:
        print(f"❌ Web search failed: {e}")
        return [{"title": "Search Error", "snippet": f"Unable to search the web: {str(e)}", "url": "", "content": ""}]

def fetch_page_content(url, max_length=3000):
    """Fetch and extract text content from a webpage"""
    try:
        print(f"📄 Fetching content from: {url[:50]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script, style, and navigation elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        # Try to find main content areas first
        content_selectors = [
            'main', 'article', '.content', '.main-content', 
            '.weather-info', '.current-weather', '.weather-details',
            '.temperature', '.conditions', '.forecast'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Get text content
        text = main_content.get_text(separator=' ', strip=True)
        
        # Clean up whitespace and common website artifacts
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 3:  # Skip very short lines
                # Skip common website navigation text
                skip_phrases = ['cookie', 'privacy policy', 'terms of service', 
                                'subscribe', 'newsletter', 'advertisement']
                if not any(phrase in line.lower() for phrase in skip_phrases):
                    cleaned_lines.append(line)
        
        text = ' '.join(cleaned_lines)
        
        # Truncate if too long but try to keep complete sentences
        if len(text) > max_length:
            text = text[:max_length]
            # Try to end at a sentence boundary
            last_period = text.rfind('.')
            if last_period > max_length * 0.8:  # If we're close to the end
                text = text[:last_period + 1]
            else:
                text = text + "..."
        
        return text
        
    except Exception as e:
        print(f"⚠️  Failed to fetch content from {url}: {e}")
        return "Content could not be retrieved from this page."


def get_apnews_articles(max_articles=10):
    """Scrape front page articles from AP News"""
    print("📰 Fetching AP News front page articles...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Get the AP News homepage
        response = requests.get("https://apnews.com/", headers=headers, timeout=15)
        response.raise_for_status()
        print(response.content)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Find article links and titles from PagePromo-title elements
        article_elements = soup.select('h2.PagePromo-title a.Link')
        
        print(f"📄 Found {len(article_elements)} potential articles")
        
        for i, article_link in enumerate(article_elements[:max_articles]):
            try:
                # Extract title from the span inside the link
                title_span = article_link.select_one('span.PagePromoContentIcons-text')
                if not title_span:
                    # Fallback: get text content directly
                    title = article_link.get_text(strip=True)
                else:
                    title = title_span.get_text(strip=True)
                
                # Get the article URL
                url = article_link.get('href', '')
                
                # Handle relative URLs
                if url.startswith('/'):
                    url = f"https://apnews.com{url}"
                elif not url.startswith('http'):
                    continue  # Skip invalid URLs
                
                # Skip if we don't have both title and URL
                if not title or not url:
                    continue
                
                print(f"📖 Fetching article {i+1}/{max_articles}: {title[:60]}...")
                
                # Fetch the full article content
                article_content = fetch_apnews_article_content(url, headers)
                
                articles.append({
                    'title': title,
                    'url': url,
                    'content': article_content
                })
                
            except Exception as e:
                print(f"⚠️  Error processing article {i+1}: {e}")
                continue
        
        print(f"✅ Successfully fetched {len(articles)} AP News articles")
        return articles
        
    except Exception as e:
        print(f"❌ Failed to fetch AP News articles: {e}")
        return []


def fetch_apnews_article_content(url, headers):
    """Fetch the full text content from an AP News article page"""
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the main article content
        article_body = soup.select_one('.RichTextStoryBody.RichTextBody')
        
        if not article_body:
            # Fallback selectors if the main one doesn't work
            fallback_selectors = [
                '.RichTextStoryBody',
                '.RichTextBody',
                '[data-module="ArticleBody"]',
                '.Article-content',
                'div[data-key="article-body"]'
            ]
            
            for selector in fallback_selectors:
                article_body = soup.select_one(selector)
                if article_body:
                    break
        
        if not article_body:
            print("⚠️  Could not find article content with any selector")
            return "Article content could not be extracted."
        
        # Remove unwanted elements within the article
        for element in article_body.find_all(['script', 'style', 'aside', '.ad', '.advertisement']):
            element.decompose()
        
        # Get the text content
        paragraphs = article_body.find_all(['p', 'div'])
        text_content = []
        
        for para in paragraphs:
            text = para.get_text(strip=True)
            if text and len(text) > 10:  # Filter out very short fragments
                text_content.append(text)
        
        # Join paragraphs with line breaks
        article_text = '\n\n'.join(text_content)
        
        # Clean up extra whitespace
        article_text = ' '.join(article_text.split())
        
        return article_text if article_text else "Article content could not be extracted."
        
    except Exception as e:
        print(f"⚠️  Failed to fetch article content from {url}: {e}")
        return "Failed to retrieve article content."
