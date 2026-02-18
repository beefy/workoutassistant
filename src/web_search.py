import requests
from bs4 import BeautifulSoup


def web_search(self, query, num_results=2):
    """Perform a web search and return summarized results"""
    print(f"🔍 Searching web for: {query}")
    
    try:
        # Use DuckDuckGo search (no API key required)
        search_url = f"https://duckduckgo.com/html/?q={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Find search results
        for result in soup.find_all('a', class_='result__a')[:num_results]:
            title = result.get_text(strip=True)
            url = result.get('href')
            
            # Get snippet from result
            snippet_elem = result.find_next('a', class_='result__snippet')
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            if title and url:
                # Fetch actual content from the page
                content = self.fetch_page_content(url)
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

def fetch_page_content(self, url, max_length=1500):
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
