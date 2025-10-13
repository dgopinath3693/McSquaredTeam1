import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import asdict
from schema import ContentDocument

class ContentStore:
    """Manages normalized content storage and retrieval"""
    
    def __init__(self, storage_path: str = "content_store.json"):
        self.storage_path = storage_path
        self.documents: Dict[str, ContentDocument] = {}
        self.load()
    
    def add_document(self, doc: ContentDocument) -> None:
        """Add or update a document in the store"""
        if doc.doc_id in self.documents:
            # Update existing document
            doc.first_seen = self.documents[doc.doc_id].first_seen
            doc.last_updated = datetime.utcnow().isoformat()
        
        self.documents[doc.doc_id] = doc
        self.save()
    
    def get_by_entity(self, entity_name: str) -> List[ContentDocument]:
        """Get all documents for a specific entity"""
        return [doc for doc in self.documents.values() 
                if doc.entity_name == entity_name]
    
    def get_by_type(self, entity_type: str) -> List[ContentDocument]:
        """Get all documents by entity type"""
        return [doc for doc in self.documents.values() 
                if doc.entity_type == entity_type]
    
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
