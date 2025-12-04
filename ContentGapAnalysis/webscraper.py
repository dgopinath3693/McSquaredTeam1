import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urlparse

HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape_text(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
        tag.extract()
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())

def scrape_sites(own_urls, competitor_urls, output_path="scraped_content.json"):
    data = []
    for tier, urls in [("OWN", own_urls), ("COMPETITOR", competitor_urls)]:
        for url in urls:
            print(f"Scraping ({tier}): {url}")
            text = scrape_text(url)
            if text:
                data.append({
                    "url": url,
                    "domain": urlparse(url).netloc,
                    "tier": tier,
                    "text": text
                })
            time.sleep(1)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} pages to {output_path}")
    return data

if __name__ == "__main__":
    own_sites = [
        "https://www.repatha.com/"
    ]
    competitor_sites = [
        "https://www.leqviohcp.com/"
    ]
    scrape_sites(own_sites, competitor_sites)
