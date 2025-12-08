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
    PromptAnalysisCreate, PromptAnalysisResponse,
    DomainScoreRequest, DomainScoreResponse,
    AIRecommendationRequest, AIRecommendationResponse
)
from domain_score_calculator import DomainScoreCalculator
from ai_recommendation_generator import AIRecommendationGenerator

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
    - **llm**: str (optional) - The LLM that generated the response
    - **prompt**: str - The prompt/question sent to AI
    - **ai_answer**: str - The AI's response to the prompt
    - **answer_length**: int (optional) - Length of original answer
    - **summary_length**: int (optional) - Length of summarized answer
    - **status**: str (optional) - Extraction status
    
    Returns: Created prompt analysis with ID and timestamps
    """
    db_prompt_analysis = PromptAnalysis(
        llm=prompt_analysis.llm,
        prompt=prompt_analysis.prompt,
        ai_answer=prompt_analysis.ai_answer,
        answer_length=prompt_analysis.answer_length,
        summary_length=prompt_analysis.summary_length,
        status=prompt_analysis.status
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


@app.post("/prompt_analysis/bulk_import/", status_code=status.HTTP_201_CREATED)
def bulk_import_prompt_analysis(
    db: Session = Depends(get_db)
):
    """
    Bulk import prompt analysis data from ai_responses_cleaned.csv.
    Reads the CSV from the AiExtractionAgent folder and imports all records.
    
    Returns: Summary of imported records
    """
    import pandas as pd
    import os
    
    try:
        # Construct path to the CSV file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        csv_path = os.path.join(parent_dir, "AiExtractionAgent", "ai_responses_cleaned.csv")
        
        if not os.path.exists(csv_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CSV file not found at {csv_path}"
            )
        
        # Read the CSV
        df = pd.read_csv(csv_path)
        
        # Import records
        imported_count = 0
        failed_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                db_prompt_analysis = PromptAnalysis(
                    llm=row.get('llm'),
                    prompt=row.get('full_prompt'),
                    ai_answer=row.get('summarized_answer'),
                    answer_length=int(row.get('answer_length')) if pd.notna(row.get('answer_length')) else None,
                    summary_length=int(row.get('summary_length')) if pd.notna(row.get('summary_length')) else None,
                    status=row.get('status')
                )
                db.add(db_prompt_analysis)
                imported_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"Row {index}: {str(e)}")
        
        db.commit()
        
        return {
            "message": "Bulk import completed",
            "total_records": len(df),
            "imported": imported_count,
            "failed": failed_count,
            "errors": errors[:10] if errors else []  # Return first 10 errors
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during bulk import: {str(e)}"
        )


# ==================== ENDPOINT 4: Domain Score Calculation (New) ====================

@app.post("/domain_score/calculate", response_model=DomainScoreResponse)
def calculate_domain_score(request: DomainScoreRequest):
    """
    Calculate domain visibility score for a brand based on crawler, extraction, and gap analysis outputs.
    
    Parameters:
    - **brand**: str - Brand name to calculate score for
    
    Returns: Domain score with breakdown and metadata
    """
    try:
        calculator = DomainScoreCalculator()
        score_data = calculator.calculate_domain_score(request.brand)
        
        return DomainScoreResponse(
            brand=score_data['brand'],
            overall_score=score_data['overall_score'],
            score_breakdown=score_data['score_breakdown'],
            weights=score_data['weights'],
            metadata=score_data['metadata']
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating domain score: {str(e)}"
        )


# ==================== ENDPOINT 5: AI-Powered Recommendations ====================

@app.post("/domain_score/recommendations", response_model=AIRecommendationResponse)
def generate_ai_recommendations(request: AIRecommendationRequest):
    """
    Generate AI-powered recommendations explaining domain score and providing improvement actions.
    Uses Google Gemini to generate detailed explanations and actionable recommendations.
    
    Parameters:
    - **brand**: str - Brand name to generate recommendations for
    - **include_score_calculation**: bool - If True, calculates score first (default: True)
    
    Returns: AI-generated explanation and recommendations
    """
    try:
        calculator = DomainScoreCalculator()
        
        # Calculate score if requested
        if request.include_score_calculation:
            score_data = calculator.calculate_domain_score(request.brand)
        else:
            # Use existing score data if available, otherwise calculate anyway
            score_data = calculator.calculate_domain_score(request.brand)
        
        # Generate AI recommendations
        try:
            generator = AIRecommendationGenerator()
            recommendations = generator.generate_recommendations(score_data)
            
            return AIRecommendationResponse(
                brand=request.brand,
                overall_score=score_data['overall_score'],
                explanation=recommendations['explanation'],
                recommendations=recommendations['recommendations'],
                score_breakdown=score_data['score_breakdown'],
                metadata=score_data['metadata']
            )
        except ValueError as e:
            # If Gemini API key is not set, return error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"AI recommendation generation failed: {str(e)}. Please set GEMINI_API_KEY environment variable."
            )
        except Exception as e:
            # If AI generation fails, return score with fallback recommendations
            generator = AIRecommendationGenerator()
            fallback_recs = generator._generate_fallback_recommendations(score_data)
            
            return AIRecommendationResponse(
                brand=request.brand,
                overall_score=score_data['overall_score'],
                explanation=f"AI recommendation generation encountered an error: {str(e)}",
                recommendations=fallback_recs,
                score_breakdown=score_data['score_breakdown'],
                metadata=score_data['metadata']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


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
