import pdfplumber
import docx2txt
from pathlib import Path
import json
from tqdm import tqdm
import re


class TextExtractor:
    """Extract text content from downloaded regulation files"""
    
    def __init__(self):
        self.raw_dir = Path('../data/raw/downloads')
        self.processed_dir = Path('../data/processed')
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {
            'processed': 0,
            'failed': 0,
            'by_format': {}
        }
    
    def extract_pdf(self, filepath):
        """Extract text from PDF with structure preservation"""
        result = {
            'format': 'pdf',
            'filepath': str(filepath),
            'filename': filepath.name,
            'pages': [],
            'full_text': '',
            'metadata': {}
        }
        
        try:
            with pdfplumber.open(filepath) as pdf:
                result['page_count'] = len(pdf.pages)
                result['metadata'] = dict(pdf.metadata) if pdf.metadata else {}
                
                for i, page in enumerate(pdf.pages):
                    page_data = {
                        'page_number': i + 1,
                        'text': '',
                        'tables': []
                    }
                    
                    # Extract text
                    text = page.extract_text()
                    if text:
                        page_data['text'] = text
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        page_data['tables'] = tables
                    
                    result['pages'].append(page_data)
                
                # Combine all text
                result['full_text'] = '\n\n'.join(
                    p['text'] for p in result['pages'] if p['text']
                )
                
        except Exception as e:
            result['error'] = str(e)
            raise
        
        return result
    
    def extract_docx(self, filepath):
        """Extract text from DOCX"""
        result = {
            'format': 'docx',
            'filepath': str(filepath),
            'filename': filepath.name,
            'full_text': '',
            'metadata': {}
        }
        
        try:
            text = docx2txt.process(str(filepath))
            result['full_text'] = text
            result['page_count'] = 1  # DOCX doesn't have explicit page count
        except Exception as e:
            result['error'] = str(e)
            raise
        
        return result
    
    def extract_html(self, filepath):
        """Extract text from HTML"""
        from bs4 import BeautifulSoup
        
        result = {
            'format': 'html',
            'filepath': str(filepath),
            'filename': filepath.name,
            'full_text': ''
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                
                # Remove script and style elements
                for script in soup(['script', 'style']):
                    script.decompose()
                
                result['full_text'] = soup.get_text(separator='\n', strip=True)
                result['title'] = soup.title.string if soup.title else ''
        except Exception as e:
            result['error'] = str(e)
            raise
        
        return result
    
    def process_file(self, filepath):
        """Process a single file based on its extension"""
        ext = filepath.suffix.lower()
        
        if ext == '.pdf':
            return self.extract_pdf(filepath)
        elif ext in ['.docx', '.doc']:
            return self.extract_docx(filepath)
        elif ext in ['.html', '.htm']:
            return self.extract_html(filepath)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def process_all(self):
        """Process all files in the raw directory"""
        files = list(self.raw_dir.iterdir())
        
        print(f"Found {len(files)} files to process")
        
        for filepath in tqdm(files, desc="Extracting text"):
            if filepath.is_dir():
                continue
            
            try:
                result = self.process_file(filepath)
                
                # Save processed data
                output_path = self.processed_dir / f"{filepath.stem}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                # Update stats
                self.stats['processed'] += 1
                fmt = result['format']
                self.stats['by_format'][fmt] = self.stats['by_format'].get(fmt, 0) + 1
                
            except Exception as e:
                print(f"Failed to process {filepath.name}: {e}")
                self.stats['failed'] += 1
        
        # Save stats
        with open(self.processed_dir / 'extraction_stats.json', 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        print(f"\nExtraction complete:")
        print(f"  Processed: {self.stats['processed']}")
        print(f"  Failed: {self.stats['failed']}")
        print(f"  By format: {self.stats['by_format']}")
        
        return self.stats


class TextCleaner:
    """Clean and normalize extracted text"""
    
    @staticmethod
    def clean_text(text):
        """Apply cleaning operations to text"""
        if not text:
            return ''
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove page numbers (common patterns)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove header/footer patterns (common in regulations)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip lines that are just page numbers
            if re.match(r'^\d+$', line):
                continue
            # Skip repeated header lines
            if len(line) < 50 and 'menteri' in line.lower() and 'keuangan' in line.lower():
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def extract_metadata(text):
        """Extract metadata from regulation text"""
        metadata = {}
        
        # Look for common patterns
        patterns = {
            'nomor': r'(?:NOMOR|Nomor|No\.?)\s*[.:]?\s*(\d+)',
            'tahun': r'(?:TAHUN|Tahun)\s*[.:]?\s*(\d{4})',
            'tentang': r'(?:TENTANG|Tentang)\s*[.:]?\s*(.+?)(?:\n|DENGAN|Menimbang)',
            'menimbang': r'(?:MENIMBANG|Menimbang)\s*[.:]?\s*(.+?)(?:\n|MENGINGAT|Mengingat)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                metadata[key] = match.group(1).strip()
        
        return metadata


if __name__ == '__main__':
    extractor = TextExtractor()
    extractor.process_all()
