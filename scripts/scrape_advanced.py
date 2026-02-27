#!/usr/bin/env python3
"""
Ortax Scraper - Advanced version with scrolling and API monitoring
"""

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
from datetime import datetime
import re

BASE_URL = "https://datacenter.ortax.org/ortax/aturan/list"
OUTPUT_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
OUTPUT_FILE = OUTPUT_DIR / 'regulations.jsonl'


async def scrape_with_monitoring():
    """Scrape while monitoring network requests for API calls"""
    print("=" * 60)
    print("ORTAX SCRAPER - ADVANCED")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    api_responses = []
    regulations = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Monitor network requests
        async def handle_response(response):
            url = response.url
            if 'api' in url or 'json' in url or 'aturan' in url:
                try:
                    body = await response.text()
                    api_responses.append({
                        'url': url,
                        'status': response.status,
                        'preview': body[:2000] if body else None
                    })
                    print(f"  API Call: {url[:80]}...")
                except:
                    pass
        
        page.on('response', handle_response)
        
        print("\n[1] Loading page...")
        await page.goto(BASE_URL, wait_until='networkidle')
        
        print("[2] Waiting for initial load...")
        await asyncio.sleep(5)
        
        # Try to find and interact with filters or search
        print("[3] Looking for regulation data...")
        
        # Get all text content
        body_text = await page.inner_text('body')
        
        # Look for regulation patterns
        print("\n[4] Analyzing page content...")
        
        # Try to scroll down to trigger lazy loading
        print("[5] Scrolling to load more content...")
        for i in range(5):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)
            print(f"  Scroll {i+1}/5")
        
        # Wait a bit more for any lazy-loaded content
        await asyncio.sleep(3)
        
        # Now try to extract data
        print("\n[6] Extracting visible regulations...")
        
        # Look for elements that might contain regulation data
        # Common patterns in modern React apps
        selectors = [
            '[data-testid]',
            '[class*="card"]',
            '[class*="item"]',
            '[class*="row"]',
            'article',
            'li',
        ]
        
        all_elements = []
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                all_elements.extend(elements)
        
        print(f"  Found {len(all_elements)} potential elements")
        
        # Extract text from each element
        for i, elem in enumerate(all_elements[:100]):  # Limit to first 100
            try:
                text = await elem.inner_text()
                if text and len(text) > 30:  # Filter out short/empty text
                    # Check if it looks like a regulation
                    if any(keyword in text.upper() for keyword in ['UU', 'PERATURAN', 'PP', 'PMK', 'TAHUN', 'NOMOR']):
                        regulations.append({
                            'id': len(regulations) + 1,
                            'text': text[:500],
                            'scraped_at': datetime.now().isoformat(),
                        })
            except:
                pass
        
        # Save page screenshot for debugging
        await page.screenshot(path=str(OUTPUT_DIR / 'screenshot.png'))
        print(f"  Screenshot saved: {OUTPUT_DIR / 'screenshot.png'}")
        
        await browser.close()
    
    # Save API responses for analysis
    with open(OUTPUT_DIR / 'api_responses.json', 'w') as f:
        json.dump(api_responses, f, indent=2, default=str)
    
    # Save regulations
    with open(OUTPUT_FILE, 'w') as f:
        for reg in regulations:
            f.write(json.dumps(reg, ensure_ascii=False) + '\n')
    
    print(f"\n{'='*60}")
    print(f"Found {len(regulations)} potential regulations")
    print(f"Captured {len(api_responses)} API responses")
    print(f"{'='*60}")
    
    return regulations, api_responses


if __name__ == '__main__':
    regs, apis = asyncio.run(scrape_with_monitoring())
