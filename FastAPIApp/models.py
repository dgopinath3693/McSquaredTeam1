"""
Database models/schemas
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func
from database import Base


class DomainScoreCalculation(Base):
    """Domain Score Calculation model"""
    __tablename__ = "domain_score_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(255), nullable=False, index=True)
    score = Column(Float, nullable=False)
    suggested_action = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ContentGapAnalysis(Base):
    """Content Gap Analysis model"""
    __tablename__ = "content_gap_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    aggregator = Column(String(255), nullable=False, index=True)
    keyword = Column(String(255), nullable=False, index=True)
    impact = Column(String(50), nullable=False)
    priority = Column(String(50), nullable=False)
    suggested_action = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PromptAnalysis(Base):
    """Prompt Analysis model"""
    __tablename__ = "prompt_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    ai_answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
