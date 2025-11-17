from datetime import datetime
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass
from enum import Enum

class ContentType(Enum):
    """Types of content being tracked"""
    ARTICLE = "article"
    PRODUCT_PAGE = "product_page"
    FAQ = "faq"
    LANDING_PAGE = "landing_page"
    BLOG_POST = "blog_post"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class EntityType(Enum):
    """Entity relationship to the brand"""
    OWNED_BRAND = "owned_brand"
    COMPETITOR = "competitor"
    THIRD_PARTY = "third_party"


@dataclass
class StructuredData:
    """Extracted structured data (Schema.org, OpenGraph, etc.)"""
    schema_type: Optional[str] = None
    faq_items: List[Dict[str, str]] = None
    product_info: Optional[Dict] = None
    article_metadata: Optional[Dict] = None
    raw_json_ld: Optional[List[Dict]] = None
    
    def __post_init__(self):
        if self.faq_items is None:
            self.faq_items = []
        if self.raw_json_ld is None:
            self.raw_json_ld = []


@dataclass
class ContentMetrics:
    """Content quality and technical metrics"""
    word_count: int = 0
    heading_count: int = 0
    image_count: int = 0
    link_count: int = 0
    has_faq: bool = False
    has_schema: bool = False
    readability_score: Optional[float] = None
    keyword_density: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        if self.keyword_density is None:
            self.keyword_density = {}


@dataclass
class CrawlMetadata:
    """Metadata about the crawl operation"""
    crawled_at: str
    crawler_id: str
    response_code: int
    response_time_ms: int
    content_hash: str
    detected_ai_bots: List[str] = None
    
    def __post_init__(self):
        if self.detected_ai_bots is None:
            self.detected_ai_bots = []


@dataclass
class ContentDocument:
    """Main normalized content document schema"""
    
    # Identity
    doc_id: str  # Unique document identifier
    url: str
    domain: str
    
    # Entity Classification
    entity_type: str  # EntityType enum value
    entity_name: str  # "Nike", "Adidas", "Runner's World", etc.
    
    # Content
    title: str
    content_type: str  # ContentType enum value
    raw_html: str
    clean_text: str
    headings: List[Dict[str, str]]  # [{"level": "h1", "text": "..."}]
    
    # Structured Data
    structured_data: Dict
    
    # Metrics
    metrics: Dict
    
    # Crawl Info
    crawl_metadata: Dict
    
    # Analysis Fields (populated by downstream processes)
    topics: List[str] = None
    entities_mentioned: List[str] = None
    citation_score: Optional[float] = None
    ai_visibility_score: Optional[float] = None
    
    # Timestamps
    first_seen: str = None
    last_updated: str = None

    keywords: List[str] = None
    
    def __post_init__(self):
        if self.topics is None:
            self.topics = []
        if self.entities_mentioned is None:
            self.entities_mentioned = []
        if not self.first_seen:
            self.first_seen = datetime.utcnow().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.utcnow().isoformat()

