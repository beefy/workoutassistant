import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


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
    """Scrape front page articles from AP News using Selenium for dynamic content"""
    print("📰 Fetching AP News front page articles with headless browser...")
    
    driver = None
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Initialize the Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Get the AP News homepage and wait for content to load
        driver.get("https://apnews.com/")
        
        # Wait for the page to load and articles to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2.PagePromo-title, .PageList-items-item, .CardHeadline"))
        )
        
        # Give it a moment for dynamic content to fully load
        time.sleep(3)
        
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        articles = []
        
        # Try multiple selectors for article links
        article_selectors = [
            'h2.PagePromo-title a.Link',
            'h2.PagePromo-title a',
            '.CardHeadline a',
            '.PageList-items-item a',
            'h3 a[href*="/article/"]',
            'h2 a[href*="/article/"]',
            'a[href*="/article/"]'
        ]
        
        article_elements = []
        for selector in article_selectors:
            article_elements = soup.select(selector)
            if article_elements:
                print(f"📄 Found {len(article_elements)} articles using selector: {selector}")
                break
        
        if not article_elements:
            print("❌ No article links found with any selector")
            return []
        
        # Process articles
        processed_urls = set()  # Avoid duplicates
        
        for i, article_link in enumerate(article_elements[:max_articles * 2]):  # Get more to account for filtering
            try:
                if len(articles) >= max_articles:
                    break
                    
                # Extract title
                title_span = article_link.select_one('span.PagePromoContentIcons-text')
                if title_span:
                    title = title_span.get_text(strip=True)
                else:
                    title = article_link.get_text(strip=True)
                
                if not title or len(title) < 10:
                    continue
                
                # Get the article URL
                url = article_link.get('href', '')
                
                # Handle relative URLs
                if url.startswith('/'):
                    url = f"https://apnews.com{url}"
                elif not url.startswith('http'):
                    continue
                
                # Skip duplicates and non-article URLs
                if url in processed_urls or '/article/' not in url:
                    continue
                
                processed_urls.add(url)
                
                print(f"📖 Fetching article {len(articles)+1}/{max_articles}: {title[:60]}...")
                
                # Fetch the full article content
                article_content = fetch_apnews_article_content_selenium(url)
                
                if article_content and "could not be extracted" not in article_content.lower():
                    articles.append({
                        'title': title,
                        'url': url,
                        'content': article_content
                    })
                
            except Exception as e:
                print(f"⚠️  Error processing article: {e}")
                continue
        
        print(f"✅ Successfully fetched {len(articles)} AP News articles")
        return articles
        
    except Exception as e:
        print(f"❌ Failed to fetch AP News articles: {e}")
        return []
    
    finally:
        if driver:
            driver.quit()


def fetch_apnews_article_content_selenium(url):
    """Fetch the full text content from an AP News article page using Selenium"""
    driver = None
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Initialize the Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for article content to load
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".RichTextStoryBody.RichTextBody")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".RichTextStoryBody")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-module='ArticleBody']")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
            )
        )
        
        # Give content time to fully load
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for the main article content with multiple selectors
        content_selectors = [
            '.RichTextStoryBody.RichTextBody',
            '.RichTextStoryBody',
            '.RichTextBody',
            '[data-module="ArticleBody"]',
            '.Article-content',
            'div[data-key="article-body"]',
            'article',
            '.story-body',
            '.article-body'
        ]
        
        article_body = None
        for selector in content_selectors:
            article_body = soup.select_one(selector)
            if article_body:
                break
        
        if not article_body:
            print("⚠️  Could not find article content with any selector")
            return "Article content could not be extracted."
        
        # Remove unwanted elements
        for element in article_body.find_all(['script', 'style', 'aside', 'nav', 'footer', '.ad', '.advertisement', '.related-articles']):
            element.decompose()
        
        # Get text content from paragraphs and divs
        content_elements = article_body.find_all(['p', 'div', 'h1', 'h2', 'h3'])
        text_content = []
        
        for element in content_elements:
            text = element.get_text(strip=True)
            if text and len(text) > 15:  # Filter out very short fragments
                # Skip common boilerplate text
                skip_phrases = [
                    'subscribe', 'newsletter', 'cookie', 'privacy policy',
                    'advertisement', 'related articles', 'share this',
                    'follow us', 'download our app'
                ]
                if not any(phrase in text.lower() for phrase in skip_phrases):
                    text_content.append(text)
        
        # Join with double line breaks for readability
        article_text = '\n\n'.join(text_content)
        
        # Clean up extra whitespace while preserving paragraph structure
        lines = article_text.split('\n')
        cleaned_lines = [' '.join(line.split()) for line in lines if line.strip()]
        article_text = '\n'.join(cleaned_lines)
        
        return article_text if article_text and len(article_text) > 50 else "Article content could not be extracted."
        
    except Exception as e:
        print(f"⚠️  Failed to fetch article content from {url}: {e}")
        return "Failed to retrieve article content."
    
    finally:
        if driver:
            driver.quit()


def fetch_apnews_article_content(url, headers):
    """Legacy function - falls back to Selenium version"""
    return fetch_apnews_article_content_selenium(url)
