#!/usr/bin/env python3
"""
Ortax Tax Regulations Scraper
Extracts all Indonesian tax regulations from datacenter.ortax.org
"""

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
from datetime import datetime
import re
from urllib.parse import urljoin

BASE_URL = "https://datacenter.ortax.org/ortax/aturan/list"
OUTPUT_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
OUTPUT_FILE = OUTPUT_DIR / 'regulations.jsonl'

# Regulation type mapping
REGULATION_TYPES = {
    'UUD 1945': 'UUD 1945',
    'UNDANG-UNDANG DASAR': 'UUD 1945',
    'TAP MPR': 'Tap MPR',
    'KETETAPAN MPR': 'Tap MPR',
    'UNDANG-UNDANG': 'UU',
    'UU': 'UU',
    'PERPU': 'PERPU',
    'PERATURAN PEMERINTAH PENGGANTI UNDANG-UNDANG': 'PERPU',
    'PERATURAN PEMERINTAH': 'PP',
    'PP': 'PP',
    'PERATURAN PRESIDEN': 'Perpres',
    'PERPRES': 'Perpres',
    'PERATURAN MENTERI KEUANGAN': 'Peraturan Menteri Keuangan',
    'PMK': 'Peraturan Menteri Keuangan',
    'KEPUTUSAN MENTERI KEUANGAN': 'Keputusan Menteri Keuangan',
    'KMK': 'Keputusan Menteri Keuangan',
    'PERATURAN DIREKTUR JENDERAL PAJAK': 'Peraturan Direktur Jenderal Pajak',
    'PERATURAN DIRJEN PAJAK': 'Peraturan Direktur Jenderal Pajak',
    'KETETAPAN DIREKTUR JENDERAL PAJAK': 'Ketetapan Direktur Jenderal Pajak',
    'KETETAPAN DIRJEN PAJAK': 'Ketetapan Direktur Jenderal Pajak',
    'SURAT EDARAN DIREKTUR JENDERAL PAJAK': 'Surat Edaran Dirjen Pajak',
    'SURAT EDARAN DIRJEN PAJAK': 'Surat Edaran Dirjen Pajak',
    'SE DIRJEN PAJAK': 'Surat Edaran Dirjen Pajak',
}


def normalize_reg_type(raw_type):
    """Map raw regulation type to standardized naming"""
    if not raw_type:
        return 'Unknown'
    
    raw_clean = raw_type.strip().upper()
    
    for key, value in REGULATION_TYPES.items():
        if key in raw_clean:
            return value
    
    if 'MENTERI KEUANGAN' in raw_clean:
        if 'KEPUTUSAN' in raw_clean:
            return 'Keputusan Menteri Keuangan'
        return 'Peraturan Menteri Keuangan'
    
    if 'DIRJEN PAJAK' in raw_clean or 'DIREKTUR JENDERAL PAJAK' in raw_clean:
        if 'SURAT EDARAN' in raw_clean:
            return 'Surat Edaran Dirjen Pajak'
        if 'KETETAPAN' in raw_clean:
            return 'Ketetapan Direktur Jenderal Pajak'
        return 'Peraturan Direktur Jenderal Pajak'
    
    return raw_type.strip()


def generate_filename(reg_type, number, year, subject):
    """Generate standardized filename"""
    import re as regex
    
    # Clean subject
    if subject:
        subject_clean = regex.sub(r'[^\w\s-]', '', subject)
        subject_clean = regex.sub(r'[-\s]+', '-', subject_clean).strip('-')
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


