import json
import hashlib
from datetime import datetime
from typing import List, Dict
from dataclasses import asdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from schema import ContentDocument, ContentType, StructuredData, ContentMetrics, CrawlMetadata

class ContentCrawler:
    """Crawls and extracts content from URLs"""
    
    def __init__(self, crawler_id: str = "geo-crawler-v1"):
        self.crawler_id = crawler_id
        self.session = requests.Session()
        
        # Realistic headers to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def crawl(self, url: str, entity_type: str, entity_name: str) -> ContentDocument:
        """
        Crawl a URL and return normalized ContentDocument
        
        Args:
            url: Target URL to crawl
            entity_type: Type of entity (owned_brand, competitor, third_party)
            entity_name: Name of the entity
        
        Returns:
            ContentDocument with all extracted data
        """
        start_time = datetime.utcnow()
        
        try:
            response = self.session.get(
                url, 
                headers=self.headers, 
                timeout=15,
                verify=True,  # SSL verification
                allow_redirects=True
            )
            response.raise_for_status()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract core content
            raw_html = str(response.content.decode('utf-8'))
            clean_text = self._extract_clean_text(soup)
            headings = self._extract_headings(soup)
            title = self._extract_title(soup)
            
            # Extract structured data
            structured_data = self._extract_structured_data(soup)
            
            # Calculate metrics
            metrics = self._calculate_metrics(soup, clean_text, structured_data)
            
            # Generate content hash
            content_hash = hashlib.sha256(clean_text.encode()).hexdigest()
            
            # Create document
            doc = ContentDocument(
                doc_id=self._generate_doc_id(url),
                url=url,
                domain=urlparse(url).netloc,
                entity_type=entity_type,
                entity_name=entity_name,
                title=title,
                content_type=self._detect_content_type(soup, url),
                raw_html=raw_html,
                clean_text=clean_text,
                headings=headings,
                structured_data=asdict(structured_data),
                metrics=asdict(metrics),
                crawl_metadata=asdict(CrawlMetadata(
                    crawled_at=datetime.utcnow().isoformat(),
                    crawler_id=self.crawler_id,
                    response_code=response.status_code,
                    response_time_ms=int(response_time),
                    content_hash=content_hash
                ))
            )
            
            return doc
            
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            raise
    
    def _generate_doc_id(self, url: str) -> str:
        """Generate unique document ID from URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        if soup.title:
            return soup.title.string.strip()
        og_title = soup.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '')
        return ''
    
    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text content"""
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all headings with hierarchy"""
        headings = []
        for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for heading in soup.find_all(level):
                headings.append({
                    'level': level,
                    'text': heading.get_text().strip()
                })
        return headings
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> StructuredData:
        """Extract structured data (JSON-LD, Schema.org, etc.)"""
        structured = StructuredData()
        
        # Extract JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured.raw_json_ld.append(data)
                
                # Parse FAQ schema
                if isinstance(data, dict) and data.get('@type') == 'FAQPage':
                    for item in data.get('mainEntity', []):
                        structured.faq_items.append({
                            'question': item.get('name', ''),
                            'answer': item.get('acceptedAnswer', {}).get('text', '')
                        })
                
                # Store schema type
                if isinstance(data, dict) and '@type' in data:
                    structured.schema_type = data['@type']
                    
            except json.JSONDecodeError:
                pass
        
        return structured
    
    def _calculate_metrics(self, soup: BeautifulSoup, clean_text: str, 
                          structured_data: StructuredData) -> ContentMetrics:
        """Calculate content quality metrics"""
        return ContentMetrics(
            word_count=len(clean_text.split()),
            heading_count=len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            image_count=len(soup.find_all('img')),
            link_count=len(soup.find_all('a')),
            has_faq=len(structured_data.faq_items) > 0,
            has_schema=len(structured_data.raw_json_ld) > 0
        )
    
    def _detect_content_type(self, soup: BeautifulSoup, url: str) -> str:
        """Detect content type from URL and content"""
        url_lower = url.lower()
        
        if '/faq' in url_lower or soup.find('script', type='application/ld+json', 
                                            string=lambda s: s and 'FAQPage' in s):
            return ContentType.FAQ.value
        elif '/blog' in url_lower or '/article' in url_lower:
            return ContentType.BLOG_POST.value
        elif '/product' in url_lower or '/shop' in url_lower:
            return ContentType.PRODUCT_PAGE.value
        elif '/docs' in url_lower or '/documentation' in url_lower:
            return ContentType.DOCUMENTATION.value
        
        return ContentType.OTHER.value
