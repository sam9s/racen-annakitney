import trafilatura
from urllib.parse import urljoin, urlparse
import time
import re
from html import unescape
import requests


def is_printable_text(text: str, threshold: float = 0.85) -> bool:
    """Check if text is mostly printable characters."""
    if not text:
        return False
    printable_chars = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
    return (printable_chars / len(text)) >= threshold


def fetch_page_content(url: str, timeout: int = 15) -> str:
    """
    Fetch page content using requests with proper encoding handling.
    Returns decoded HTML string or empty string on failure.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        if not any(t in content_type.lower() for t in ['text/html', 'text/plain', 'application/xhtml']):
            print(f"  Skipping non-HTML content type: {content_type}")
            return ""
        
        response.encoding = response.apparent_encoding or 'utf-8'
        html = response.text
        
        if not is_printable_text(html[:1000] if len(html) > 1000 else html, threshold=0.80):
            print(f"  Content appears to be binary or encoded, skipping")
            return ""
        
        return html
        
    except requests.RequestException as e:
        print(f"  Request error: {e}")
        return ""
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return ""


def extract_text_from_html(html: str) -> str:
    """
    Fallback text extraction from raw HTML.
    Used when trafilatura can't extract content.
    """
    script_pattern = re.compile(r'<script[^>]*>.*?</script>', re.DOTALL | re.IGNORECASE)
    html = script_pattern.sub('', html)
    
    style_pattern = re.compile(r'<style[^>]*>.*?</style>', re.DOTALL | re.IGNORECASE)
    html = style_pattern.sub('', html)
    
    comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
    html = comment_pattern.sub('', html)
    
    tag_pattern = re.compile(r'<[^>]+>')
    text = tag_pattern.sub(' ', html)
    
    text = unescape(text)
    
    text = re.sub(r'\s+', ' ', text)
    
    text = text.strip()
    
    if not is_printable_text(text):
        return ""
    
    return text


def get_website_text_content(url: str) -> str:
    """
    Extract main text content from a website URL.
    Uses requests for fetching and trafilatura for extraction.
    """
    try:
        html = fetch_page_content(url)
        if not html:
            downloaded = trafilatura.fetch_url(url)
            if downloaded and is_printable_text(downloaded[:500] if len(downloaded) > 500 else downloaded):
                html = downloaded
            else:
                return ""
        
        if html:
            text = trafilatura.extract(
                html, 
                include_links=False, 
                include_images=False,
                include_tables=True,
                no_fallback=False
            )
            
            if text and len(text.strip()) > 100 and is_printable_text(text):
                return text
            
            fallback_text = extract_text_from_html(html)
            if len(fallback_text) > 200 and is_printable_text(fallback_text):
                return fallback_text
                
        return ""
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return ""


def get_all_links(url: str, base_domain: str, html: str = None) -> list:
    """
    Extract all internal links from a page.
    """
    try:
        if html is None:
            html = fetch_page_content(url)
        if not html:
            return []
        
        links = []
        link_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        matches = link_pattern.findall(html)
        
        for link in matches:
            if link.startswith('#') or link.startswith('mailto:') or link.startswith('tel:'):
                continue
            if link.startswith('javascript:'):
                continue
            
            full_url = urljoin(url, link)
            parsed = urlparse(full_url)
            
            if base_domain in parsed.netloc:
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                clean_url = clean_url.rstrip('/')
                if clean_url not in links:
                    links.append(clean_url)
        
        return links
    except Exception as e:
        print(f"Error getting links from {url}: {e}")
        return []


def clean_extracted_text(text: str) -> str:
    """Clean and normalize extracted text."""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if len(line) > 10 and is_printable_text(line):
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def scrape_joveheal_website(max_pages: int = 50) -> list:
    """
    Scrape the JoveHeal website and return a list of documents.
    Each document contains the URL and its text content.
    """
    base_url = "https://www.joveheal.com"
    base_domain = "joveheal.com"
    
    common_pages = [
        "https://www.joveheal.com",
        "https://www.joveheal.com/about",
        "https://www.joveheal.com/services",
        "https://www.joveheal.com/programs",
        "https://www.joveheal.com/coaching",
        "https://www.joveheal.com/healing",
        "https://www.joveheal.com/membership",
        "https://www.joveheal.com/workshops",
        "https://www.joveheal.com/contact",
        "https://www.joveheal.com/faq",
        "https://www.joveheal.com/pricing",
        "https://www.joveheal.com/balance-mastery",
        "https://www.joveheal.com/inner-mastery-lounge",
    ]
    
    visited = set()
    to_visit = common_pages.copy()
    documents = []
    
    print(f"Starting to scrape {base_url}...")
    
    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        
        normalized_url = url.rstrip('/')
        if normalized_url in visited:
            continue
            
        visited.add(normalized_url)
        
        print(f"Scraping ({len(visited)}/{max_pages}): {url}")
        
        content = get_website_text_content(url)
        
        if content and len(content.strip()) > 100:
            cleaned_content = clean_extracted_text(content)
            if len(cleaned_content) > 100 and is_printable_text(cleaned_content):
                documents.append({
                    "url": url,
                    "content": cleaned_content,
                    "source": "website"
                })
                print(f"  - Found {len(cleaned_content)} chars of content")
            else:
                print(f"  - Content failed quality check, skipping")
        
        new_links = get_all_links(url, base_domain)
        for link in new_links:
            normalized_link = link.rstrip('/')
            if normalized_link not in visited and link not in to_visit:
                to_visit.append(link)
        
        time.sleep(0.3)
    
    print(f"Scraping complete. Found {len(documents)} pages with content.")
    return documents


if __name__ == "__main__":
    docs = scrape_joveheal_website(max_pages=10)
    for doc in docs:
        print(f"\n--- {doc['url']} ---")
        print(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
