import os
from pathlib import Path
import requests
from urllib.parse import urlparse
import json
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem


class JsonWriterPipeline:
    """Pipeline to write items to JSON Lines file"""
    
    def __init__(self):
        self.file = None
    
    def open_spider(self, spider):
        output_dir = Path('../data/raw')
        output_dir.mkdir(parents=True, exist_ok=True)
        self.file = open(output_dir / 'regulations.jsonl', 'w', encoding='utf-8')
    
    def close_spider(self, spider):
        if self.file:
            self.file.close()
    
    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(line)
        return item


class RegulationDownloadPipeline:
    """Pipeline to download regulation files (PDF, DOCX)"""
    
    def __init__(self):
        self.download_dir = Path('../data/raw/downloads')
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {'success': 0, 'failed': 0}
    
    def process_item(self, item, spider):
        if not item.get('download_url'):
            spider.logger.debug(f"No download URL for {item.get('filename', 'unknown')}")
            return item
        
        # Determine file extension
        ext = self.get_extension(item['download_url'])
        filename = f"{item['filename']}.{ext}"
        filepath = self.download_dir / filename
        
        # Skip if already downloaded
        if filepath.exists():
            spider.logger.info(f"Already downloaded: {filename}")
            item['local_path'] = str(filepath)
            item['download_status'] = 'already_exists'
            return item
        
        # Download with retry logic
        try:
            spider.logger.info(f"Downloading: {filename}")
            
            response = requests.get(
                item['download_url'],
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,*/*',
                },
                timeout=120,
                stream=True,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Verify content type
            content_type = response.headers.get('Content-Type', '')
            if 'html' in content_type.lower() and ext != 'html':
                spider.logger.warning(f"Got HTML instead of {ext} for {filename}")
                item['download_status'] = 'wrong_content_type'
                return item
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            item['local_path'] = str(filepath)
            item['download_status'] = 'success'
            item['file_size'] = filepath.stat().st_size
            self.stats['success'] += 1
            spider.stats['download_success'] = self.stats['success']
            
            spider.logger.info(f"Downloaded: {filename} ({item['file_size']} bytes)")
            
        except requests.exceptions.RequestException as e:
            item['download_status'] = f'failed: {str(e)}'
            self.stats['failed'] += 1
            spider.stats['download_failed'] = self.stats['failed']
            spider.logger.error(f"Download failed for {filename}: {e}")
        
        except Exception as e:
            item['download_status'] = f'error: {str(e)}'
            self.stats['failed'] += 1
            spider.stats['download_failed'] = self.stats['failed']
            spider.logger.error(f"Unexpected error downloading {filename}: {e}")
        
        return item
    
    def get_extension(self, url):
        """Extract file extension from URL"""
        parsed = urlparse(url.lower())
        path = parsed.path
        
        if '.pdf' in path:
            return 'pdf'
        elif '.docx' in path:
            return 'docx'
        elif '.doc' in path:
            return 'doc'
        elif '.html' in path or '.htm' in path:
            return 'html'
        elif '.txt' in path:
            return 'txt'
        
        # Default to PDF for regulation documents
        return 'pdf'


class ValidationPipeline:
    """Pipeline to validate regulation data"""
    
    REQUIRED_FIELDS = ['regulation_type', 'filename']
    
    def process_item(self, item, spider):
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not item.get(field):
                spider.logger.warning(f"Missing required field '{field}' for item")
                item[field] = 'unknown'
        
        # Validate regulation type is in required list
        required_types = [
            'UUD 1945', 'Tap MPR', 'UU', 'PERPU', 'PP', 'Perpres',
            'Peraturan Menteri Keuangan', 'Keputusan Menteri Keuangan',
            'Peraturan Direktur Jenderal Pajak', 'Ketetapan Direktur Jenderal Pajak',
            'Surat Edaran Dirjen Pajak'
        ]
        
        if item.get('regulation_type') not in required_types:
            spider.logger.debug(f"Unusual regulation type: {item.get('regulation_type')}")
        
        return item
