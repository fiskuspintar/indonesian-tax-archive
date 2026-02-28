#!/usr/bin/env python3
"""
QA Script - Check content quality by comparing lengths
Run this to verify scraped content is complete
"""

import json
from pathlib import Path
import random

DATA_DIR = Path('/root/.openclaw/workspace/indonesian-tax-archive/data/raw')

def check_content_quality():
    print("=" * 70)
    print("CONTENT QUALITY CHECK")
    print("=" * 70)
    
    # Load regulations with content
    regulations = []
    if (DATA_DIR / 'regulations_with_content.jsonl').exists():
        with open(DATA_DIR / 'regulations_with_content.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    regulations.append(json.loads(line))
    
    if not regulations:
        print("No content file found!")
        return
    
    print(f"Total regulations with content: {len(regulations)}")
    
    # Check content lengths
    with_content = [r for r in regulations if r.get('full_content')]
    print(f"Successfully scraped: {len(with_content)}")
    
    if with_content:
        lengths = [len(r['full_content']) for r in with_content]
        avg_length = sum(lengths) / len(lengths)
        max_length = max(lengths)
        min_length = min(lengths)
        
        print(f"\nContent length statistics:")
        print(f"  Average: {avg_length:,.0f} characters")
        print(f"  Maximum: {max_length:,.0f} characters")
        print(f"  Minimum: {min_length:,.0f} characters")
        
        # Find potentially truncated content (less than 2000 chars)
        short_content = [r for r in with_content if len(r['full_content']) < 2000]
        print(f"\nPotentially truncated (< 2000 chars): {len(short_content)}")
        
        # Sample check - show 5 random regulations
        print("\n" + "=" * 70)
        print("SAMPLE CHECK (5 random regulations):")
        print("=" * 70)
        
        sample = random.sample(with_content, min(5, len(with_content)))
        for r in sample:
            content_len = len(r.get('full_content', ''))
            api_id = r.get('api_id', 'N/A')
            print(f"\nID: {api_id}")
            print(f"Title: {r.get('subject', 'N/A')[:80]}...")
            print(f"Content length: {content_len:,} characters")
            print(f"Ortax URL: https://datacenter.ortax.org/ortax/aturan/show/{api_id}")
            
            if content_len < 2000:
                print("⚠️  WARNING: Content may be truncated!")
            else:
                print("✓ Content looks good")
    
    # Check specific problematic ID
    print("\n" + "=" * 70)
    print("CHECKING SPECIFIC ID 26509 (reported as truncated):")
    print("=" * 70)
    
    for r in regulations:
        if r.get('api_id') == '26509':
            content = r.get('full_content', '')
            print(f"Found ID 26509")
            print(f"Content length: {len(content):,} characters")
            print(f"\nFirst 500 chars:\n{content[:500]}...")
            print(f"\nLast 500 chars:\n...{content[-500:]}")
            
            # Count lines/paragraphs
            lines = content.split('\n')
            print(f"\nTotal lines: {len(lines)}")
            break
    else:
        print("ID 26509 not found in scraped content")


if __name__ == '__main__':
    check_content_quality()
