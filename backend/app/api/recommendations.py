from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import get_db
import models
from app.services.vector_service import VectorService
from app.services.rag_service import RAGService

router = APIRouter()

class RecommendationRequest(BaseModel):
    user_id: str
    context: Optional[str] = None
    limit: int = 10
    use_rag: bool = False

class RecommendationResponse(BaseModel):
    item_id: int
    title: str
    description: str
    score: float
    explanation: Optional[str] = None

    class Config:
        from_attributes = True

vector_service = VectorService()
rag_service = RAGService()

@router.post("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations for a user
    """
    try:
        # Get user interaction history
        interactions = db.query(models.UserInteraction).filter(
            models.UserInteraction.user_id == request.user_id
        ).order_by(models.UserInteraction.timestamp.desc()).limit(20).all()
        
        if not interactions:
            # No history - return popular items
            popular_items = db.query(models.Item).limit(request.limit).all()
            return [
                RecommendationResponse(
                    item_id=item.id,
                    title=item.title,
                    description=item.description[:200],
                    score=0.5,
                    explanation="Popular item recommendation"
                )
                for item in popular_items
            ]
        
        # Get embeddings for interacted items
        item_ids = [interaction.item_id for interaction in interactions]
        items = db.query(models.Item).filter(models.Item.id.in_(item_ids)).all()
        
        # Vector similarity search
        if items:
            similar_items = vector_service.find_similar_items(
                items[0].vector_id if items else None,
                top_k=request.limit
            )
            
            if request.use_rag and request.context:
                # Re-rank using RAG
                similar_items = rag_service.rerank_with_context(
                    similar_items,
                    request.context
                )
            
            # Fetch full item details
            vector_ids = [item["id"] for item in similar_items]
            recommended_items = db.query(models.Item).filter(
                models.Item.vector_id.in_(vector_ids)
            ).all()
            
            return [
                RecommendationResponse(
                    item_id=item.id,
                    title=item.title,
                    description=item.description[:200],
                    score=0.85,
                    explanation="Based on your viewing history"
                )
                for item in recommended_items[:request.limit]
            ]
        
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{user_id}")
async def get_user_recommendations(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Quick endpoint to get recommendations by user ID
    """
    request = RecommendationRequest(user_id=user_id, limit=limit)
    return await get_recommendations(request, db)
