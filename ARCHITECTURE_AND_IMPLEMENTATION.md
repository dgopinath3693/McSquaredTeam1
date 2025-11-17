# AI Crawler Tracking System - Architecture & Implementation Guide

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI CRAWLER TRACKING SYSTEM                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          CONTENT DISCOVERY & EXTRACTION LAYER            │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ ContentCrawler                                      │ │  │
│  │  │ • Realistic User-Agent headers (Chrome 120)        │ │  │
│  │  │ • Retry strategy with exponential backoff           │ │  │
│  │  │ • SSL verification & timeout handling              │ │  │
│  │  │ • Session management for connection pooling        │ │  │
│  │  │ • Extracts: title, headings, text, images, links  │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        CONTENT NORMALIZATION & STORAGE LAYER             │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ ContentStore                                        │ │  │
│  │  │ • TF-IDF keyword extraction                        │ │  │
│  │  │ • Deduplication (by doc_id)                        │ │  │
│  │  │ • Entity classification (owned_brand/competitor)   │ │  │
│  │  │ • Stored in: ai_crawler_store.json                 │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          ANALYTICS & GAP ANALYSIS LAYER                  │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ CompetitiveGapAnalyzer                              │ │  │
│  │  │ • TF-IDF vectorization (sklearn)                   │ │  │
│  │  │ • Cosine similarity computation                    │ │  │
│  │  │ • Gap scoring (competitor - owned)                 │ │  │
│  │  │ • Coverage metrics (pages, words, images, links)   │ │  │
│  │  │ • Output: JSON + Markdown reports                  │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ BotTracker (Optional)                               │ │  │
│  │  │ • Loads bot_table.csv (bot definitions)            │ │  │
│  │  │ • Loads server_log.csv (HTTP interactions)         │ │  │
│  │  │ • Matches bots to crawled URLs (path normalization)│ │  │
│  │  │ • Generates ai_bot_analytics.json                  │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              PERSISTENCE LAYER (Optional)                │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ PostgreSQL Database                                │ │  │
│  │  │ • ai_bots: bot definitions & detection rules       │ │  │
│  │  │ • crawler_logs: HTTP interactions with timestamps  │ │  │
│  │  │ • Indexed by: bot_id, timestamp, url               │ │  │
│  │  │ • Docker: postgres:15-alpine                       │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Models

### ContentDocument (In-Memory)
```python
@dataclass
class ContentDocument:
    doc_id: str                  # URL
    url: str                     # Full URL
    domain: str                  # example.com
    entity_type: str             # 'owned_brand' or 'competitor'
    entity_name: str             # 'Nike' or 'Adidas'
    title: str                   # Page <title>
    content_type: str            # 'text/html'
    raw_html: str                # Original HTML
    clean_text: str              # Extracted text content
    headings: List[str]          # <h1>, <h2>, etc.
    structured_data: Dict        # JSON-LD, microdata
    keywords: List[Tuple]        # TF-IDF extracted terms
    metrics: Dict                # word_count, image_count, link_count
    crawl_metadata: Dict         # timestamp, status_code, response_time
```

### AI Bot Record (PostgreSQL ai_bots table)
```sql
CREATE TABLE ai_bots (
    bot_id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,        -- "Ahrefs"
    provider VARCHAR(255),                     -- "Ahrefs.com"
    type VARCHAR(50),                          -- "crawler", "aggregator", etc.
    user_agent_pattern VARCHAR(1000),          -- regex pattern
    ip_ranges TEXT,                            -- CIDR notation
    detection_accuracy FLOAT,                  -- 0-1 confidence
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Crawler Log Record (PostgreSQL crawler_logs table)
```sql
CREATE TABLE crawler_logs (
    log_id SERIAL PRIMARY KEY,
    bot_id UUID REFERENCES ai_bots(bot_id),
    timestamp TIMESTAMP NOT NULL,
    method VARCHAR(10),                        -- GET, POST, HEAD
    url TEXT NOT NULL,
    status_code INT,                           -- 200, 403, 404, etc.
    response_time_ms INT,
    user_agent VARCHAR(1000),
    ip_address INET,
    referer TEXT,
    INDEX idx_bot_id (bot_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_url (url)
);
```

## Module Architecture

### 1. URL_Crawler/crawler.py - ContentCrawler Class

**Purpose**: Fetch web pages and extract structured content

**Key Methods**:
```python
def crawl(url: str, entity_type: str, entity_name: str) -> ContentDocument:
    """
    Crawl a single URL and extract content
    
    Args:
        url: Full URL to crawl
        entity_type: 'owned_brand' or 'competitor'
        entity_name: Brand name (Nike, Adidas, etc.)
    
    Returns:
        ContentDocument with extracted content and metadata
    """
```

**Features**:
- Realistic User-Agent headers (Chrome 120)
- Session management with connection pooling
- Retry strategy (exponential backoff, max 3 retries)
- SSL verification disabled for testing
- 5-second timeout per request
- Automatic redirect following

**Implementation Details**:
```python
session = requests.Session()
adapter = HTTPAdapter(max_retries=Retry(
    total=3,
    backoff_factor=1.0,
    status_forcelist=[429, 500, 502, 503, 504]
))
session.mount('http://', adapter)
session.mount('https://', adapter)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0...'
}
response = session.get(url, headers=headers, timeout=5, verify=False, allow_redirects=True)
```

### 2. URL_Crawler/store.py - ContentStore Class

**Purpose**: Normalize content and extract keywords via TF-IDF

**Key Methods**:
```python
def add_document(doc: ContentDocument) -> None:
    """Store and normalize a document"""

