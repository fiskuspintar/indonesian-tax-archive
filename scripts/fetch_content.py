#!/usr/bin/env python3
"""
Fetch full regulation content from Ortax detail pages
This enriches our existing data with full document text
"""

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
from datetime import datetime
import time

DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
OUTPUT_FILE = DATA_DIR / 'regulations_with_content.jsonl'

# Load existing regulations
print("Loading existing regulations...")
regulations = []
with open(DATA_DIR / 'regulations_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            regulations.append(json.loads(line))

print(f"Loaded {len(regulations)} regulations")


async def fetch_regulation_content(page, regulation_id):
    """Fetch content for a single regulation"""
    url = f"https://datacenter.ortax.org/ortax/aturan/show/{regulation_id}"
    
    try:
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(2)  # Wait for content to load
        
        # Try multiple selectors to find content
        content_selectors = [
            '[class*="content"]',
            '[class*="detail"]',
            'article',
            'main',
            '.prose',
            '[data-testid*="content"]',
        ]
        
        content = None
        for selector in content_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text) > 100:  # Meaningful content
                        content = text
                        break
            except:
                continue
        
        # If no content found, get body text
        if not content:
            body = await page.query_selector('body')
            if body:
                content = await body.inner_text()
        
        return content[:10000] if content else None  # Limit to 10k chars
        
    except Exception as e:
        print(f"Error fetching {regulation_id}: {e}")
        return None


async def enrich_regulations():
    """Fetch content for all regulations"""
    print("\nStarting content enrichment...")
    
    enriched = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Process first 100 regulations as a test
        # (Full scrape would take too long - ~20k regulations * 3 seconds = 16+ hours)
        limit = min(100, len(regulations))
        
        print(f"Fetching content for first {limit} regulations...")
        
        for i, reg in enumerate(regulations[:limit]):
            reg_id = reg.get('id')
            print(f"[{i+1}/{limit}] Fetching content for regulation {reg_id}...", end=' ')
            
            content = await fetch_regulation_content(page, reg_id)
            
            if content:
                reg['full_content'] = content
                print(f"✓ ({len(content)} chars)")
            else:
                print("✗ (no content)")
            
            enriched.append(reg)
            
            # Be nice to the server
            time.sleep(1)
            
            # Save progress every 10
            if (i + 1) % 10 == 0:
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    for r in enriched:
                        f.write(json.dumps(r, ensure_ascii=False) + '\n')
                print(f"  [Saved progress: {len(enriched)} regulations]")
        
        await browser.close()
    
    # Final save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for r in enriched:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    print(f"\n{'='*60}")
    print(f"ENRICHMENT COMPLETE")
    print(f"Total with content: {len([r for r in enriched if r.get('full_content')])}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == '__main__':
    asyncio.run(enrich_regulations())
