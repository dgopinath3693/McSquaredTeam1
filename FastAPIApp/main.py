"""
FastAPI application with PostgreSQL database integration
"""
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from config import get_settings
from database import get_db, create_tables
from models import DomainScoreCalculation, ContentGapAnalysis, PromptAnalysis
from schemas import (
    DomainScoreCalculationCreate, DomainScoreCalculationResponse,
    ContentGapAnalysisCreate, ContentGapAnalysisResponse,
    PromptAnalysisCreate, PromptAnalysisResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="McSquared API",
    description="FastAPI application with PostgreSQL database integration",
    version="1.0.0"
)

# Settings
settings = get_settings()


# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        create_tables()
        print("✓ Database tables created successfully")
    except Exception as e:
        print(f"✗ Error creating database tables: {e}")


# ==================== ENDPOINT 1: Domain Score Calculation ====================

@app.post("/domain_score_calculation/", response_model=DomainScoreCalculationResponse, status_code=status.HTTP_201_CREATED)
def create_domain_score(
    domain_score: DomainScoreCalculationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new domain score calculation entry.
    
    Parameters:
    - **brand**: str - Brand name
    - **score**: float - Calculated score
    - **suggested_action**: str - Recommended action based on score
    
    Returns: Created domain score calculation with ID and timestamps
    """
    db_domain_score = DomainScoreCalculation(
        brand=domain_score.brand,
        score=domain_score.score,
        suggested_action=domain_score.suggested_action
    )
    db.add(db_domain_score)
    db.commit()
    db.refresh(db_domain_score)
    return db_domain_score


@app.get("/domain_score_calculation/", response_model=List[DomainScoreCalculationResponse])
def list_domain_scores(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get all domain score calculations with pagination support.
    
    Parameters:
    - **skip**: int - Number of records to skip (default: 0)
    - **limit**: int - Maximum number of records to return (default: 10)
    
    Returns: List of domain score calculations
    """
    domain_scores = db.query(DomainScoreCalculation).offset(skip).limit(limit).all()
    return domain_scores


@app.get("/domain_score_calculation/{score_id}", response_model=DomainScoreCalculationResponse)
def get_domain_score(
    score_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific domain score calculation by ID.
    
    Parameters:
    - **score_id**: int - The ID of the domain score calculation
    
    Returns: Domain score calculation details
    """
    db_domain_score = db.query(DomainScoreCalculation).filter(DomainScoreCalculation.id == score_id).first()
    if not db_domain_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain score calculation with id {score_id} not found"
        )
    return db_domain_score


@app.get("/domain_score_calculation/brand/{brand}", response_model=List[DomainScoreCalculationResponse])
def get_domain_scores_by_brand(
    brand: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get domain score calculations filtered by brand.
    
    Parameters:
    - **brand**: str - Brand name to filter by
    - **skip**: int - Number of records to skip (default: 0)
    - **limit**: int - Maximum number of records to return (default: 10)
    
    Returns: List of domain score calculations for the brand
    """
    domain_scores = db.query(DomainScoreCalculation).filter(DomainScoreCalculation.brand == brand).offset(skip).limit(limit).all()
    return domain_scores


# ==================== ENDPOINT 2: Content Gap Analysis ====================

@app.post("/content_gap_analysis/", response_model=ContentGapAnalysisResponse, status_code=status.HTTP_201_CREATED)
def create_content_gap_analysis(
    gap_analysis: ContentGapAnalysisCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new content gap analysis entry.
    
    Parameters:
    - **aggregator**: str - Aggregator name
    - **keyword**: str - Keyword analyzed
    - **impact**: str - Impact level of the gap
    - **priority**: str - Priority level (e.g., high, medium, low)
    - **suggested_action**: str - Recommended action to address the gap
    
    Returns: Created content gap analysis with ID and timestamps
    """
    db_gap_analysis = ContentGapAnalysis(
        aggregator=gap_analysis.aggregator,
        keyword=gap_analysis.keyword,
        impact=gap_analysis.impact,
        priority=gap_analysis.priority,
        suggested_action=gap_analysis.suggested_action
    )
    db.add(db_gap_analysis)
    db.commit()
    db.refresh(db_gap_analysis)
    return db_gap_analysis


@app.get("/content_gap_analysis/", response_model=List[ContentGapAnalysisResponse])
def list_content_gap_analysis(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get all content gap analysis records with pagination support.
    
    Parameters:
    - **skip**: int - Number of records to skip (default: 0)
    - **limit**: int - Maximum number of records to return (default: 10)
    
    Returns: List of content gap analysis records
    """
    gap_analysis_records = db.query(ContentGapAnalysis).offset(skip).limit(limit).all()
    return gap_analysis_records


@app.get("/content_gap_analysis/{analysis_id}", response_model=ContentGapAnalysisResponse)
def get_content_gap_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific content gap analysis record by ID.
    
    Parameters:
    - **analysis_id**: int - The ID of the content gap analysis
    
    Returns: Content gap analysis details
    """
    db_gap_analysis = db.query(ContentGapAnalysis).filter(ContentGapAnalysis.id == analysis_id).first()
    if not db_gap_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content gap analysis with id {analysis_id} not found"
        )
    return db_gap_analysis


@app.get("/content_gap_analysis/aggregator/{aggregator}", response_model=List[ContentGapAnalysisResponse])
def get_gap_analysis_by_aggregator(
    aggregator: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get content gap analysis records filtered by aggregator.
    
    Parameters:
    - **aggregator**: str - Aggregator name to filter by
    - **skip**: int - Number of records to skip (default: 0)
    - **limit**: int - Maximum number of records to return (default: 10)
    
    Returns: List of content gap analysis records for the aggregator
    """
    gap_analysis_records = db.query(ContentGapAnalysis).filter(ContentGapAnalysis.aggregator == aggregator).offset(skip).limit(limit).all()
    return gap_analysis_records


@app.get("/content_gap_analysis/priority/{priority}", response_model=List[ContentGapAnalysisResponse])
def get_gap_analysis_by_priority(
    priority: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get content gap analysis records filtered by priority.
    
    Parameters:
    - **priority**: str - Priority level to filter by
    - **skip**: int - Number of records to skip (default: 0)
    - **limit**: int - Maximum number of records to return (default: 10)
    
    Returns: List of content gap analysis records with the specified priority
    """
    gap_analysis_records = db.query(ContentGapAnalysis).filter(ContentGapAnalysis.priority == priority).offset(skip).limit(limit).all()
    return gap_analysis_records


# ==================== ENDPOINT 3: Prompt Analysis ====================

@app.post("/prompt_analysis/", response_model=PromptAnalysisResponse, status_code=status.HTTP_201_CREATED)
def create_prompt_analysis(
    prompt_analysis: PromptAnalysisCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new prompt analysis entry.
    
    Parameters:
    - **prompt**: str - The prompt/question sent to AI
    - **ai_answer**: str - The AI's response to the prompt
    
    Returns: Created prompt analysis with ID and timestamps
    """
    db_prompt_analysis = PromptAnalysis(
        prompt=prompt_analysis.prompt,
        ai_answer=prompt_analysis.ai_answer
    )
    db.add(db_prompt_analysis)
    db.commit()
    db.refresh(db_prompt_analysis)
    return db_prompt_analysis


@app.get("/prompt_analysis/", response_model=List[PromptAnalysisResponse])
def list_prompt_analysis(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get all prompt analysis records with pagination support.
    
    Parameters:
    - **skip**: int - Number of records to skip (default: 0)
    - **limit**: int - Maximum number of records to return (default: 10)
    
    Returns: List of prompt analysis records
    """
    prompt_analysis_records = db.query(PromptAnalysis).offset(skip).limit(limit).all()
    return prompt_analysis_records


@app.get("/prompt_analysis/{analysis_id}", response_model=PromptAnalysisResponse)
def get_prompt_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific prompt analysis record by ID.
    
    Parameters:
    - **analysis_id**: int - The ID of the prompt analysis
    
    Returns: Prompt analysis details
    """
    db_prompt_analysis = db.query(PromptAnalysis).filter(PromptAnalysis.id == analysis_id).first()
    if not db_prompt_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt analysis with id {analysis_id} not found"
        )
    return db_prompt_analysis


# ==================== HEALTH CHECK ====================

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns: Status message
    """
    return {
        "status": "healthy",
        "message": "FastAPI application is running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