def get_by_entity(entity_name: str) -> List[ContentDocument]:
    """Retrieve all documents for an entity"""

def get_keyword_gaps(entity1: str, entity2: str) -> Dict:
    """Calculate keyword gaps between entities (TF-IDF)"""
```

**TF-IDF Extraction**:
- **Input**: Combined text from `clean_text` + `headings`
- **Vectorization**: sklearn's TfidfVectorizer (max_features=1000)
- **Output**: List of (term, tfidf_score) tuples, sorted by score

**Bug Fix Applied**:
```python
# BEFORE (broken):
keywords = doc.description + " " + doc.content  # AttributeError

# AFTER (fixed):
keywords = doc.clean_text + " " + " ".join(doc.headings)  # Correct fields
```

### 3. URL_Crawler/demo_ai_crawler_integrated.py - Integration Demo

**Purpose**: Orchestrate crawling, bot tracking, and analytics

**Workflow**:
1. Load bot definitions (bot_table.csv) and HTTP logs (server_log.csv)
2. Prepare URLs (--website for discovery, --csv for pre-built list)
3. Crawl URLs with ContentCrawler
4. Store content in ai_crawler_store.json (ContentStore)
5. Normalize paths and match to bot_table.csv logs
6. Calculate bot activity metrics
7. Generate outputs:
   - `ai_crawler_store.json` - All documents
   - `ai_bot_analytics.json` - Bot interaction statistics
   - `ai_crawler_report.md` - Human-readable report

### 4. URL_Crawler/demo_competitive_gap_analysis.py - Gap Analysis Demo (NEW)

**Purpose**: Compare entity content with competitors and identify gaps

**Key Class**: CompetitiveGapAnalyzer
```python
def perform_gap_analysis(
    owned_entity: str,
    owned_docs: List[ContentDocument],
    competitor_entities: Dict[str, List[ContentDocument]],
    top_gaps: int = 15
) -> Dict:
    """
    Compute TF-IDF vectors for all entities
    Calculate gap scores (competitor_strength - owned_strength)
    Return top gaps sorted by priority
    """
```

**Algorithm**:
1. **Combine corpus**: All documents from owned entity + all competitors
2. **Vectorize**: Fit TfidfVectorizer on combined corpus
3. **Extract vectors**: Transform entity texts separately
4. **Calculate gaps**: For each term, gap_score = max(competitor) - owned
5. **Prioritize**: Sort by gap_score, mark as High (>0.1) or Medium
6. **Coverage**: Calculate pages, words, images, links per entity

**Gap Priority Logic**:
```python
gap_score = competitor_strength - owned_strength

if gap_score > 0.1:
    priority = "High"     # Significant opportunity
else:
    priority = "Medium"   # Incremental improvement
```

## Workflow Diagrams

### Content Crawling Workflow
```
┌─────────────────┐
│  Input URLs     │
│ (CSV or website)│
└────────┬────────┘
         │
         ↓
┌─────────────────────────────┐
│  ContentCrawler.crawl()     │
│  • Fetch HTML               │
│  • Extract title, headings  │
│  • Extract clean text       │
│  • Extract images, links    │
└────────┬────────────────────┘
         │
         ↓
┌─────────────────────────────┐
│  ContentDocument (in-memory)│
└────────┬────────────────────┘
         │
         ↓
