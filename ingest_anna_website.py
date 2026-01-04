"""
Ingestion script for Anna Kitney's website content.

This script crawls annakitney.com and ingests content into the knowledge base.
Run this script to populate the chatbot with Anna's website content.

Usage:
    python3 ingest_anna_website.py
"""

import os
import sys
from knowledge_base import (
    get_or_create_collection,
    split_text_into_chunks,
    clear_knowledge_base,
    get_knowledge_base_stats,
    is_valid_text_content
)
from web_scraper import get_website_text_content, get_all_links, fetch_page_content


ANNA_MAIN_PAGES = [
    "https://www.annakitney.com/",
    "https://www.annakitney.com/work-with-me/",
    "https://www.annakitney.com/contact/",
    "https://www.annakitney.com/clarity-call/",
    "https://www.annakitney.com/privacy-policy/",
    "https://www.annakitney.com/terms-and-conditions/",
]

ANNA_PROGRAM_PAGES = [
    "https://www.annakitney.com/all-the-things/",
    "https://www.annakitney.com/the-ascend-collective/",
    "https://www.annakitney.com/soul-align-business-course/",
    "https://www.annakitney.com/vip-day/",
    "https://www.annakitney.com/elite-private-advisory/",
    "https://www.annakitney.com/soulalign-heal/",
    "https://www.annakitney.com/soulalign-manifestation-mastery/",
    "https://www.annakitney.com/soulalign-money/",
    "https://www.annakitney.com/divine-abundance-codes/",
    "https://www.annakitney.com/more-love-and-money-intensive/",
    "https://www.annakitney.com/avatar-unleash-your-divine-brilliance/",
    "https://www.annakitney.com/launch-and-grow-live/",
    "https://www.annakitney.com/get-clients-fast-masterclass/",
]

ANNA_PORTAL_PAGES = [
    "https://www.annakitneyportal.com/soulaligncoach",
]

ANNA_BLOG_PAGES = [
    "https://www.annakitney.com/blog/",
    "https://www.annakitney.com/making-the-impossible-possible/",
    "https://www.annakitney.com/is-nervous-system-regulation-treating-a-symptom-rather-than-the-cause/",
    "https://www.annakitney.com/the-evolution-of-consciousness-into-the-god-zone-how-to-escape-the-matrix-and-manifest-as-source/",
    "https://www.annakitney.com/escaping-the-matrix-and-accessing-the-god-zone-a-new-paradigm-for-manifestation/",
    "https://www.annakitney.com/the-root-of-feast-famine-cycles-in-your-business/",
    "https://www.annakitney.com/how-to-coach-anyone-on-anything/",
    "https://www.annakitney.com/the-one-universal-law-that-will-amplify-your-manifestations/",
    "https://www.annakitney.com/from-entrepreneur-to-ceo-evolving-the-strategy-mindset-to-achieve-50k-months-and-beyond/",
    "https://www.annakitney.com/from-entrepreneur-to-enterprise-evolving-the-mindset-to-achieve-50k-months-and-beyond/",
    "https://www.annakitney.com/the-art-of-doing-less-to-achieve-more/",
    "https://www.annakitney.com/the-manifestation-secret-no-one-teaches/",
    "https://www.annakitney.com/how-we-did-1million-in-pandemic/",
]

ADDITIONAL_PAGES_TO_DISCOVER = True
BASE_DOMAIN = "annakitney.com"
MAX_DISCOVERY_PAGES = 100


def get_content_type(url: str) -> str:
    """Determine content type based on URL path for metadata tagging."""
    url_lower = url.lower()
    
    if any(prog in url_lower for prog in [
        'elite-private-advisory', 'ascend-collective', 'vip-day',
        'soulalign-heal', 'soulalign-manifestation', 'soulalign-money',
        'divine-abundance', 'avatar', 'soul-align-business',
        'launch-and-grow', 'get-clients-fast', 'more-love-and-money',
        'all-the-things', 'work-with-me'
    ]):
        return "program"
    elif '/blog/' in url_lower or any(x in url_lower for x in [
        'making-the-impossible', 'nervous-system', 'evolution-of-consciousness',
        'escaping-the-matrix', 'feast-famine', 'coach-anyone', 'universal-law',
        'entrepreneur-to-ceo', 'art-of-doing-less', 'manifestation-secret', '1million'
    ]):
        return "blog"
    elif '/event' in url_lower or '/2024' in url_lower or '/2025' in url_lower or '/2026' in url_lower:
        return "event"
    elif 'contact' in url_lower or 'clarity-call' in url_lower:
        return "contact"
    elif 'about' in url_lower or 'testimonial' in url_lower:
        return "about"
    else:
        return "website"


