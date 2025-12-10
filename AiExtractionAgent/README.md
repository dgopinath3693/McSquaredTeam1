# AiExtractionAgent

An AI-powered extraction and summarization agent that leverages Selenium for web automation and Google Generative AI (Gemini) for intelligent content extraction. This component crawls web pages, interacts with JavaScript-heavy content, and extracts/summarizes information using natural language processing.

## Overview

The AiExtractionAgent provides automated web scraping with AI-enhanced content extraction. It uses:

- **Selenium WebDriver**: Automates browser interactions for JavaScript-rendered content
- **Google Gemini API**: Summarizes and extracts key information from page content
- **LLM Processing**: Enhances scraped data with AI insights

## Contents

### Core Files

- **`scrape.py`** - Main AIExtractionAgent class with capabilities:
  - Browser automation using Selenium WebDriver
  - Dynamic content loading and interaction
  - JavaScript rendering support
  - AI-powered content summarization via Gemini API
  - Structured data extraction from web pages
  - Error handling and logging for failed extractions
  - CSV output of extracted responses

- **`clean.py`** - Data cleaning and normalization:
  - Processes scraped and extracted data
  - Handles format inconsistencies
  - Removes noise and duplicates from extraction results
  - Normalizes extracted information for downstream analysis

### Data Files

- **`ai_responses_extracted.csv`** - Output of AI extraction:
  - Extracted information from web pages
  - Structured responses from Gemini API
  - Timestamps of extraction
  - Source URLs

- **`ai_responses_cleaned.csv`** - Cleaned and processed extraction results:
  - Normalized formats
  - Deduplicated entries
  - Quality-filtered responses
  - Ready for analysis and storage

## Setup

### Requirements

- Python 3.8+
- Chrome/Chromium browser installed
- ChromeDriver matching your Chrome version
- Google Generative AI API key

### Installation

```bash
cd AiExtractionAgent
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file with your API key:

```
GEMINI_API_KEY=your_api_key_here
```

Or set as environment variable:

```bash
export GEMINI_API_KEY=your_api_key_here
```

## Usage

### Basic Extraction

```python
from scrape import AIExtractionAgent

# Initialize agent
agent = AIExtractionAgent(
    prompts_csv="PromptAgent/output_prompts_df.csv",
    output_csv="ai_responses_extracted.csv"
)

# Run extraction on pages
agent.extract_and_summarize()
```

### Running from Command Line

```bash
# Extract from prompt list
python3 scrape.py --prompts PromptAgent/output_prompts_df.csv

# Extract and clean
python3 clean.py ai_responses_extracted.csv ai_responses_cleaned.csv
```

## Features

### Web Scraping Capabilities

- **Dynamic Content Loading**: Waits for JavaScript to render before extraction
- **Form Interaction**: Can fill forms and submit for content discovery
- **Click Actions**: Handles click-triggered content loading
- **Element Waiting**: Intelligent waits for specific elements to appear
- **Error Recovery**: Continues with other pages if one fails

### AI-Powered Extraction

- **Gemini Integration**: Uses Google's LLM for understanding and summarization
- **Prompt-Based**: Works with custom prompts from PromptAgent
- **Context Preservation**: Maintains context across multiple pages
- **Structured Output**: Organizes extracted information in CSV format

### Data Quality

- **Logging**: Comprehensive logging of extraction process
- **Error Handling**: Graceful handling of network and parsing errors
- **Deduplication**: Identifies and removes duplicate extractions
- **Validation**: Validates extracted data before output

## Data Model

### Input: Prompts CSV

Expected columns:
- `prompt` - Question or extraction task
- `domain` - Related domain for context
- `metadata` - Additional context for extraction

### Output: Extracted Responses

Columns generated:
- `timestamp` - When extraction occurred
- `url` - Source URL crawled
- `prompt` - Original prompt used
- `response` - AI-extracted/summarized response
- `status` - Success/failure indicator
- `error_message` - If extraction failed

## Integration

### Upstream Dependencies

- **PromptAgent**: Generates prompts used for extraction
- **URL_Crawler**: Provides URLs to extract from

### Downstream Usage

- **ContentGapAnalysis**: Analyzes extracted content for gaps
- **FastAPIApp**: Stores and serves extracted data
- **Analytics**: Generates reports on extraction coverage

## Advanced Configuration

### Selenium Options

```python
agent = AIExtractionAgent()
agent.headless = False          # Show browser window
agent.timeout = 30              # Seconds to wait for elements
agent.implicit_wait = 10        # Implicit wait time
```

### API Configuration

```python
agent.gemini_model = "gemini-2.5-flash"  # Model selection
agent.max_retries = 3                     # API retry attempts
agent.timeout_per_request = 60            # Seconds per request
```

## Output Examples

### Extraction Output

```csv
timestamp,url,prompt,response,status
2025-01-10T10:30:45,https://example.com,What are the main products?,Nike offers...,success
2025-01-10T10:31:20,https://example.com/about,Company history?,Founded in 1964...,success
```

### After Cleaning

```csv
timestamp,url,category,normalized_response,quality_score
2025-01-10T10:30:45,https://example.com,products,Nike-branded footwear and apparel,0.95
2025-01-10T10:31:20,https://example.com/about,history,Established 1964 as Blue Ribbon Sports,0.92
```

## Troubleshooting

### ChromeDriver Issues

```bash
# Install ChromeDriver for your Chrome version
# Download from: https://chromedriver.chromium.org/
# Or install via package manager:
brew install chromedriver  # macOS
```

### Gemini API Errors

- Verify API key is correct and active
- Check rate limits on your Google Cloud project
- Ensure sufficient quota for API calls

### Timeout Issues

- Increase timeout values for slow connections
- Check network connectivity to target sites
- Verify target sites are accessible and not blocking

## Performance Tips

- Use headless mode for faster extraction
- Batch process URLs to parallelize work
- Cache API responses to avoid duplicate calls
- Monitor logs for patterns in failures

## Next Steps

- Add support for additional browser types (Firefox, Safari)
- Implement caching layer for extracted content
- Add preprocessing for better extraction results
- Build visualization dashboard for extraction coverage
