#!/usr/bin/env python3
"""
Export collected regulations to web application format
"""

import json
from pathlib import Path

DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
WEB_DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/web/public/data')

def export_for_web():
    """Export regulations to web app format"""
    print("Exporting regulations for web application...")
    
    # Load regulations
    regulations = []
    with open(DATA_DIR / 'regulations.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                regulations.append(json.loads(line))
    
    print(f"Loaded {len(regulations)} regulations")
    
    # Transform to web format
    web_regulations = []
    for reg in regulations:
        web_reg = {
            'id': reg['id'],
            'type': reg.get('regulation_type', 'Unknown'),
            'number': reg.get('number'),
            'year': reg.get('year'),
            'title': reg.get('subject', ''),
            'subject': reg.get('subject', ''),
            'filename': reg.get('filename', ''),
            'dateEnacted': reg.get('published_date'),
            'status': 'active',
            'content': '',  # Will be populated later with full text
            'pageCount': None,
        }
        web_regulations.append(web_reg)
    
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
    
    print(f"Exported to {WEB_DATA_DIR}")
    print(f"  - regulations.json: {len(web_regulations)} items")
    print(f"  - regulations-by-type.json: {len(by_type)} types")
    print(f"  - search-index.json: {len(search_index)} items")
    
    # Print summary by type
    print("\nRegulations by type:")
    for reg_type, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"  {reg_type}: {len(items)}")

if __name__ == '__main__':
    export_for_web()