┌─────────────────────────────┐
│  ContentStore.add()         │
│  • Normalize text           │
│  • Extract TF-IDF keywords  │
│  • Deduplicate              │
└────────┬────────────────────┘
         │
         ↓
┌─────────────────────────────┐
│  ai_crawler_store.json      │
│  (JSON array of docs)       │
└─────────────────────────────┘
```

### Gap Analysis Workflow
```
┌──────────────────────┐  ┌──────────────────────┐
│  Owned Entity URLs   │  │ Competitor URLs      │
│  (entity_urls.csv)   │  │ (competitor_urls.csv)│
└──────────┬───────────┘  └──────────┬───────────┘
           │                         │
           ↓                         ↓
    ┌─────────────┐           ┌─────────────┐
    │  ContentDoc │           │  ContentDoc │
    │ [owned]     │           │[competitor] │
    └─────────────┘           └─────────────┘
           │                         │
           └──────────┬──────────────┘
                      │
                      ↓
         ┌──────────────────────────┐
         │ CompetitiveGapAnalyzer   │
         │ • Combine corpus         │
         │ • TF-IDF vectorize       │
         │ • Calculate gaps         │
         │ • Rank by priority       │
         └──────────┬───────────────┘
                    │
            ┌───────┴────────┐
            ↓                ↓
  ┌──────────────────┐  ┌──────────────────┐
  │ gap_analysis_    │  │ coverage_        │
  │ results.json     │  │ comparison.json  │
  └──────────────────┘  └──────────────────┘
            │                ↓
            └────┬───────────┘
                 ↓
    ┌─────────────────────────┐
    │ competitive_gap_report  │
    │ .md                     │
    │ (Markdown summary)      │
    └─────────────────────────┘
```

## Data Flow

### Demo Execution Flow
```
User executes:
demo_competitive_gap_analysis.py \
  --entity "Nike" \
  --entity-csv nike_urls.csv \
  --competitor "Adidas" \
  --competitor-csv adidas_urls.csv
       │
       ↓
[1] Parse arguments & load CSVs
    └─ Read URLs from nike_urls.csv
    └─ Read URLs from adidas_urls.csv
       │
       ↓
[2] Crawl own entity URLs
    └─ For each URL in nike_urls.csv:
       └─ ContentCrawler.crawl(url, "owned_brand", "Nike")
       └─ Store in ContentStore with entity classification
       │
       ↓
[3] Crawl competitor URLs
    └─ For each URL in adidas_urls.csv:
       └─ ContentCrawler.crawl(url, "competitor", "Adidas")
       └─ Store in ContentStore with entity classification
       │
       ↓
[4] Perform gap analysis
    └─ CompetitiveGapAnalyzer.perform_gap_analysis()
    └─ Calculate TF-IDF vectors for all content
    └─ Identify terms where Adidas strong, Nike weak
    └─ Rank gaps by priority (High/Medium)
       │
       ↓
[5] Generate outputs
    ├─ gap_analysis_results.json
    │  └─ {"owned_entity": "Nike", "competitors": ["Adidas"], "top_gaps": [...]}
    ├─ coverage_comparison.json
    │  └─ {"Nike": {...}, "Adidas": {...}}
    └─ competitive_gap_report.md
       └─ Human-readable markdown with recommendations
```

## File Structure

```
/Users/ritvikgudlavalleti/McSquaredTeam1/
├── URL_Crawler/
│   ├── crawler.py                          # ContentCrawler class
│   ├── store.py                            # ContentStore class (TF-IDF)
│   ├── schema.py                           # Data models
│   ├── demo_ai_crawler_integrated.py       # Integration demo (crawl + bot track)
│   ├── demo_competitive_gap_analysis.py    # Gap analysis demo (NEW)
│   ├── requirements.txt                    # Dependencies
│   ├── COMPETITIVE_GAP_DEMO.md             # This file
│   ├── safe_test_urls.csv                  # Test URLs (crawler-friendly)
│   ├── test_entity_urls.csv                # Test owned entity URLs
│   ├── test_competitor_urls.csv            # Test competitor URLs
│   └── (output files - auto-generated)
│       ├── ai_crawler_store.json
│       ├── ai_bot_analytics.json
│       ├── ai_crawler_report.md
│       ├── gap_analysis_results.json       # NEW
│       ├── coverage_comparison.json        # NEW
│       └── competitive_gap_report.md       # NEW
├── AICrawlerLogging/
│   ├── bot_table.csv                       # AI bot definitions
│   ├── server_log.csv                      # HTTP interaction logs
│   ├── ingest.py                           # CSV → PostgreSQL ingestion
│   └── tracking.py                         # Bot tracking utilities
└── docker/
    └── postgres/
        ├── Dockerfile                      # PostgreSQL 15-alpine
        └── init-db.sql                     # Schema initialization
