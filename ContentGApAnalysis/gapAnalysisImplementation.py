from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

def load_scraped_content(engine):
    with Session(engine) as session:
        competitor_texts = [r.text for r in session.query(ScrapedPage).filter(ScrapedPage.tier != 'OWN')]
        brand_texts = [r.text for r in session.query(ScrapedPage).filter(ScrapedPage.tier == 'OWN')]
    if not brand_texts:
        brand_texts = [""]
    return competitor_texts, brand_texts

def detect_content_gaps(competitor_texts, brand_texts, top_k=10):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=2000)
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

def classify_and_prioritize_gaps(gap_terms):
    gaps = []
    for term in gap_terms:
        priority = "High" if len(term) > 10 else "Medium"
        gaps.append({
            "term": term,
            "priority": priority,
            "impact_reason": "Frequent in competitor content, missing from brand coverage"
        })
    return gaps
