#!/usr/bin/env python3
"""
FULL CONTENT SCRAPER - Using Ortax API (CORRECT VERSION)
This gets the COMPLETE document content via API with HTML parsing
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import time
from html.parser import HTMLParser

DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
OUTPUT_FILE = DATA_DIR / 'regulations_with_content_api.jsonl'
PROGRESS_FILE = DATA_DIR / 'content_scrape_api_progress.json'
LOG_FILE = DATA_DIR / 'content_scrape_api.log'


class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_script = False
        self.in_style = False
        
    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            self.in_script = True
        elif tag == 'br':
            self.text.append('\n')
        elif tag in ['p', 'div']:
            self.text.append('\n\n')
            
    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.in_script = False
        elif tag in ['p', 'div']:
            self.text.append('\n')
            
    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            self.text.append(data)
            
    def get_text(self):
        text = ''.join(self.text)
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(line for line in lines if line)


# Load existing regulations
print("[INIT] Loading regulations...")
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


def fetch_full_content_api(regulation_id):
    """Fetch FULL content using Ortax API"""
    url = f"https://datacenter.ortax.org/api/datacenter/aturan/{regulation_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract HTML content from API response
        content_obj = data.get('content', {})
        if isinstance(content_obj, dict):
            html_content = content_obj.get('idn', '')
        else:
            html_content = str(content_obj)
        
        if html_content and len(html_content) > 100:
            # Parse HTML to text
            extractor = HTMLTextExtractor()
            extractor.feed(html_content)
            text_content = extractor.get_text()
            
            if len(text_content) > 200:
                return text_content
        
        return None
        
    except Exception as e:
        log(f"  Error fetching ID {regulation_id}: {e}")
        return None


def scrape_all_content():
    log("=" * 70)
    log("FULL CONTENT SCRAPER - API VERSION - STARTING")
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
    
    log("[INIT] Starting API scraping...")
    
    for i in range(start_index, TOTAL):
        reg = regulations[i]
        source_url = reg.get('source_url', '')
        ortax_id = source_url.split('/')[-1] if source_url else reg.get('api_id')
        
        log(f"[{i+1}/{TOTAL}] Fetching ID {ortax_id}...")
        
        content = fetch_full_content_api(ortax_id)
        
        if content:
            reg['full_content'] = content
            log(f"  ✓ Content: {len(content):,} characters")
        else:
            reg['full_content'] = None
            log(f"  ✗ No content")
        
        enriched.append(reg)
        
        # Save progress every 10
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
            log(f"[PROGRESS] {i+1}/{TOTAL} ({percentage:.1f}%) - With content: {with_content}")
        
        time.sleep(0.5)  # Be nice to API
    
    # Final save
    log("[FINAL] Saving final results...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for r in enriched:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    with_content = len([r for r in enriched if r.get('full_content')])
    
    log("=" * 70)
    log("SCRAPING COMPLETE")
    log(f"Total: {len(enriched)}")
    log(f"With content: {with_content}")
    log(f"Output: {OUTPUT_FILE}")
    log("=" * 70)


if __name__ == '__main__':
    scrape_all_content()
