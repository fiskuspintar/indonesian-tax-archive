#!/usr/bin/env python3
"""
Ortax API Scraper
Uses the discovered API endpoint to collect all regulations efficiently.
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import time

BASE_API_URL = "https://datacenter.ortax.org/api/search/aturan"
OUTPUT_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
OUTPUT_FILE = OUTPUT_DIR / 'regulations.jsonl'

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


def normalize_reg_type(raw_type):
    """Map raw regulation type to standardized naming"""
    if not raw_type:
        return 'Unknown'
    
    for key, value in REGULATION_TYPES.items():
        if key in raw_type:
            return value
    
    return raw_type.strip()


def generate_filename(reg_type, number, year, subject):
    """Generate standardized filename"""
    import re
    
    # Clean subject
    if subject:
        subject_clean = re.sub(r'[^\w\s-]', '', subject)
        subject_clean = re.sub(r'[-\s]+', '-', subject_clean).strip('-')
        subject_clean = subject_clean[:100]
    else:
        subject_clean = 'unknown'
    
    # Format number with year
    if year and number:
        number_formatted = f"Nomor {number} Tahun {year}"
    elif number:
        number_formatted = f"Nomor {number}"
    elif year:
        number_formatted = f"Tahun {year}"
    else:
        number_formatted = 'unknown'
    
    filename = f"{reg_type}_{number_formatted}_{subject_clean}"
    return filename


def extract_number_and_year(title):
    """Extract regulation number and year from title"""
    number = None
    year = None
    
    # Patterns like "Nomor: 1 Tahun 2026" or "Nomor 36 Tahun 2008"
    import re
    
    # Extract year
    year_match = re.search(r'Tahun\s*:?\s*(\d{4})', title)
    if year_match:
        year = int(year_match.group(1))
    
    # Extract number
    number_match = re.search(r'Nomor\s*:?\s*([^\s]+)', title)
    if number_match:
        number = number_match.group(1).strip()
    
    return number, year


def fetch_page(page=1, per_page=100):
    """Fetch a single page of regulations from the API"""
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
        print(f"Error fetching page {page}: {e}")
        return None


def scrape_all_regulations():
    """Scrape all regulations using the API"""
    print("=" * 60)
    print("ORTAX API SCRAPER")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_regulations = []
    
    # First, get the first page to determine total pages
    print("\n[1] Fetching first page to determine total...")
    first_page = fetch_page(1, 100)
    
    if not first_page:
        print("ERROR: Could not fetch first page")
        return
    
    total = first_page.get('total', 0)
    per_page = first_page.get('perPage', 100)
    total_pages = first_page.get('totalPage', 0)
    
    print(f"  Total regulations: {total}")
    print(f"  Per page: {per_page}")
    print(f"  Total pages: {total_pages}")
    
    # Process first page
    if 'data' in first_page:
        all_regulations.extend(first_page['data'])
        print(f"  Fetched {len(first_page['data'])} from page 1")
    
    # Fetch remaining pages
    print(f"\n[2] Fetching remaining {total_pages - 1} pages...")
    
    for page_num in range(2, total_pages + 1):  # Fetch ALL pages
        print(f"  Fetching page {page_num}/{total_pages}...", end=' ')
        
        page_data = fetch_page(page_num, per_page)
        
        if page_data and 'data' in page_data:
            all_regulations.extend(page_data['data'])
            print(f"Got {len(page_data['data'])} regulations (Total: {len(all_regulations)})")
        else:
            print("Failed")
        
        # Be nice to the server - longer delay for full scrape
        time.sleep(1)
        
        # Save progress every 100 pages
        if page_num % 100 == 0:
            print(f"\n  [Checkpoint] Saving progress at page {page_num}...")
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                for reg in all_regulations:
                    f.write(json.dumps(reg, ensure_ascii=False) + '\n')
    
    print(f"\n[3] Processing {len(all_regulations)} regulations...")
    
    # Transform and save
    processed = []
    for i, item in enumerate(all_regulations):
        try:
            # Extract data
            title = item.get('title', '')
            full_title = item.get('fullTitle', '')
            description = item.get('description', '')
            
            # Determine regulation type from title
            reg_type_raw = ''
            for type_key in REGULATION_TYPES.keys():
                if type_key in full_title:
                    reg_type_raw = type_key
                    break
            
            reg_type = normalize_reg_type(reg_type_raw)
            number, year = extract_number_and_year(full_title)
            
            # Generate filename
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
            print(f"    Error processing item {i}: {e}")
            continue
    
    # Save to JSONL
    print(f"\n[4] Saving {len(processed)} regulations...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for reg in processed:
            f.write(json.dumps(reg, ensure_ascii=False) + '\n')
    
    # Save summary
    by_type = {}
    for reg in processed:
        reg_type = reg.get('regulation_type', 'Unknown')
        by_type[reg_type] = by_type.get(reg_type, 0) + 1
    
    summary = {
        'scraped_at': datetime.now().isoformat(),
        'total_regulations': len(processed),
        'by_type': by_type,
        'year_range': {
            'min': min(r.get('year') for r in processed if r.get('year')) if any(r.get('year') for r in processed) else None,
            'max': max(r.get('year') for r in processed if r.get('year')) if any(r.get('year') for r in processed) else None,
        }
    }
    
    with open(OUTPUT_DIR / 'scraping_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total regulations: {len(processed)}")
    print(f"By type:")
    for reg_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  - {reg_type}: {count}")
    print(f"Year range: {summary['year_range']['min']} - {summary['year_range']['max']}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"{'='*60}")
    
    return processed


if __name__ == '__main__':
    scrape_all_regulations()
