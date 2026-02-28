#!/usr/bin/env python3
"""
FIXED CONTENT SCRAPER - Gets FULL document content by scrolling
"""

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
from datetime import datetime
import time

DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
OUTPUT_FILE = DATA_DIR / 'regulations_with_content.jsonl'
PROGRESS_FILE = DATA_DIR / 'content_scrape_progress.json'
LOG_FILE = DATA_DIR / 'content_scrape.log'

# Load existing regulations
print("[INIT] Loading existing regulations...")
regulations = []
with open(DATA_DIR / 'regulations_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            regulations.append(json.loads(line))

TOTAL = len(regulations)
print(f"[INIT] Loaded {TOTAL} regulations")


def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')


async def fetch_full_content(page, regulation_id, retries=3):
    """Fetch FULL content by scrolling through the entire page"""
    url = f"https://datacenter.ortax.org/ortax/aturan/show/{regulation_id}"
    
    for attempt in range(retries):
        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(3)  # Wait for initial load
            
            # Scroll down multiple times to load all content
            all_text_parts = []
            last_height = 0
            scroll_attempts = 0
            max_scrolls = 20  # Maximum scroll attempts
            
            while scroll_attempts < max_scrolls:
                # Get current page text
                current_text = await page.evaluate('() => document.body.innerText')
                
                # Extract meaningful content (filter out navigation)
                lines = [l.strip() for l in current_text.split('\n') if l.strip()]
                content_lines = [l for l in lines if len(l) > 50]  # Only substantial lines
                
                if content_lines:
                    current_content = '\n'.join(content_lines)
                    if current_content not in all_text_parts:
                        all_text_parts.append(current_content)
                
                # Scroll down
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)
                
                # Check if we've reached the bottom
                new_height = await page.evaluate('document.body.scrollHeight')
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_attempts += 1
            
            # Combine all parts and remove duplicates
            full_content = '\n\n'.join(all_text_parts)
            
            # Clean up - remove excessive whitespace
            full_content = '\n'.join(line for line in full_content.split('\n') if line.strip())
            
            # Limit to reasonable size (100k chars)
            if len(full_content) > 100000:
                full_content = full_content[:100000] + "\n\n[Content truncated due to length...]"
            
            return full_content if len(full_content) > 500 else None
            
        except Exception as e:
            if attempt < retries - 1:
                log(f"  Retry {attempt + 1} for ID {regulation_id}: {e}")
                await asyncio.sleep(5)
            else:
                log(f"  Failed after {retries} attempts for ID {regulation_id}: {e}")
                return None
    
    return None


async def scrape_all_content():
    log("=" * 70)
    log("FULL CONTENT SCRAPER - SCROLLING VERSION - STARTING")
    log(f"Total regulations to process: {TOTAL}")
    log("=" * 70)
    
    # Check for existing progress
    start_index = 0
    enriched = []
    
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            start_index = progress.get('last_index', 0)
            log(f"[RESUME] Resuming from regulation {start_index}")
    
    if OUTPUT_FILE.exists() and start_index > 0:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    enriched.append(json.loads(line))
        log(f"[RESUME] Loaded {len(enriched)} already processed")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        log("[INIT] Browser started, beginning full content scrape...")
        
        for i in range(start_index, TOTAL):
            reg = regulations[i]
            source_url = reg.get('source_url', '')
            ortax_id = source_url.split('/')[-1] if source_url else reg.get('api_id')
            
            log(f"[{i+1}/{TOTAL}] Processing regulation ID {ortax_id}...")
            
            content = await fetch_full_content(page, ortax_id)
            
            if content:
                reg['full_content'] = content
                log(f"  ✓ Full content fetched: {len(content)} characters")
            else:
                reg['full_content'] = None
                log(f"  ✗ No content found")
            
            enriched.append(reg)
            
            # Save progress every 10 regulations
            if (i + 1) % 10 == 0:
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    for r in enriched:
                        f.write(json.dumps(r, ensure_ascii=False) + '\n')
                
                with open(PROGRESS_FILE, 'w') as f:
                    json.dump({
                        'last_index': i + 1,
                        'total': TOTAL,
                        'with_content': len([r for r in enriched if r.get('full_content')]),
                        'timestamp': datetime.now().isoformat(),
                    }, f, indent=2)
                
                with_content = len([r for r in enriched if r.get('full_content')])
                percentage = ((i + 1) / TOTAL) * 100
                log(f"[PROGRESS] Saved: {i+1}/{TOTAL} ({percentage:.1f}%) - With content: {with_content}")
            
            time.sleep(3)  # Be nice to server
        
        await browser.close()
    
    # Final save
    log("[FINAL] Saving final results...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for r in enriched:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    with_content = len([r for r in enriched if r.get('full_content')])
    
    log("=" * 70)
    log("SCRAPING COMPLETE")
    log(f"Total processed: {len(enriched)}")
    log(f"With full content: {with_content}")
    log(f"Output: {OUTPUT_FILE}")
    log("=" * 70)


if __name__ == '__main__':
    asyncio.run(scrape_all_content())
