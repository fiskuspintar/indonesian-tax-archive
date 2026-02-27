import scrapy
from scrapy.http import Request, FormRequest
from scrapy.selector import Selector
import re
from slugify import slugify
from urllib.parse import urljoin, parse_qs, urlparse
import json

class OrtaxRegulationSpider(scrapy.Spider):
    """
    Spider for scraping Indonesian tax regulations from Ortax Data Center.
    Target: https://datacenter.ortax.org/ortax/aturan/list
    """
    
    name = 'ortax_regulations'
    allowed_domains = ['datacenter.ortax.org', 'ortax.org']
    
    # Base URL
    base_url = 'https://datacenter.ortax.org/ortax/aturan/list'
    
    # Regulation type mapping for standardized naming
    REGULATION_TYPES = {
        'UUD 1945': 'UUD 1945',
        'UNDANG-UNDANG DASAR': 'UUD 1945',
        'TAP MPR': 'Tap MPR',
        'KETETAPAN MPR': 'Tap MPR',
        'UNDANG-UNDANG': 'UU',
        'UU': 'UU',
        'PERPU': 'PERPU',
        'PERATURAN PEMERINTAH PENGGANTI UNDANG-UNDANG': 'PERPU',
        'PERATURAN PEMERINTAH': 'PP',
        'PP': 'PP',
        'PERATURAN PRESIDEN': 'Perpres',
        'PERPRES': 'Perpres',
        'PERATURAN MENTERI KEUANGAN': 'Peraturan Menteri Keuangan',
        'PMK': 'Peraturan Menteri Keuangan',
        'KEPUTUSAN MENTERI KEUANGAN': 'Keputusan Menteri Keuangan',
        'KMK': 'Keputusan Menteri Keuangan',
        'PERATURAN DIREKTUR JENDERAL PAJAK': 'Peraturan Direktur Jenderal Pajak',
        'PERATURAN DIRJEN PAJAK': 'Peraturan Direktur Jenderal Pajak',
        'KETETAPAN DIREKTUR JENDERAL PAJAK': 'Ketetapan Direktur Jenderal Pajak',
        'KETETAPAN DIRJEN PAJAK': 'Ketetapan Direktur Jenderal Pajak',
        'SURAT EDARAN DIREKTUR JENDERAL PAJAK': 'Surat Edaran Dirjen Pajak',
        'SURAT EDARAN DIRJEN PAJAK': 'Surat Edaran Dirjen Pajak',
        'SE DIRJEN PAJAK': 'Surat Edaran Dirjen Pajak',
    }
    
    # Required regulation types for validation
    REQUIRED_TYPES = [
        'UUD 1945',
        'Tap MPR', 
        'UU',
        'PERPU',
        'PP',
        'Perpres',
        'Peraturan Menteri Keuangan',
        'Keputusan Menteri Keuangan',
        'Peraturan Direktur Jenderal Pajak',
        'Ketetapan Direktur Jenderal Pajak',
        'Surat Edaran Dirjen Pajak',
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats = {
            'total_found': 0,
            'by_type': {},
            'download_success': 0,
            'download_failed': 0,
        }
    
    def start_requests(self):
        """Start with the main listing page"""
        yield Request(
            url=self.base_url,
            callback=self.parse_list,
            meta={'page': 1}
        )
    
    def parse_list(self, response):
        """Parse the regulation listing page"""
        self.logger.info(f"Parsing page: {response.url}")
        
        # Try multiple selector patterns for regulation items
        # Pattern 1: Table rows
        rows = response.css('table tr, .table tr, .data-list tr')
        
        # Pattern 2: Card/list items
        if not rows:
            rows = response.css('.regulation-item, .item-regulation, .list-item, .card')
        
        # Pattern 3: Generic article/div items
        if not rows:
            rows = response.css('article, .post, .entry')
        
        self.logger.info(f"Found {len(rows)} potential regulation items")
        
        for row in rows:
            # Skip header rows
            if self.is_header_row(row):
                continue
            
            regulation = self.extract_regulation_data(row, response)
            if regulation:
                self.stats['total_found'] += 1
                reg_type = regulation.get('regulation_type', 'Unknown')
                self.stats['by_type'][reg_type] = self.stats['by_type'].get(reg_type, 0) + 1
                
                yield regulation
                
                # Follow detail page if URL available
                if regulation.get('detail_url'):
                    yield Request(
                        url=regulation['detail_url'],
                        callback=self.parse_detail,
                        meta={'regulation': regulation}
                    )
        
        # Follow pagination
        yield from self.handle_pagination(response)
    
    def is_header_row(self, row):
        """Check if row is a table header"""
        header_indicators = ['th', 'thead', '.header', '.thead']
        for indicator in header_indicators:
            if row.css(indicator):
                return True
        
        text = row.get().lower()
        header_texts = ['no', 'nomor', 'jenis', 'tipe', 'tentang', 'download', 'action']
        if all(h in text for h in header_texts[:3]):
            return True
        
        return False
    
    def extract_regulation_data(self, row, response):
        """Extract regulation data from a listing row"""
        regulation = {}
        
        # Extract regulation type
        reg_type = self.extract_field(row, [
            '.type::text', '.jenis::text', '.category::text',
            'td:nth-child(2)::text', 'td:nth-child(1)::text',
            '.reg-type::text', '[data-field="type"]::text'
        ])
        
        # Extract number
        number = self.extract_field(row, [
            '.number::text', '.nomor::text', '.no::text',
            'td:nth-child(3)::text', 'td:nth-child(2)::text',
            '.reg-number::text', '[data-field="number"]::text'
        ])
        
        # Extract year
        year = self.extract_field(row, [
            '.year::text', '.tahun::text',
            'td:nth-child(4)::text', 'td:nth-child(3)::text',
            '.reg-year::text', '[data-field="year"]::text'
        ])
        
        # Extract subject/title
        subject = self.extract_field(row, [
            '.subject::text', '.tentang::text', '.title::text', '.judul::text',
            'td:nth-child(5)::text', 'td:nth-child(4)::text',
            '.reg-subject::text', '[data-field="subject"]::text',
            'a::text', 'h3::text', 'h4::text'
        ])
        
        # Extract detail page URL
        detail_url = row.css('a::attr(href)').get('')
        if detail_url:
            detail_url = urljoin(response.url, detail_url)
        
        # Extract download URL
        download_url = row.css('a[href*="download"]::attr(href), .download::attr(href)').get('')
        if download_url:
            download_url = urljoin(response.url, download_url)
        
        # Skip if no meaningful data found
        if not any([reg_type, number, subject]):
            return None
        
        # Normalize regulation type
        normalized_type = self.normalize_reg_type(reg_type)
        
        # Generate standardized filename
        filename = self.generate_filename(normalized_type, number, year, subject)
        
        regulation = {
            'regulation_type_raw': reg_type,
            'regulation_type': normalized_type,
            'number': self.clean_number(number),
            'year': self.clean_year(year),
            'subject': subject.strip() if subject else '',
            'filename': filename,
            'detail_url': detail_url,
            'download_url': download_url,
            'source_url': response.url,
            'page': response.meta.get('page', 1),
        }
        
        return regulation
    
    def extract_field(self, selector, patterns):
        """Try multiple CSS patterns to extract a field"""
        for pattern in patterns:
            value = selector.css(pattern).get('').strip()
            if value:
                return value
        return ''
    
    def normalize_reg_type(self, raw_type):
        """Map raw regulation type to standardized naming"""
        if not raw_type:
            return 'Unknown'
        
        raw_clean = raw_type.strip().upper()
        
        # Direct mapping
        for key, value in self.REGULATION_TYPES.items():
            if key in raw_clean:
                return value
        
        # Pattern matching for partial matches
        if 'MENTERI KEUANGAN' in raw_clean:
            if 'KEPUTUSAN' in raw_clean:
                return 'Keputusan Menteri Keuangan'
            return 'Peraturan Menteri Keuangan'
        
        if 'DIRJEN PAJAK' in raw_clean or 'DIREKTUR JENDERAL PAJAK' in raw_clean:
            if 'SURAT EDARAN' in raw_clean:
                return 'Surat Edaran Dirjen Pajak'
            if 'KETETAPAN' in raw_clean:
                return 'Ketetapan Direktur Jenderal Pajak'
            return 'Peraturan Direktur Jenderal Pajak'
        
        return raw_type.strip()
    
    def clean_number(self, number):
        """Clean and normalize regulation number"""
        if not number:
            return ''
        # Remove common prefixes
        cleaned = re.sub(r'^(no\.?|nomor)\s*', '', number.strip(), flags=re.IGNORECASE)
        return cleaned.strip()
    
    def clean_year(self, year):
        """Clean and validate year"""
        if not year:
            return None
        # Extract 4-digit year
        match = re.search(r'\b(19|20)\d{2}\b', str(year))
        if match:
            return int(match.group(1))
        return None
    
    def generate_filename(self, reg_type, number, year, subject):
        """
        Generate filename following strict convention:
        [Regulation Type]_[Regulation Number]_[Subject]
        """
        # Clean subject for filename
        if subject:
            subject_clean = slugify(subject, separator='_', max_length=100)
        else:
            subject_clean = 'unknown'
        
        # Format number with year
        if year and number:
            number_formatted = f"Nomor {number} Tahun {year}"
        elif number:
            number_formatted = f"Nomor {number}"
        elif year:
            number_formatted = f"Tahun {year}"
        else:
            number_formatted = 'unknown'
        
        # Build filename
        filename = f"{reg_type}_{number_formatted}_{subject_clean}"
        
        # Remove any problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        return filename
    
    def handle_pagination(self, response):
        """Handle pagination - find and follow next page links"""
        current_page = response.meta.get('page', 1)
        
        # Common pagination patterns
        next_selectors = [
            'a.next::attr(href)',
            'a[rel="next"]::attr(href)',
            '.pagination .active + li a::attr(href)',
            '.pagination a[aria-label="Next"]::attr(href)',
            'a:contains("Next")::attr(href)',
            'a:contains("Berikutnya")::attr(href)',
        ]
        
        for selector in next_selectors:
            next_url = response.css(selector).get('')
            if next_url:
                yield Request(
                    url=urljoin(response.url, next_url),
                    callback=self.parse_list,
                    meta={'page': current_page + 1}
                )
                break
        
        # Also try page number increment
        next_page_url = response.url.replace(f'page={current_page}', f'page={current_page + 1}')
        if next_page_url != response.url and current_page < 100:  # Safety limit
            yield Request(
                url=next_page_url,
                callback=self.parse_list,
                meta={'page': current_page + 1}
            )
    
    def parse_detail(self, response):
        """Parse detail page for additional information"""
        regulation = response.meta.get('regulation', {})
        
        # Extract full text content if available
        content_selectors = [
            '.content::text', '.regulation-content::text',
            '.detail-content::text', 'article::text',
            '.main-content::text', '#content::text'
        ]
        
        for selector in content_selectors:
            content = response.css(selector).get('')
            if content and len(content) > 100:
                regulation['full_text'] = content.strip()
                break
        
        # Look for download links on detail page
        if not regulation.get('download_url'):
            download_selectors = [
                'a[href*=".pdf"]::attr(href)',
                'a[href*="download"]::attr(href)',
                '.download-link::attr(href)',
                'a:contains("Download")::attr(href)',
                'a:contains("Unduh")::attr(href)',
            ]
            
            for selector in download_selectors:
                download_url = response.css(selector).get('')
                if download_url:
                    regulation['download_url'] = urljoin(response.url, download_url)
                    break
        
        yield regulation
    
    def closed(self, reason):
        """Called when spider closes - log statistics"""
        self.logger.info("=" * 50)
        self.logger.info("SCRAPING STATISTICS")
        self.logger.info("=" * 50)
        self.logger.info(f"Total regulations found: {self.stats['total_found']}")
        self.logger.info(f"By type: {json.dumps(self.stats['by_type'], indent=2)}")
        self.logger.info(f"Download success: {self.stats['download_success']}")
        self.logger.info(f"Download failed: {self.stats['download_failed']}")
        self.logger.info("=" * 50)
        
        # Save stats to file
        with open('../data/scraper_stats.json', 'w') as f:
            json.dump(self.stats, f, indent=2)
