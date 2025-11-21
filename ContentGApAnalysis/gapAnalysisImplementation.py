from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

def load_scraped_content(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        pages = json.load(f)
    competitor_texts = [p["text"] for p in pages if p["tier"] == "COMPETITOR"]
    brand_texts = [p["text"] for p in pages if p["tier"] == "OWN"]
    if not brand_texts:
        brand_texts = [""]
    return competitor_texts, brand_texts

def detect_content_gaps(competitor_texts, brand_texts, top_k=10):
    vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
    all_texts = competitor_texts + brand_texts
    tfidf = vectorizer.fit_transform(all_texts)

    competitor_vec = tfidf[:len(competitor_texts)]
    brand_vec = tfidf[len(competitor_texts):]

    similarity = cosine_similarity(competitor_vec, brand_vec)
    avg_similarity = similarity.mean(axis=1)

    gap_indices = avg_similarity.argsort()[:top_k]
    feature_names = vectorizer.get_feature_names_out()
    gap_terms = set()

    for i in gap_indices:
        top_terms = [feature_names[j] for j in competitor_vec[i].toarray().argsort()[0, -10:]]
        gap_terms.update(top_terms)

    return list(gap_terms)

def classify_and_prioritize_gaps(gap_terms, competitor_texts):
    results = []
    all_text = " ".join(competitor_texts).lower()
    for term in gap_terms:
        count = all_text.count(term.lower())
        priority = "High" if count > 10 else "Medium"
        results.append({
            "term": term,
            "count": count,
            "priority": priority
        })
    return results


if __name__ == "__main__":
    competitor_texts, brand_texts = load_scraped_content("scraped_content.json")
    gap_terms = detect_content_gaps(competitor_texts, brand_texts)
    gaps = classify_and_prioritize_gaps(gap_terms, competitor_texts)

    print(json.dumps(gaps, indent=2))
