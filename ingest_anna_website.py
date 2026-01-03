"""
Ingestion script for Anna Kitney's website content.

This script crawls annakitney.com and ingests content into the knowledge base.
Run this script to populate the chatbot with Anna's website content.

Usage:
    python ingest_anna_website.py
"""

import os
import sys
from knowledge_base import add_document_to_kb, clear_knowledge_base, get_knowledge_base_stats
from web_scraper import get_website_text_content, get_all_links, fetch_page_content


ANNA_WEBSITE_URLS = [
    "https://annakitney.com/",
    "https://annakitney.com/about/",
    "https://annakitney.com/services/",
    "https://annakitney.com/contact/",
    "https://annakitney.com/testimonials/",
]

ADDITIONAL_PAGES_TO_DISCOVER = True
BASE_DOMAIN = "annakitney.com"


def ingest_url(url: str, source_name: str = None) -> bool:
    """
    Ingest a single URL into the knowledge base.
    
    Args:
        url: The URL to scrape and ingest
        source_name: Optional custom source name
    
    Returns:
        True if successful, False otherwise
    """
    print(f"Ingesting: {url}")
    
    try:
        content = get_website_text_content(url)
        
        if not content or len(content.strip()) < 100:
            print(f"  - Skipped (no content or too short)")
            return False
        
        if source_name is None:
            path = url.replace("https://", "").replace("http://", "").replace("www.", "")
            source_name = f"website_{path.replace('/', '_').replace('.', '_').rstrip('_')}"
        
        add_document_to_kb(content, source_name)
        print(f"  - Success! ({len(content)} chars)")
        return True
        
    except Exception as e:
        print(f"  - Error: {e}")
        return False


def discover_pages(base_url: str, base_domain: str, max_pages: int = 50) -> list:
    """
    Discover all pages on the website starting from base_url.
    
    Args:
        base_url: Starting URL
        base_domain: Domain to stay within
        max_pages: Maximum number of pages to discover
    
    Returns:
        List of discovered URLs
    """
    print(f"\nDiscovering pages on {base_domain}...")
    
    discovered = set([base_url])
    to_visit = [base_url]
    visited = set()
    
    while to_visit and len(discovered) < max_pages:
        url = to_visit.pop(0)
        
        if url in visited:
            continue
        
        visited.add(url)
        
        try:
            html = fetch_page_content(url)
            if html:
                links = get_all_links(url, base_domain, html)
                for link in links:
                    if link not in discovered:
                        discovered.add(link)
                        to_visit.append(link)
        except Exception as e:
            print(f"  Error discovering from {url}: {e}")
    
    print(f"Discovered {len(discovered)} pages")
    return list(discovered)


def main():
    """Main ingestion function."""
    print("=" * 60)
    print("Anna Kitney Website Content Ingestion")
    print("=" * 60)
    
    print("\nClearing existing knowledge base...")
    clear_knowledge_base()
    
    urls_to_ingest = list(ANNA_WEBSITE_URLS)
    
    if ADDITIONAL_PAGES_TO_DISCOVER:
        discovered = discover_pages(
            "https://annakitney.com/",
            BASE_DOMAIN,
            max_pages=30
        )
        for url in discovered:
            if url not in urls_to_ingest:
                urls_to_ingest.append(url)
    
    print(f"\nIngesting {len(urls_to_ingest)} pages...")
    print("-" * 40)
    
    success_count = 0
    fail_count = 0
    
    for url in urls_to_ingest:
        if ingest_url(url):
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 60)
    print("Ingestion Complete!")
    print(f"  Successfully ingested: {success_count}")
    print(f"  Failed/Skipped: {fail_count}")
    print("=" * 60)
    
    stats = get_knowledge_base_stats()
    print(f"\nKnowledge Base Stats:")
    print(f"  Total documents: {stats.get('total_documents', 0)}")
    print(f"  Total chunks: {stats.get('total_chunks', 0)}")


if __name__ == "__main__":
    main()