def ingest_url(url: str, collection, source_name: str = None) -> int:
    """
    Ingest a single URL into the knowledge base.
    
    Args:
        url: The URL to scrape and ingest
        collection: ChromaDB collection
        source_name: Optional custom source name
    
    Returns:
        Number of chunks added
    """
    url_lower = url.lower()
    if '/event' in url_lower or '/events/' in url_lower:
        print(f"Skipping event page: {url}")
        return 0
    
    print(f"Ingesting: {url}")
    
    try:
        content = get_website_text_content(url)
        
        if not content or len(content.strip()) < 100:
            print(f"  - Skipped (no content or too short)")
            return 0
        
        if not is_valid_text_content(content):
            print(f"  - Skipped (invalid content)")
            return 0
        
        if source_name is None:
            path = url.replace("https://", "").replace("http://", "").replace("www.", "")
            source_name = f"website_{path.replace('/', '_').replace('.', '_').rstrip('_')}"
        
        content_type = get_content_type(url)
        
        chunks = split_text_into_chunks(content, url)
        chunks_added = 0
        
        for chunk in chunks:
            if not is_valid_text_content(chunk["content"], min_printable_ratio=0.90):
                continue
            try:
                collection.upsert(
                    ids=[chunk["id"]],
                    documents=[chunk["content"]],
                    metadatas=[{
                        "source": url,
                        "type": content_type,
                        "chunk_index": chunk["chunk_index"]
                    }]
                )
                chunks_added += 1
            except Exception as e:
                print(f"  - Chunk error: {e}")
        
        print(f"  - Success! ({len(content)} chars, {chunks_added} chunks, type: {content_type})")
        return chunks_added
        
    except Exception as e:
        print(f"  - Error: {e}")
        return 0


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
                        skip_patterns = [
                            '/wp-content/', '/wp-admin/', '/wp-includes/',
                            '.jpg', '.png', '.gif', '.pdf', '.css', '.js',
                            '#', '?', 'facebook.com', 'instagram.com', 
                            'youtube.com', 'linkedin.com', 'twitter.com',
                            '/cart/', '/checkout/', '/my-account/',
                            '/events/', '/event/', '/2024', '/2025', '/2026',
                        ]
                        should_skip = any(pattern in link.lower() for pattern in skip_patterns)
                        if not should_skip:
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
    
    collection = get_or_create_collection()
    
    all_urls = set()
    
    print("\n--- Adding Main Pages ---")
    for url in ANNA_MAIN_PAGES:
        all_urls.add(url)
    
    print("\n--- Adding Program Pages ---")
    for url in ANNA_PROGRAM_PAGES:
        all_urls.add(url)
    
    print("\n--- Adding Portal Pages ---")
    for url in ANNA_PORTAL_PAGES:
        all_urls.add(url)
    
    print("\n--- Adding Blog Pages ---")
    for url in ANNA_BLOG_PAGES:
        all_urls.add(url)
    
    if ADDITIONAL_PAGES_TO_DISCOVER:
        print("\n--- Discovering Additional Pages ---")
        discovered = discover_pages(
            "https://www.annakitney.com/",
            BASE_DOMAIN,
            max_pages=MAX_DISCOVERY_PAGES
        )
        for url in discovered:
            all_urls.add(url)
        
        discovered_blog = discover_pages(
            "https://www.annakitney.com/blog/",
            BASE_DOMAIN,
            max_pages=30
        )
        for url in discovered_blog:
            all_urls.add(url)
    
    urls_to_ingest = sorted(list(all_urls))
    
    print(f"\n{'=' * 60}")
    print(f"Total pages to ingest: {len(urls_to_ingest)}")
    print(f"{'=' * 60}")
    
    total_chunks = 0
    success_count = 0
    error_count = 0
    
    for i, url in enumerate(urls_to_ingest, 1):
        print(f"\n[{i}/{len(urls_to_ingest)}] ", end="")
        chunks = ingest_url(url, collection)
        if chunks > 0:
            success_count += 1
            total_chunks += chunks
        else:
            error_count += 1
    
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Successfully ingested: {success_count} pages")
    print(f"Failed/Skipped: {error_count} pages")
    print(f"Total chunks added: {total_chunks}")
    
    stats = get_knowledge_base_stats()
    print(f"\nKnowledge Base Stats:")
    print(f"  - Total chunks: {stats.get('total_chunks', 'N/A')}")
    print(f"  - Collection: {stats.get('collection_name', 'N/A')}")
    
    return success_count > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
