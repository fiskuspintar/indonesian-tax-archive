#!/usr/bin/env python3
"""
Playwright-based scraper for JavaScript-rendered pages.
This handles Next.js apps that load content dynamically.
"""

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
from datetime import datetime

BASE_URL = "https://datacenter.ortax.org/ortax/aturan/list"
OUTPUT_FILE = Path('../data/raw/regulations_playwright.jsonl')

async def scrape_ortax():
    """Scrape Ortax using Playwright for JavaScript rendering"""
    
    print("Starting Playwright scraper...")
    print(f"Target: {BASE_URL}")
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Enable request interception to capture API calls
        api_responses = []
        
        async def handle_response(response):
            """Capture API responses"""
            if 'api' in response.url or 'json' in response.url:
                try:
                    body = await response.body()
                    api_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'body_preview': body[:500] if body else None
                    })
                except:
                    pass
        
        page.on('response', handle_response)
        
        print("\nNavigating to page...")
        await page.goto(BASE_URL, wait_until='networkidle')
        
        # Wait for content to load
        print("Waiting for content to load...")
        await asyncio.sleep(5)
        
        # Try to find regulation data
        print("\nAnalyzing page content...")
        
        # Check for table rows
        rows = await page.query_selector_all('table tr, [class*="row"], [class*="item"]')
        print(f"Found {len(rows)} potential row elements")
        
        # Check for links
        links = await page.query_selector_all('a')
        print(f"Found {len(links)} links")
        
        # Try to extract visible text
        content = await page.content()
        
        # Look for regulation patterns
        regulation_patterns = [
            'UU', 'PP', 'Peraturan', 'Keputusan', 'PMK', 'KMK', 
            'Perpres', 'PERPU', 'Tap MPR', 'UUD'
        ]
        
        found_patterns = []
        for pattern in regulation_patterns:
            if pattern in content:
                found_patterns.append(pattern)
        
        print(f"\nFound regulation patterns: {found_patterns}")
        
        # Try to scroll and load more content
        print("\nScrolling to load more content...")
        for _ in range(3):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)
        
        # Extract all text content
        page_text = await page.evaluate('() => document.body.innerText')
        
        # Save analysis
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'url': BASE_URL,
            'page_title': await page.title(),
            'row_count': len(rows),
            'link_count': len(links),
            'patterns_found': found_patterns,
            'api_responses': api_responses[:10],  # First 10 API responses
            'text_sample': page_text[:2000] if page_text else None
        }
        
        with open('../data/playwright_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print("\nSaved analysis to: data/playwright_analysis.json")
        
        # Try to extract regulation data if available
        regulations = []
        
        # Look for elements containing regulation info
        elements = await page.query_selector_all('text=/\\d{4}/')  # Years
        print(f"\nFound {len(elements)} elements with years")
        
        await browser.close()
        
        print("\nPlaywright analysis complete!")
        return analysis

if __name__ == '__main__':
    result = asyncio.run(scrape_ortax())
    print(json.dumps(result, indent=2, default=str))
