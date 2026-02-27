#!/usr/bin/env python3
"""
FIX DATA - Use existing processed data with correct Ortax IDs
"""

import json
from pathlib import Path

DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
WEB_DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/web/public/data')

print("[FIX] Loading processed regulations...")
regulations = []
with open(DATA_DIR / 'regulations_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            regulations.append(json.loads(line))

print(f"[FIX] Loaded {len(regulations)} regulations")

print("[FIX] Rebuilding with correct Ortax IDs...")

web_regulations = []
for item in regulations:
    # Extract Ortax ID from source_url
    source_url = item.get('source_url', '')
    ortax_id = source_url.split('/')[-1] if source_url else item.get('api_id')
    
    web_reg = {
        'id': int(ortax_id),  # Use REAL Ortax ID from URL
        'type': item.get('regulation_type', 'Unknown'),
        'number': item.get('number'),
        'year': item.get('year'),
        'title': item.get('subject', ''),
        'subject': item.get('subject', ''),
        'filename': item.get('filename', ''),
        'dateEnacted': item.get('published_date'),
        'status': 'active',
        'content': item.get('full_content', ''),  # Use content if available
        'pageCount': None,
    }
    web_regulations.append(web_reg)

print(f"[FIX] Rebuilt {len(web_regulations)} regulations with correct IDs")

# Group by type
by_type = {}
for reg in web_regulations:
    reg_type = reg['type']
    if reg_type not in by_type:
        by_type[reg_type] = []
    by_type[reg_type].append(reg)

# Create search index
search_index = []
for reg in web_regulations:
    search_index.append({
        'id': reg['id'],
        'title': reg['title'],
        'type': reg['type'],
        'year': reg['year'],
        'number': reg['number'],
        'content': reg['subject'][:500] if reg['subject'] else '',
    })

# Save files
WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

with open(WEB_DATA_DIR / 'regulations.json', 'w', encoding='utf-8') as f:
    json.dump(web_regulations, f, ensure_ascii=False, indent=2)

with open(WEB_DATA_DIR / 'regulations-by-type.json', 'w', encoding='utf-8') as f:
    json.dump(by_type, f, ensure_ascii=False, indent=2)

with open(WEB_DATA_DIR / 'search-index.json', 'w', encoding='utf-8') as f:
    json.dump(search_index, f, ensure_ascii=False, indent=2)

print(f"[FIX] Saved to {WEB_DATA_DIR}")
print(f"  - regulations.json: {len(web_regulations)} items")
print(f"  - regulations-by-type.json: {len(by_type)} types")

# Verify: Show sample with correct ID
print("\n[FIX] Sample regulations with CORRECT IDs:")
for i, reg in enumerate(web_regulations[:3]):
    print(f"\n  Regulation {i+1}:")
    print(f"    ID: {reg['id']}")
    print(f"    Type: {reg['type']}")
    print(f"    Number: {reg['number']}")
    print(f"    Year: {reg['year']}")
    print(f"    Filename: {reg['filename']}")
    print(f"    Ortax URL: https://datacenter.ortax.org/ortax/aturan/show/{reg['id']}")

# Verify ID 24 specifically
print("\n[FIX] Looking for regulation that should match Ortax ID 24...")
for reg in web_regulations:
    if reg['id'] == 24:
        print(f"  FOUND ID 24:")
        print(f"    Type: {reg['type']}")
        print(f"    Number: {reg['number']}")
        print(f"    Year: {reg['year']}")
        print(f"    Subject: {reg['subject'][:100]}...")
        print(f"    Ortax URL: https://datacenter.ortax.org/ortax/aturan/show/24")
        break
else:
    print("  No regulation with ID 24 found in our data")

print("\n[FIX] Data rebuild complete!")
