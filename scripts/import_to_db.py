import sqlite3
import json
from pathlib import Path
from datetime import datetime


class DatabaseImporter:
    """Import scraped and processed data into SQLite database"""
    
    def __init__(self, db_path='../data/tax_regulations.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with schema"""
        conn = sqlite3.connect(self.db_path)
        with open('../data/schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()
        print(f"Database initialized: {self.db_path}")
    
    def import_from_jsonl(self, metadata_file='../data/raw/regulations.jsonl'):
        """Import regulations from scraped metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        count = 0
        filepath = Path(metadata_file)
        
        if not filepath.exists():
            print(f"Metadata file not found: {metadata_file}")
            return 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    
                    # Extract text content if available
                    processed_path = Path('../data/processed') / f"{data.get('filename', '')}.json"
                    full_text = ''
                    page_count = None
                    extracted_metadata = None
                    
                    if processed_path.exists():
                        with open(processed_path, 'r', encoding='utf-8') as pf:
                            processed = json.load(pf)
                            
                            # Extract full text
                            if isinstance(processed.get('pages'), list):
                                full_text = '\n\n'.join(
                                    p.get('text', '') for p in processed['pages'] if p.get('text')
                                )
                                page_count = len(processed['pages'])
                            else:
                                full_text = processed.get('full_text', '')
                            
                            extracted_metadata = json.dumps({
                                'format': processed.get('format'),
                                'page_count': processed.get('page_count'),
                                'pdf_metadata': processed.get('metadata')
                            })
                    
                    # Build search vector
                    search_vector = ' '.join(filter(None, [
                        data.get('regulation_type', ''),
                        data.get('number', ''),
                        str(data.get('year', '')),
                        data.get('subject', ''),
                        full_text[:5000]  # First 5000 chars for search
                    ]))
                    
                    # Insert regulation
                    cursor.execute('''
                        INSERT OR REPLACE INTO regulations 
                        (regulation_type, number, year, title, subject, filename,
                         source_url, download_url, local_path, full_text, 
                         search_vector, page_count, extracted_metadata, file_format)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data.get('regulation_type'),
                        data.get('number'),
                        data.get('year'),
                        data.get('subject', ''),
                        data.get('subject', ''),
                        data.get('filename'),
                        data.get('source_url'),
                        data.get('download_url'),
                        data.get('local_path'),
                        full_text,
                        search_vector,
                        page_count,
                        extracted_metadata,
                        self.detect_format(data.get('local_path'))
                    ))
                    
                    count += 1
                    
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON line: {e}")
                except Exception as e:
                    print(f"Error importing regulation: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"Imported {count} regulations")
        return count
    
    def detect_format(self, local_path):
        """Detect file format from path"""
        if not local_path:
            return None
        
        path = Path(local_path)
        ext = path.suffix.lower()
        
        format_map = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'doc',
            '.html': 'html',
            '.htm': 'html',
            '.txt': 'txt'
        }
        
        return format_map.get(ext)
    
    def get_statistics(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        stats = {}
        
        # Total count
        cursor.execute('SELECT COUNT(*) as count FROM regulations')
        stats['total'] = cursor.fetchone()['count']
        
        # By type
        cursor.execute('SELECT regulation_type, COUNT(*) as count FROM regulations GROUP BY regulation_type')
        stats['by_type'] = {row['regulation_type']: row['count'] for row in cursor.fetchall()}
        
        # By year
        cursor.execute('''
            SELECT year, COUNT(*) as count 
            FROM regulations 
            WHERE year IS NOT NULL 
            GROUP BY year 
            ORDER BY year DESC
        ''')
        stats['by_year'] = {row['year']: row['count'] for row in cursor.fetchall()}
        
        # With/without content
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN full_text IS NOT NULL AND full_text != '' THEN 1 END) as with_content,
                COUNT(CASE WHEN full_text IS NULL OR full_text = '' THEN 1 END) as without_content
            FROM regulations
        ''')
        row = cursor.fetchone()
        stats['content_status'] = dict(row)
        
        conn.close()
        return stats
    
    def export_for_web(self, output_dir='../web/public/data'):
        """Export data for web application"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Export all regulations
        cursor.execute('''
            SELECT id, regulation_type, number, year, title, subject, 
                   filename, date_enacted, status, full_text, page_count
            FROM regulations
            ORDER BY regulation_type, year DESC, number DESC
        ''')
        
        regulations = []
        for row in cursor.fetchall():
            regulations.append({
                'id': row['id'],
                'type': row['regulation_type'],
                'number': row['number'],
                'year': row['year'],
                'title': row['title'],
                'subject': row['subject'],
                'filename': row['filename'],
                'dateEnacted': row['date_enacted'],
                'status': row['status'],
                'content': row['full_text'][:50000] if row['full_text'] else '',
                'pageCount': row['page_count']
            })
        
        # Group by type
        by_type = {}
        for reg in regulations:
            reg_type = reg['type']
            if reg_type not in by_type:
                by_type[reg_type] = []
            by_type[reg_type].append(reg)
        
        # Save exports
        with open(output_path / 'regulations.json', 'w', encoding='utf-8') as f:
            json.dump(regulations, f, ensure_ascii=False, indent=2)
        
        with open(output_path / 'regulations-by-type.json', 'w', encoding='utf-8') as f:
            json.dump(by_type, f, ensure_ascii=False, indent=2)
        
        # Search index (lightweight)
        search_docs = [
            {
                'id': r['id'],
                'title': r['title'],
                'type': r['type'],
                'year': r['year'],
                'number': r['number'],
                'content': r['content'][:10000]
            }
            for r in regulations
        ]
        
        with open(output_path / 'search-index.json', 'w', encoding='utf-8') as f:
            json.dump(search_docs, f, ensure_ascii=False, indent=2)
        
        print(f"Exported {len(regulations)} regulations to {output_dir}")
        conn.close()
        
        return len(regulations)


if __name__ == '__main__':
    importer = DatabaseImporter()
    
    # Import from scraped data
    importer.import_from_jsonl()
    
    # Show statistics
    stats = importer.get_statistics()
    print("\nDatabase Statistics:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # Export for web
    importer.export_for_web()
