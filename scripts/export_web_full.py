#!/usr/bin/env python3
"""
Export collected regulations to web application format (for full scrape data)
"""

import json
from pathlib import Path
import re

DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
WEB_DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/web/public/data')

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
    'Pengumuman': 'Pengumuman',
    'Nota Dinas': 'Nota Dinas',
}


def normalize_reg_type(raw_type):
    if not raw_type:
        return 'Unknown'
    for key, value in REGULATION_TYPES.items():
        if key in raw_type:
            return value
    return raw_type.strip()


def extract_number_and_year(title):
    number = None
    year = None
    
    year_match = re.search(r'Tahun\s*:?\s*(\d{4})', title)
    if year_match:
        year = int(year_match.group(1))
    
    number_match = re.search(r'Nomor\s*:?\s*([^\s]+)', title)
    if number_match:
        number = number_match.group(1).strip()
    
    return number, year


def generate_filename(reg_type, number, year, subject):
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


def export_for_web():
    print("Exporting regulations for web application...")
    
    # Load regulations from full scrape
    regulations = []
    with open(DATA_DIR / 'regulations_full.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                regulations.append(json.loads(line))
    
    print(f"Loaded {len(regulations)} regulations")
    
    # Transform to web format
    web_regulations = []
    for i, item in enumerate(regulations):
        full_title = item.get('fullTitle', '')
        description = item.get('description', '')
        
        # Determine regulation type
        reg_type_raw = ''
        for type_key in REGULATION_TYPES.keys():
            if type_key in full_title:
                reg_type_raw = type_key
                break
        
        reg_type = normalize_reg_type(reg_type_raw)
        number, year = extract_number_and_year(full_title)
        
        filename = generate_filename(reg_type, number, year, description)
        
        web_reg = {
            'id': i + 1,
            'type': reg_type,
            'number': number,
            'year': year,
            'title': description,
            'subject': description,
            'filename': filename,
            'dateEnacted': item.get('publishedDate'),
            'status': 'active',
            'content': '',
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
    
    print(f"\nExported to {WEB_DATA_DIR}")
    print(f"  - regulations.json: {len(web_regulations)} items")
    print(f"  - regulations-by-type.json: {len(by_type)} types")
    print(f"  - search-index.json: {len(search_index)} items")
    
    print("\nRegulations by type:")
    for reg_type, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"  {reg_type}: {len(items)}")


if __name__ == '__main__':
    export_for_web()
