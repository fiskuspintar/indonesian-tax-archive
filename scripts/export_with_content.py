#!/usr/bin/env python3
"""
Export regulations WITH CONTENT to web application
"""

import json
from pathlib import Path

DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')
WEB_DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/web/public/data')

print("[EXPORT] Loading regulations with content...")

# Load regulations with content
regulations = []
if (DATA_DIR / 'regulations_with_content.jsonl').exists():
    with open(DATA_DIR / 'regulations_with_content.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                regulations.append(json.loads(line))
    print(f"[EXPORT] Loaded {len(regulations)} regulations with content")
else:
    print("[EXPORT] No content file yet, using base data")

# Also load all regulations for those without content yet
all_regs = []
with open(DATA_DIR / 'regulations_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            all_regs.append(json.loads(line))

print(f"[EXPORT] Total regulations in database: {len(all_regs)}")

# Create a map of regulations with content
content_map = {r.get('api_id'): r.get('full_content') for r in regulations}

# Build web regulations
web_regulations = []
for item in all_regs:
    source_url = item.get('source_url', '')
    ortax_id = source_url.split('/')[-1] if source_url else item.get('api_id')
    api_id = item.get('api_id')
    
    # Check if we have content for this regulation
    full_content = content_map.get(api_id, '')
    
    web_reg = {
        'id': int(ortax_id),
        'type': item.get('regulation_type', 'Unknown'),
        'number': item.get('number'),
        'year': item.get('year'),
        'title': item.get('subject', ''),
        'subject': item.get('subject', ''),
        'filename': item.get('filename', ''),
        'dateEnacted': item.get('published_date'),
        'status': 'active',
        'content': full_content if full_content else '',  # Use content if available
        'pageCount': None,
    }
    web_regulations.append(web_reg)

print(f"[EXPORT] Built {len(web_regulations)} web regulations")

# Count with content
with_content = len([r for r in web_regulations if r.get('content')])
print(f"[EXPORT] Regulations with full content: {with_content}")

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
        'content': reg['content'][:1000] if reg.get('content') else reg['subject'][:500],
    })

# Save files
WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

with open(WEB_DATA_DIR / 'regulations.json', 'w', encoding='utf-8') as f:
    json.dump(web_regulations, f, ensure_ascii=False, indent=2)

with open(WEB_DATA_DIR / 'regulations-by-type.json', 'w', encoding='utf-8') as f:
    json.dump(by_type, f, ensure_ascii=False, indent=2)

with open(WEB_DATA_DIR / 'search-index.json', 'w', encoding='utf-8') as f:
    json.dump(search_index, f, ensure_ascii=False, indent=2)

print(f"[EXPORT] Saved to {WEB_DATA_DIR}")
print(f"  - regulations.json: {len(web_regulations)} items")
print(f"  - regulations-by-type.json: {len(by_type)} types")
print(f"  - search-index.json: {len(search_index)} items")
print(f"  - With full content: {with_content}")

print("\n[EXPORT] Export complete!")
