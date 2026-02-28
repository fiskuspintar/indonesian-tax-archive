#!/usr/bin/env python3
"""
Re-scrape first 500 regulations with FIXED full content scraper
This gets the COMPLETE document content by scrolling
"""

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
from datetime import datetime
import time

DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
OUTPUT_FILE = DATA_DIR / 'regulations_with_content_fixed.jsonl'
LOG_FILE = DATA_DIR / 'content_scrape_fixed.log'

# Load existing regulations
print("[INIT] Loading regulations...")
regulations = []
with open(DATA_DIR / 'regulations_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            regulations.append(json.loads(line))

LIMIT = 500  # Re-scrape first 500 with full content
print(f"[INIT] Will re-scrape first {LIMIT} regulations with FIXED scraper")


def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')


async def fetch_full_content(page, regulation_id):
    """Fetch FULL content by scrolling through the entire page"""
    url = f"https://datacenter.ortax.org/ortax/aturan/show/{regulation_id}"
    
    try:
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await asyncio.sleep(3)
        
        # Scroll and collect all content
        all_content = []
        last_height = 0
        no_change_count = 0
        
        for scroll in range(30):  # Up to 30 scrolls
            # Get visible text
            text = await page.evaluate('''() => {
                const article = document.querySelector('article, .content, [class*="content"], main');
                if (article) return article.innerText;
                return document.body.innerText;
            }''')
            
            if text and len(text) > 100:
                all_content.append(text)
            
            # Scroll down
            await page.evaluate('window.scrollBy(0, 800)')
            await asyncio.sleep(1.5)
            
            # Check if page height changed
            new_height = await page.evaluate('document.body.scrollHeight')
            if new_height == last_height:
                no_change_count += 1
                if no_change_count >= 3:  # Stop if no change for 3 scrolls
                    break
            else:
                no_change_count = 0
            last_height = new_height
        
        # Combine and deduplicate
        combined = '\n'.join(all_content)
        lines = combined.split('\n')
        seen = set()
        unique_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and stripped not in seen and len(stripped) > 20:
                seen.add(stripped)
                unique_lines.append(stripped)
        
        full_content = '\n\n'.join(unique_lines)
        
        # Limit size
        if len(full_content) > 150000:
            full_content = full_content[:150000] + "\n\n[Document continues...]"
        
        return full_content if len(full_content) > 500 else None
        
    except Exception as e:
        log(f"  Error: {e}")
        return None


async def rescrape():
    log("=" * 70)
    log("RE-SCRAPING FIRST 500 WITH FIXED FULL CONTENT")
    log("=" * 70)
    
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        for i in range(min(LIMIT, len(regulations))):
            reg = regulations[i]
            source_url = reg.get('source_url', '')
            ortax_id = source_url.split('/')[-1] if source_url else reg.get('api_id')
            
            log(f"[{i+1}/{LIMIT}] Re-scraping ID {ortax_id}...")
            
            content = await fetch_full_content(page, ortax_id)
            
            if content:
                reg['full_content'] = content
                log(f"  ✓ Content: {len(content)} chars")
            else:
                reg['full_content'] = None
                log(f"  ✗ Failed")
            
            results.append(reg)
            
            # Save every 10
            if (i + 1) % 10 == 0:
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    for r in results:
                        f.write(json.dumps(r, ensure_ascii=False) + '\n')
                log(f"[SAVED] {i+1} regulations")
            
            time.sleep(2)
        
        await browser.close()
    
    # Final save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    with_content = len([r for r in results if r.get('full_content')])
    log("=" * 70)
    log(f"COMPLETE: {with_content}/{len(results)} with full content")
    log("=" * 70)


if __name__ == '__main__':
    asyncio.run(rescrape())
