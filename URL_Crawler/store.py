import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import asdict
from collections import Counter
import math
from schema import ContentDocument

class ContentStore:
    """Manages normalized content storage and retrieval with TF-IDF keyword extraction"""
    
    def __init__(self, storage_path: str = "content_store.json"):
        self.storage_path = storage_path
        self.documents: Dict[str, ContentDocument] = {}
        self.load()
    
    def add_document(self, doc: ContentDocument) -> None:
        """Add or update a document in the store"""
        if doc.doc_id in self.documents:
            doc.first_seen = self.documents[doc.doc_id].first_seen
            doc.last_updated = datetime.utcnow().isoformat()
        
        doc.keywords = self._extract_keywords(doc)
        
        self.documents[doc.doc_id] = doc
        self.save()
    
    def _extract_keywords(self, doc: ContentDocument, top_n: int = 15) -> List[str]:
        """Extract top keywords using TF-IDF scoring"""
        # Combine all text content from the document
        # Use clean_text instead of non-existent description/content fields
        heading_texts = " ".join([h.get("text", "") for h in doc.headings]) if doc.headings else ""
        text = " ".join([
            doc.title or "",
            doc.clean_text or "",
            heading_texts
        ]).lower()
        
        # to be determined stopwords list
        stopwords = {}
        
        words = [w.strip('.,!?;:()[]{}\"\'') for w in text.split()]
        words = [w for w in words if w and w not in stopwords and len(w) > 2]
        
        # Calculate Term Frequency (TF)
        word_counts = Counter(words)
        total_words = len(words)
        tf_scores = {word: count / total_words for word, count in word_counts.items()}
        
        # Calculate Inverse Document Frequency (IDF)
        idf_scores = self._calculate_idf()
        
        # Calculate TF-IDF scores
        tfidf_scores = {}
        for word, tf in tf_scores.items():
            idf = idf_scores.get(word, math.log(len(self.documents) + 1))
            tfidf_scores[word] = tf * idf
        
        # Return top N keywords
        top_keywords = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [word for word, score in top_keywords]
    
    def _calculate_idf(self) -> Dict[str, float]:
        """Calculate IDF scores across all documents"""
        if not self.documents:
            return {}
        
        # Count documents containing each word
        word_doc_count = Counter()
        for doc in self.documents.values():
            heading_texts = " ".join([h.get("text", "") for h in doc.headings]) if doc.headings else ""
            text = " ".join([
                doc.title or "",
                doc.clean_text or "",
                heading_texts
            ]).lower()
            unique_words = set(text.split())
            word_doc_count.update(unique_words)
        
        # Calculate IDF: log(total_docs / docs_containing_word)
        total_docs = len(self.documents)
        idf_scores = {
            word: math.log(total_docs / count)
            for word, count in word_doc_count.items()
        }
        
        return idf_scores
    
    def get_by_entity(self, entity_name: str) -> List[ContentDocument]:
        """Get all documents for a specific entity"""
        return [doc for doc in self.documents.values() 
                if doc.entity_name == entity_name]
    
    def get_by_type(self, entity_type: str) -> List[ContentDocument]:
        """Get all documents by entity type"""
        return [doc for doc in self.documents.values() 
                if doc.entity_type == entity_type]
    
    def get_keyword_gaps(self, client_entity: str, competitor_entities: List[str]) -> Dict[str, List[str]]:
        """Identify keywords competitors have that client doesn't"""
        client_docs = self.get_by_entity(client_entity)
        client_keywords = set()
        for doc in client_docs:
            if hasattr(doc, 'keywords') and doc.keywords:
                client_keywords.update(doc.keywords)
        
        gaps = {}
        for competitor in competitor_entities:
            competitor_docs = self.get_by_entity(competitor)
            competitor_keywords = set()
            for doc in competitor_docs:
                if hasattr(doc, 'keywords') and doc.keywords:
                    competitor_keywords.update(doc.keywords)
            
            # Find keywords competitor has that client doesn't
            missing_keywords = competitor_keywords - client_keywords
            if missing_keywords:
                gaps[competitor] = list(missing_keywords)
        
        return gaps
    
    def export_for_analysis(self, entity_name: Optional[str] = None) -> List[Dict]:
        """Export documents as JSON for downstream analysis"""
        docs = self.documents.values()
        if entity_name:
            docs = [d for d in docs if d.entity_name == entity_name]
        
        return [asdict(doc) for doc in docs]
    
    def save(self) -> None:
        """Save store to disk"""
        with open(self.storage_path, 'w') as f:
            json.dump(
                {doc_id: asdict(doc) for doc_id, doc in self.documents.items()},
                f,
                indent=2
            )
    
    def load(self) -> None:
        """Load store from disk"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for doc_id, doc_dict in data.items():
                    self.documents[doc_id] = ContentDocument(**doc_dict)
        except FileNotFoundError:
            pass