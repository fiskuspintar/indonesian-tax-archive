#!/usr/bin/env python3
"""
Ortax API Scraper - Full Collection (Background version with progress saving)
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import time
import sys

BASE_API_URL = "https://datacenter.ortax.org/api/search/aturan"
OUTPUT_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
OUTPUT_FILE = OUTPUT_DIR / 'regulations_full.jsonl'
PROGRESS_FILE = OUTPUT_DIR / 'scrape_progress.json'

# Regulation type mapping
REGULATION_TYPES = {
    'Undang-Undang': 'UU',
    'Perpu': 'PERPU',
    'Peraturan Pemerintah': 'PP',
    'Peraturan Presiden': 'Perpres',
    'Keputusan Presiden': 'Keputusan Presiden',
    'Instruksi Presiden': 'Instruksi Presiden',
    'Keputusan Bersama Menteri': 'Keputusan Bersama Menteri',
    'Peraturan Bersama Menteri': 'Peraturan Bersama Menteri',
    'Peraturan Menteri Keuangan': 'Peraturan Menteri Keuangan',
    'Keputusan Menteri Keuangan': 'Keputusan Menteri Keuangan',
    'Instruksi Menteri Keuangan': 'Instruksi Menteri Keuangan',
    'Surat Edaran Menteri Keuangan': 'Surat Edaran Menteri Keuangan',
    'Surat Menteri Keuangan': 'Surat Menteri Keuangan',
    'Peraturan Dirjen Pajak': 'Peraturan Direktur Jenderal Pajak',
    'Keputusan Dirjen Pajak': 'Keputusan Direktur Jenderal Pajak',
    'Instruksi Dirjen Pajak': 'Instruksi Dirjen Pajak',
    'Surat Edaran Dirjen Pajak': 'Surat Edaran Dirjen Pajak',
    'Peraturan Dirjen Bea dan Cukai': 'Peraturan Dirjen Bea dan Cukai',
    'Keputusan Dirjen Bea dan Cukai': 'Keputusan Dirjen Bea dan Cukai',
    'Surat Edaran Dirjen Bea dan Cukai': 'Surat Edaran Dirjen Bea dan Cukai',
}


def log(message):
    """Print with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def normalize_reg_type(raw_type):
    if not raw_type:
        return 'Unknown'
    for key, value in REGULATION_TYPES.items():
        if key in raw_type:
            return value
    return raw_type.strip()


def generate_filename(reg_type, number, year, subject):
    import re
    if subject:
        subject_clean = re.sub(r'[^\w\s-]', '', subject)
        subject_clean = re.sub(r'[-\s]+', '-', subject_clean).strip('-')
        subject_clean = subject_clean[:100]
    else:
        subject_clean = 'unknown'
    
    if year and number:
        number_formatted = f"Nomor {number} Tahun {year}"
    elif number:
        number_formatted = f"Nomor {number}"
    elif year:
        number_formatted = f"Tahun {year}"
    else:
        number_formatted = 'unknown'
    
    return f"{reg_type}_{number_formatted}_{subject_clean}"


def extract_number_and_year(title):
    import re
    number = None
    year = None
    
    year_match = re.search(r'Tahun\s*:?\s*(\d{4})', title)
    if year_match:
        year = int(year_match.group(1))
    
    number_match = re.search(r'Nomor\s*:?\s*([^\s]+)', title)
    if number_match:
        number = number_match.group(1).strip()
    
    return number, year


def fetch_page(page=1, per_page=100):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'page': page,
        'perPage': per_page,
    }
    
    try:
        response = requests.post(BASE_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"Error fetching page {page}: {e}")
        return None