async def scrape_ortax():
    """Main scraping function"""
    print("=" * 60)
    print("ORTAX TAX REGULATIONS SCRAPER")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    regulations = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print("\n[1/4] Loading main page...")
        await page.goto(BASE_URL, wait_until='networkidle')
        await asyncio.sleep(3)  # Wait for JavaScript to load
        
        # Wait for the table/data to load
        print("[2/4] Waiting for content to load...")
        try:
            await page.wait_for_selector('table tbody tr, [class*="row"], [class*="item"]', timeout=10000)
        except:
            print("Warning: Could not find expected content selectors")
        
        await asyncio.sleep(2)
        
        # Get page content
        print("[3/4] Extracting regulation data...")
        
        # Try multiple selectors to find regulation data
        selectors_to_try = [
            'table tbody tr',
            '[class*="regulation"]',
            '[class*="item"]',
            'article',
            '.list-item',
        ]
        
        rows = []
        for selector in selectors_to_try:
            rows = await page.query_selector_all(selector)
            if len(rows) > 0:
                print(f"  Found {len(rows)} elements with selector: {selector}")
                break
        
        print(f"\n  Total rows found: {len(rows)}")
        
        # Extract data from each row
        for i, row in enumerate(rows):
            try:
                # Get all text content
                text_content = await row.inner_text()
                
                # Get HTML for analysis
                html_content = await row.inner_html()
                
                # Look for links
                links = await row.query_selector_all('a')
                detail_url = None
                download_url = None
                
                for link in links:
                    href = await link.get_attribute('href')
                    if href:
                        full_url = urljoin(BASE_URL, href)
                        text = await link.inner_text()
                        
                        if 'download' in href.lower() or 'download' in text.lower():
                            download_url = full_url
                        else:
                            detail_url = full_url
                
                # Parse regulation data from text
                # Common patterns in Indonesian regulations
                reg_data = {
                    'id': i + 1,
                    'raw_text': text_content[:500],
                    'detail_url': detail_url,
                    'download_url': download_url,
                    'scraped_at': datetime.now().isoformat(),
                }
                
                # Try to extract regulation type
                for pattern in REGULATION_TYPES.keys():
                    if pattern in text_content.upper():
                        reg_data['regulation_type_raw'] = pattern
                        reg_data['regulation_type'] = normalize_reg_type(pattern)
                        break
                
                # Try to extract year (4 digits that look like a year)
                year_match = re.search(r'\b(19|20)\d{2}\b', text_content)
                if year_match:
                    reg_data['year'] = int(year_match.group(0))
                
                # Try to extract number
                number_patterns = [
                    r'(?:Nomor|No\.?)\s*[:.]?\s*(\d+)',
                    r'(?:NOMOR|NO)\s*[:.]?\s*(\d+)',
                ]
                for pattern in number_patterns:
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        reg_data['number'] = match.group(1)
                        break
                
                # Extract subject (usually the longest text)
                lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                if lines:
                    # Filter out short lines (likely headers/metadata)
                    long_lines = [l for l in lines if len(l) > 20]
                    if long_lines:
                        reg_data['subject'] = long_lines[0][:200]
                    else:
                        reg_data['subject'] = lines[-1][:200]
                
                # Generate filename
                if reg_data.get('regulation_type'):
                    reg_data['filename'] = generate_filename(
                        reg_data['regulation_type'],
                        reg_data.get('number', ''),
                        reg_data.get('year'),
                        reg_data.get('subject', '')
                    )
                
                regulations.append(reg_data)
                
                # Print progress
                if (i + 1) % 10 == 0:
                    print(f"    Processed {i + 1} rows...")
                
            except Exception as e:
                print(f"    Error processing row {i}: {e}")
                continue
        
        # Check for pagination
        print("\n[4/4] Checking for pagination...")
        
        pagination_info = {
            'current_page': 1,
            'total_pages': 1,
        }
        
        # Look for page indicators
        page_text = await page.inner_text('body')
        page_match = re.search(r'(\d+)\s*/\s*(\d+)', page_text)  # e.g., "1 / 10"
        if page_match:
            pagination_info['current_page'] = int(page_match.group(1))
            pagination_info['total_pages'] = int(page_match.group(2))
            print(f"  Found pagination: Page {pagination_info['current_page']} of {pagination_info['total_pages']}")
        
        # Try to find and click next page
        next_button = await page.query_selector('a:has-text("Next"), a:has-text("Berikutnya"), [class*="next"]')
        if next_button:
            print("  Found next page button")
        
        await browser.close()
    
    # Save results
    print(f"\n[5/5] Saving {len(regulations)} regulations...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for reg in regulations:
            f.write(json.dumps(reg, ensure_ascii=False) + '\n')
    
    # Save summary
    summary = {
        'scraped_at': datetime.now().isoformat(),
        'total_regulations': len(regulations),
        'by_type': {},
        'pagination': pagination_info,
    }
    
    for reg in regulations:
        reg_type = reg.get('regulation_type', 'Unknown')
        summary['by_type'][reg_type] = summary['by_type'].get(reg_type, 0) + 1
    
    with open(OUTPUT_DIR / 'scraping_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total regulations: {len(regulations)}")
    print(f"By type: {summary['by_type']}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"{'='*60}")
    
    return regulations


if __name__ == '__main__':
    regulations = asyncio.run(scrape_ortax())
