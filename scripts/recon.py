#!/usr/bin/env python3
"""
Reconnaissance script for Ortax Data Center
Analyzes the website structure to determine the best scraping approach.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

BASE_URL = "https://datacenter.ortax.org/ortax/aturan/list"

def analyze_page():
    """Analyze the main listing page"""
    print("=" * 60)
    print("ORTAX DATA CENTER - RECONNAISSANCE REPORT")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"\nFetching: {BASE_URL}")
        response = requests.get(BASE_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Length: {len(response.text)} bytes")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Analyze page structure
        print("\n" + "=" * 60)
        print("PAGE STRUCTURE ANALYSIS")
        print("=" * 60)
        
        # Find tables
        tables = soup.find_all('table')
        print(f"\nTables found: {len(tables)}")
        
        for i, table in enumerate(tables[:3]):
            rows = table.find_all('tr')
            print(f"  Table {i+1}: {len(rows)} rows")
            if rows:
                cols = rows[0].find_all(['td', 'th'])
                print(f"    Columns: {len(cols)}")
                if cols:
                    headers = [c.get_text(strip=True) for c in cols]
                    print(f"    Headers: {headers}")
        
        # Find list items
        lists = soup.find_all(['ul', 'ol'])
        print(f"\nLists found: {len(lists)}")
        
        # Find regulation-like elements
        print("\n" + "=" * 60)
        print("REGULATION ELEMENTS")
        print("=" * 60)
        
        # Common class names for regulation items
        possible_classes = [
            'regulation', 'aturan', 'item', 'entry', 'post',
            'list-item', 'data-item', 'row'
        ]
        
        for cls in possible_classes:
            elements = soup.find_all(class_=lambda x: x and cls in str(x).lower())
            if elements:
                print(f"\nElements with '{cls}' in class: {len(elements)}")
                if elements:
                    print(f"  Sample: {elements[0].get_text(strip=True)[:100]}...")
        
        # Find all links
        links = soup.find_all('a', href=True)
        print(f"\nTotal links: {len(links)}")
        
        # Find download links
        download_links = [a for a in links if 'download' in a.get('href', '').lower()]
        print(f"Download links: {len(download_links)}")
        
        # Find pagination
        print("\n" + "=" * 60)
        print("PAGINATION")
        print("=" * 60)
        
        pagination = soup.find(class_=lambda x: x and 'page' in str(x).lower())
        if pagination:
            print(f"Pagination element found: {pagination.get('class')}")
        
        page_links = [a for a in links if 'page' in a.get('href', '').lower()]
        print(f"Page links: {len(page_links)}")
        for link in page_links[:5]:
            print(f"  - {link.get('href')} (text: {link.get_text(strip=True)})")
        
        # Save sample HTML for inspection
        print("\n" + "=" * 60)
        print("SAVING SAMPLES")
        print("=" * 60)
        
        with open('data/sample_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("Saved: data/sample_page.html")
        
        # Extract and save potential regulation data
        print("\n" + "=" * 60)
        print("EXTRACTED DATA SAMPLES")
        print("=" * 60)
        
        samples = []
        
        # Try to find regulation data in various formats
        for row in soup.find_all('tr')[1:6]:  # Skip header, get 5 samples
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 3:
                sample = {
                    'raw_html': str(row)[:500],
                    'text_content': [c.get_text(strip=True) for c in cells]
                }
                samples.append(sample)
        
        with open('data/sample_regulations.json', 'w', encoding='utf-8') as f:
            json.dump(samples, f, indent=2, ensure_ascii=False)
        print("Saved: data/sample_regulations.json")
        
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)
        print("""
Based on the analysis:

1. If tables are found: Use table row selectors (tr, td)
2. If list items: Use list-based extraction
3. If pagination exists: Implement page following
4. Check for JavaScript rendering: May need Playwright/Selenium

Next steps:
1. Review sample_page.html manually
2. Review sample_regulations.json
3. Adjust spider selectors accordingly
4. Run test crawl with limited pages
        """)
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return False
    
    return True

if __name__ == '__main__':
    analyze_page()
