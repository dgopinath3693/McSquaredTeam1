"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DomainScoreCalculationCreate(BaseModel):
    """Schema for creating a Domain Score Calculation"""
    brand: str
    score: float
    suggested_action: str


class DomainScoreCalculationResponse(DomainScoreCalculationCreate):
    """Schema for Domain Score Calculation response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ContentGapAnalysisCreate(BaseModel):
    """Schema for creating a Content Gap Analysis"""
    aggregator: str
    keyword: str
    impact: str
    priority: str
    suggested_action: str


class ContentGapAnalysisResponse(ContentGapAnalysisCreate):
    """Schema for Content Gap Analysis response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PromptAnalysisCreate(BaseModel):
    """Schema for creating a Prompt Analysis"""
    prompt: str
    ai_answer: str


class PromptAnalysisResponse(PromptAnalysisCreate):
    """Schema for Prompt Analysis response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