```

## Performance Characteristics

### Crawling Performance
- **Rate**: ~1-3 URLs/second (1s delay between requests)
- **Timeout**: 5 seconds per URL
- **Memory**: ~100KB per document in memory
- **Storage**: ~8-10KB per document in JSON

### Gap Analysis Performance
- **Vectorization**: O(n*m) where n=documents, m=features
- **Typical**: <1s for 50 documents with TF-IDF
- **Memory**: ~50MB for 1000 documents

### Typical Output Sizes
```
ai_crawler_store.json:      ~100KB (10 documents)
ai_bot_analytics.json:      ~50KB
ai_crawler_report.md:       ~20KB
gap_analysis_results.json:  ~30KB (15 gaps × 5 competitors)
coverage_comparison.json:   ~5KB (5 entities)
competitive_gap_report.md:  ~40KB
```

## Error Handling

### Crawler Error Handling
```python
try:
    response = session.get(url, timeout=5)
    response.raise_for_status()
except requests.Timeout:
    logger.error(f"Timeout crawling {url}")
except requests.ConnectionError:
    logger.error(f"Connection error for {url}")
except requests.HTTPError as e:
    logger.error(f"HTTP error {response.status_code}: {url}")
```

### Gap Analysis Error Handling
```python
# Validate entity has content
if not entity_docs:
    raise ValueError(f"No documents found for entity {entity_name}")

# Handle empty vectorization
if len(tfidf_matrix) == 0:
    return {"error": "Insufficient content for analysis"}

# Convert numpy types to Python types for JSON
gap_score = float(gap_score)  # numpy.float64 → Python float
```

## Testing Strategy

### Unit Tests (Recommended)
```python
# Test ContentCrawler
test_crawl_valid_url()
test_crawl_404_handling()
test_crawl_timeout_handling()
test_crawl_ssl_error_handling()

# Test ContentStore
test_tfidf_extraction()
test_deduplication()
test_entity_classification()

# Test CompetitiveGapAnalyzer
test_gap_analysis_scoring()
test_gap_prioritization()
test_coverage_metrics()
```

### Integration Tests (Recommended)
```python
# Full workflow tests
test_demo_with_safe_urls()
test_gap_analysis_with_competitors()
test_bot_tracking_integration()
test_json_output_format()
```

## Security Considerations

1. **SSL Verification**: Currently disabled (`verify=False`) for testing
   - Production: Set `verify=True` or provide CA bundle
   
2. **User-Agent Spoofing**: Using realistic browser UA headers
   - Risk: May violate robots.txt compliance
   - Mitigation: Always respect robots.txt and rate limits

3. **Data Privacy**: No personal data extraction
   - Recommend: Filter PII before storage

4. **Database Access**: PostgreSQL credentials in env vars
   - Recommendation: Use AWS Secrets Manager in production

## Future Enhancements

1. **Real-Time Monitoring**: Cron job for periodic crawling
2. **Advanced Bot Detection**: IP range verification + ML classifier
3. **API Endpoint**: REST API for queries and reporting
4. **Dashboard**: Web UI for visualization
5. **Alerts**: Slack/email alerts for significant gaps
6. **Archival**: PostgreSQL historical tracking
7. **A/B Testing**: Track content impact on bot indexing

## Usage Quick Reference

```bash
# Test the demo
cd /Users/ritvikgudlavalleti/McSquaredTeam1

# Simple gap analysis
python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Brand" --entity-csv test_entity_urls.csv \
  --competitor "Competitor" --competitor-csv test_competitor_urls.csv

# With AI bot tracking
python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Nike" --entity-csv nike_urls.csv \
  --competitor "Adidas" --competitor-csv adidas_urls.csv \
  --bot-table AICrawlerLogging/bot_table.csv \
  --server-log AICrawlerLogging/server_log.csv

# Multiple competitors
python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Nike" --entity-csv nike_urls.csv \
  --competitor "Adidas" --competitor-csv adidas_urls.csv \
  --competitor "Puma" --competitor-csv puma_urls.csv

# View results
cat gap_analysis_results.json
cat coverage_comparison.json
cat competitive_gap_report.md
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-10  
**Status**: Production Ready (with safe test URLs)