def save_progress(all_regulations, page_num):
    """Save progress to file"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for reg in all_regulations:
            f.write(json.dumps(reg, ensure_ascii=False) + '\n')
    
    progress = {
        'last_page': page_num,
        'total_collected': len(all_regulations),
        'timestamp': datetime.now().isoformat(),
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)
    
    log(f"Progress saved: {len(all_regulations)} regulations from {page_num} pages")


def scrape_all_regulations():
    log("=" * 60)
    log("ORTAX API SCRAPER - FULL COLLECTION")
    log("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for existing progress
    start_page = 1
    all_regulations = []
    
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            start_page = progress.get('last_page', 1)
            log(f"Resuming from page {start_page}")
    
    if OUTPUT_FILE.exists() and start_page > 1:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    all_regulations.append(json.loads(line))
        log(f"Loaded {len(all_regulations)} existing regulations")
    
    # Get first page to determine total
    if start_page == 1:
        log("Fetching first page...")
        first_page = fetch_page(1, 100)
        
        if not first_page:
            log("ERROR: Could not fetch first page")
            return
        
        total = first_page.get('total', 0)
        total_pages = first_page.get('totalPage', 0)
        
        log(f"Total regulations: {total}")
        log(f"Total pages: {total_pages}")
        
        if 'data' in first_page:
            all_regulations.extend(first_page['data'])
            log(f"Fetched {len(first_page['data'])} from page 1")
        
        start_page = 2
    else:
        # Get total from a quick fetch
        test_page = fetch_page(1, 1)
        total_pages = test_page.get('totalPage', 1364) if test_page else 1364
    
    # Fetch remaining pages
    log(f"Fetching pages {start_page} to {total_pages}...")
    
    for page_num in range(start_page, total_pages + 1):
        page_data = fetch_page(page_num, 100)
        
        if page_data and 'data' in page_data:
            all_regulations.extend(page_data['data'])
            
            if page_num % 10 == 0:
                log(f"Page {page_num}/{total_pages}: {len(all_regulations)} regulations")
        else:
            log(f"Failed to fetch page {page_num}")
        
        # Save progress every 50 pages
        if page_num % 50 == 0:
            save_progress(all_regulations, page_num)
        
        time.sleep(0.8)  # Be nice to the server
    
    # Final save
    save_progress(all_regulations, total_pages)
    
    # Process and save final output
    log(f"\nProcessing {len(all_regulations)} regulations...")
    
    processed = []
    for i, item in enumerate(all_regulations):
        try:
            title = item.get('title', '')
            full_title = item.get('fullTitle', '')
            description = item.get('description', '')
            
            reg_type_raw = ''
            for type_key in REGULATION_TYPES.keys():
                if type_key in full_title:
                    reg_type_raw = type_key
                    break
            
            reg_type = normalize_reg_type(reg_type_raw)
            number, year = extract_number_and_year(full_title)
            
            filename = generate_filename(reg_type, number, year, description)
            
            processed_item = {
                'id': i + 1,
                'api_id': item.get('id'),
                'regulation_type': reg_type,
                'regulation_type_raw': reg_type_raw,
                'number': number,
                'year': year,
                'title': full_title,
                'subject': description,
                'filename': filename,
                'categories': [c.get('title') for c in item.get('categories', [])],
                'published_date': item.get('publishedDate'),
                'created_date': item.get('createdDate'),
                'source_url': f"https://datacenter.ortax.org/ortax/aturan/show/{item.get('id')}",
                'scraped_at': datetime.now().isoformat(),
            }
            
            processed.append(processed_item)
            
        except Exception as e:
            log(f"Error processing item {i}: {e}")
            continue
    
    # Save processed
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for reg in processed:
            f.write(json.dumps(reg, ensure_ascii=False) + '\n')
    
    # Summary
    by_type = {}
    for reg in processed:
        reg_type = reg.get('regulation_type', 'Unknown')
        by_type[reg_type] = by_type.get(reg_type, 0) + 1
    
    summary = {
        'scraped_at': datetime.now().isoformat(),
        'total_regulations': len(processed),
        'by_type': by_type,
    }
    
    with open(OUTPUT_DIR / 'scraping_summary_full.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    log("=" * 60)
    log("SCRAPING COMPLETE")
    log(f"Total: {len(processed)} regulations")
    log(f"Output: {OUTPUT_FILE}")
    log("=" * 60)


if __name__ == '__main__':
    scrape_all_regulations()
