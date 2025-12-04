import json
import re
import math
from collections import Counter
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from store import ContentStore
except ImportError:
    print("Warning: store.py not found, using fallback data structure")

    class ContentStore:
        def __init__(self, path="content_store.json"):
            self.documents = {}

        def get_by_type(self, entity_type):
            return []

        def get_by_entity(self, entity_name):
            return []


def simple_tokenize(text):
    """Basic tokenization without external dependencies"""
    if not text:
        return []
    return re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())


def calculate_tf_idf(documents):
    """Simple TF-IDF calculation without scikit-learn"""
    doc_freq = Counter()
    all_docs_tokens = []

    for doc in documents:
        if doc.clean_text:
            tokens = simple_tokenize(doc.clean_text)
            all_docs_tokens.append(tokens)
            doc_freq.update(set(tokens))

    tfidf_scores = []
    total_docs = len(all_docs_tokens)

    for tokens in all_docs_tokens:
        tf = Counter(tokens)
        doc_scores = {}

        for word, count in tf.items():
            tf_score = count / len(tokens) if tokens else 0
            idf_score = math.log(total_docs / (doc_freq[word] + 1)) + 1
            doc_scores[word] = tf_score * idf_score

        tfidf_scores.append(doc_scores)

    return tfidf_scores, list(doc_freq.keys())


def detect_content_gaps_simple(competitor_docs, brand_docs, top_k=10):
    """Detect content gaps using simple TF-IDF comparison"""
    if not competitor_docs:
        return []

    competitor_scores, vocabulary = calculate_tf_idf(competitor_docs)
    brand_scores, _ = calculate_tf_idf(brand_docs)

    avg_competitor_scores = {}
    for word in vocabulary:
        scores = [doc.get(word, 0) for doc in competitor_scores]
        avg_competitor_scores[word] = sum(scores) / len(scores) if scores else 0

    avg_brand_scores = {}
    for word in vocabulary:
        scores = [doc.get(word, 0) for doc in brand_scores]
        avg_brand_scores[word] = sum(scores) / len(scores) if scores else 0

    gaps = []
    for word in vocabulary:
        comp_score = avg_competitor_scores[word]
        brand_score = avg_brand_scores.get(word, 0)

        if comp_score > 0.01 and brand_score < comp_score * 0.5:
            gap_score = comp_score - brand_score
            gaps.append((word, gap_score, comp_score, brand_score))

    gaps.sort(key=lambda x: x[1], reverse=True)
    return [gap[0] for gap in gaps[:top_k]]


def load_content_from_store(store_path="content_store.json"):
    """Load content from ContentStore"""
    try:
        store = ContentStore(store_path)
        competitor_docs = store.get_by_type("competitor")
        brand_docs = store.get_by_type("owned_brand")
        return competitor_docs, brand_docs
    except Exception as e:
        print(f"Error loading content from store: {e}")
        return [], []


def classify_and_prioritize_gaps(gap_terms, competitor_docs):
    """Classify and prioritize gap terms"""
    if not gap_terms:
        return []

    results = []
    all_competitor_text = " ".join([doc.clean_text for doc in competitor_docs if doc.clean_text])
    all_words = simple_tokenize(all_competitor_text)
    word_freq = Counter(all_words)
    total_words = len(all_words)

    for term in gap_terms:
        count = word_freq.get(term.lower(), 0)
        frequency_percent = (count / total_words * 100) if total_words > 0 else 0

        if count > 15 and frequency_percent > 0.1:
            priority = "High"
        elif count > 8 and frequency_percent > 0.05:
            priority = "Medium"
        else:
            priority = "Low"

        competitors_using = set()
        for doc in competitor_docs:
            if doc.clean_text and term.lower() in doc.clean_text.lower():
                competitors_using.add(doc.entity_name)

        results.append({
            "term": term,
            "count": count,
            "frequency_percent": round(frequency_percent, 3),
            "priority": priority,
            "competitors_using": list(competitors_using),
            "competitor_count": len(competitors_using)
        })

    results.sort(key=lambda x: (x["priority"], x["count"]), reverse=True)
    return results


def analyze_content_coverage():
    """Analyze overall content coverage"""
    try:
        store = ContentStore()
        brand_docs = store.get_by_type("owned_brand")
        competitor_docs = store.get_by_type("competitor")

        coverage = {
            "brand_pages": len(brand_docs),
            "competitor_pages": len(competitor_docs),
            "total_brand_words": sum(len(simple_tokenize(doc.clean_text)) for doc in brand_docs if doc.clean_text),
            "total_competitor_words": sum(len(simple_tokenize(doc.clean_text)) for doc in competitor_docs if doc.clean_text),
            "brand_entities": list(set(doc.entity_name for doc in brand_docs)),
            "competitor_entities": list(set(doc.entity_name for doc in competitor_docs))
        }

        return coverage
    except Exception as e:
        print(f"Error analyzing coverage: {e}")
        return {}


def main():
    print("Starting Simplified Content Gap Analysis...")

    competitor_docs, brand_docs = load_content_from_store()

    if not competitor_docs:
        print("No competitor content found in store")
        print("Please run the crawler first to populate the content store")
        return

    print(f"Loaded {len(competitor_docs)} competitor documents")
    print(f"Loaded {len(brand_docs)} brand documents")

    gap_terms = detect_content_gaps_simple(competitor_docs, brand_docs, top_k=15)

    if not gap_terms:
        print("No gap terms identified")
        return

    print(f"Identified {len(gap_terms)} potential gap terms")

    gaps = classify_and_prioritize_gaps(gap_terms, competitor_docs)
    coverage = analyze_content_coverage()

    results = {
        "content_gaps": gaps,
        "coverage_analysis": coverage,
        "summary": {
            "total_gaps_identified": len(gaps),
            "high_priority_gaps": len([g for g in gaps if g["priority"] == "High"]),
            "medium_priority_gaps": len([g for g in gaps if g["priority"] == "Medium"]),
            "low_priority_gaps": len([g for g in gaps if g["priority"] == "Low"])
        }
    }

    print("\n" + "=" * 50)
    print("GAP ANALYSIS RESULTS")
    print("=" * 50)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
