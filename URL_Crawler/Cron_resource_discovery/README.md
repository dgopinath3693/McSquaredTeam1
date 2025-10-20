## Integrated Product & Content Scraper
This project discovers and scrapes content related to a company's products from its own sites, competitor sites, and third-party domains. It uses DuckDuckGo for URL discovery, crawls pages to extract structured content, and saves the data in a normalized JSON-based content store.

Features
URL Discovery: Automatically searches DuckDuckGo for URLs based on your company name and keywords (e.g., "YourCompany product review").

Content Crawling: Scrapes target URLs using requests and BeautifulSoup.

Data Extraction: Pulls clean text, headings (H1, H2, etc.), and structured data (JSON-LD, Schema.org).

Classification: Automatically classifies URLs as OWNED_BRAND, COMPETITOR, or THIRD_PARTY.

Persistent Storage: Saves all scraped data in a persistent JSON "content store," which is loaded and updated on each run.

Reporting: Exports a full analysis-ready JSON file and a simple .txt list of discovered URLs.

Core Components (Class Roles)
This project is divided into several key components that work together:

1. scrapper.py (The Orchestrator)
This is the main entry point for running the script. It contains the logic for coordinating the discovery, crawling, and storage processes.

ProductDiscoveryEngine: This class acts as the "Scout". Its job is to find relevant URLs. It builds search queries (e.g., "Nike shoes," "Nike Jordans review") and uses DuckDuckGo to find pages. It also classifies each URL it finds (owned, competitor, etc.).

IntegratedProductScraper: This class is the "Manager" or "Orchestrator". It initializes all other components. It takes the list of URLs from the ProductDiscoveryEngine, tells the ContentCrawler to scrape each one, performs simple topic analysis, and then hands the final, structured data to the ContentStore to be saved.

2. crawler.py (The Worker)
ContentCrawler: This class is the "Worker". Its job is to visit a single URL given to it by the manager. It downloads the HTML, parses it with BeautifulSoup, and meticulously extracts all the data (title, text, headings, schema, metrics). It then packages this data into a standardized ContentDocument object.

3. store.py (The Database)
ContentStore: This class is the "Database" or "Archive". It manages a single JSON file (e.g., company_content_store.json) that acts as a simple, persistent database. It loads all existing documents from this file when it starts, saves new or updated documents, and provides methods for retrieving data.

4. schema.py (The Blueprint)
ContentDocument & other Dataclasses: This file is the "Blueprint". It defines the exact structure of the data. Every piece of content scraped by the ContentCrawler is organized into a ContentDocument object. This ensures all data is consistent and normalized before being saved in the ContentStore.
