#!/usr/bin/env python3
"""
Indonesian Tax Regulations Archive - Master Execution Script
This script orchestrates the entire data collection and processing pipeline.

Usage:
    python run_pipeline.py [command]

Commands:
    scrape      - Run the web scraper to collect regulation metadata
    download    - Download regulation files (PDF/DOCX)
    extract     - Extract text from downloaded files
    import      - Import data into SQLite database
    export      - Export data for web application
    build       - Build the Next.js web application
    all         - Run complete pipeline (scrape → download → extract → import → export → build)
    validate    - Validate data integrity and naming conventions
    stats       - Show database statistics
"""

import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a shell command and print output"""
    print(f"\n{'='*60}")
    print(f"Running: {cmd}")
    print('='*60)
    
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=False,
        text=True
    )
    
    return result.returncode == 0


def ensure_directories():
    """Create necessary directories"""
    dirs = [
        'data/raw/downloads',
        'data/processed',
        'data/structured',
        'web/public/data',
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("✓ Directories created")


def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling Python dependencies...")
    return run_command("pip install -r requirements.txt")


def scrape():
    """Run the web scraper"""
    print("\n[1/6] Scraping regulation metadata from Ortax...")
    return run_command("cd scraper && scrapy crawl ortax_regulations -L INFO")


def download():
    """Download regulation files"""
    print("\n[2/6] Downloading regulation files...")
    # This is handled by the pipeline in the spider
    print("Downloads are handled during scraping via pipeline")
    return True


def extract():
    """Extract text from downloaded files"""
    print("\n[3/6] Extracting text from downloaded files...")
    return run_command("python scripts/extract_text.py")


def import_to_db():
    """Import data into database"""
    print("\n[4/6] Importing data into SQLite database...")
    return run_command("python scripts/import_to_db.py")


def export_for_web():
    """Export data for web application"""
    print("\n[5/6] Exporting data for web application...")
    return run_command("python scripts/import_to_db.py")


def build_web():
    """Build the Next.js web application"""
    print("\n[6/6] Building Next.js web application...")
    
    # Install npm dependencies
    if not run_command("cd web && npm install"):
        return False
    
    # Build
    return run_command("cd web && npm run build")


def validate():
    """Validate data integrity"""
    print("\nValidating data integrity...")
    return run_command("python scripts/validate.py")


def stats():
    """Show database statistics"""
    print("\nDatabase Statistics:")
    return run_command("python -c \"from scripts.import_to_db import DatabaseImporter; i = DatabaseImporter(); print(__import__('json').dumps(i.get_statistics(), indent=2, ensure_ascii=False))\"")


def main():
    """Main entry point"""
    command = sys.argv[1] if len(sys.argv) > 1 else 'help'
    
    # Ensure we're in the right directory
    if not Path('scraper').exists():
        print("Error: Must run from project root directory")
        sys.exit(1)
    
    ensure_directories()
    
    commands = {
        'scrape': [scrape],
        'download': [download],
        'extract': [extract],
        'import': [import_to_db],
        'export': [export_for_web],
        'build': [build_web],
        'all': [scrape, download, extract, import_to_db, export_for_web, build_web],
        'validate': [validate],
        'stats': [stats],
        'help': [lambda: print(__doc__)],
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
    
    for func in commands[command]:
        if not func():
            print(f"\n❌ Command failed: {func.__name__}")
            sys.exit(1)
    
    print("\n✅ All commands completed successfully!")


if __name__ == '__main__':
    main()
