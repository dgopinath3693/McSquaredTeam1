"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


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
    llm: Optional[str] = None
    prompt: str
    ai_answer: str
    answer_length: Optional[int] = None
    summary_length: Optional[int] = None
    status: Optional[str] = None


class PromptAnalysisResponse(PromptAnalysisCreate):
    """Schema for Prompt Analysis response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PromptAnalysisBulkCreate(BaseModel):
    """Schema for bulk creating Prompt Analysis from CSV"""
    records: List[PromptAnalysisCreate]


# ==================== Domain Score Calculation Schemas ====================

class ScoreBreakdown(BaseModel):
    """Score breakdown by component"""
    crawler_score: float
    gap_analysis_score: float
    bot_analytics_score: float
    extraction_score: float


class ScoreMetadata(BaseModel):
    """Metadata about the score calculation"""
    crawler_docs_count: int
    total_gaps: int
    bot_interactions: int
    extraction_count: int


class DomainScoreRequest(BaseModel):
    """Request schema for calculating domain score"""
    brand: str


class DomainScoreResponse(BaseModel):
    """Response schema for domain score calculation"""
    brand: str
    overall_score: float
    score_breakdown: ScoreBreakdown
    weights: dict
    metadata: ScoreMetadata


class AIRecommendationRequest(BaseModel):
    """Request schema for generating AI recommendations"""
    brand: str
    include_score_calculation: bool = True  # If True, calculates score first


class AIRecommendationResponse(BaseModel):
    """Response schema for AI recommendations"""
    brand: str
    overall_score: Optional[float] = None
    explanation: str
    recommendations: str
    score_breakdown: Optional[ScoreBreakdown] = None
    metadata: Optional[ScoreMetadata] = None
