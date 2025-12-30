from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
from datetime import datetime

from app.services.vector_service import VectorSearchService
from app.services.rag_service import RAGReRankingService
from app.services.feedback_service import FeedbackService
from app.database.db import engine, SessionLocal
from app.database import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Recommendation System API",
    description="AI-powered recommendation engine with vector similarity and RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_service = VectorSearchService()
rag_service = RAGReRankingService()
feedback_service = FeedbackService()

class RecommendationRequest(BaseModel):
    user_id: str
    context: Optional[str] = None
    top_k: int = 10
    use_rag: bool = True

class FeedbackRequest(BaseModel):
    user_id: str
    item_id: str
    rating: float
    interaction_type: str

class Item(BaseModel):
    item_id: str
    title: str
    description: str
    category: str
    metadata: Optional[Dict] = {}

@app.get("/")
async def root():
    return {
        "message": "Recommendation System API",
        "status": "active",
        "version": "1.0.0"
    }

@app.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    try:
        logger.info(f"Getting recommendations for user {request.user_id}")
        
        # Get initial candidates from vector search
        candidates = await vector_service.search(
            user_id=request.user_id,
            context=request.context,
            top_k=request.top_k * 2
        )
        
        if request.use_rag and request.context:
            # Re-rank using RAG
            recommendations = await rag_service.rerank(
                candidates=candidates,
                context=request.context,
                top_k=request.top_k
            )
        else:
            recommendations = candidates[:request.top_k]
        
        return {
            "user_id": request.user_id,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Received feedback from user {request.user_id}")
        
        # Store feedback
        await feedback_service.store_feedback(
            user_id=request.user_id,
            item_id=request.item_id,
            rating=request.rating,
            interaction_type=request.interaction_type
        )
        
        # Trigger model update in background
        background_tasks.add_task(
            feedback_service.update_user_preferences,
            request.user_id
        )
        
        return {
            "status": "success",
            "message": "Feedback recorded"
        }
    
    except Exception as e:
        logger.error(f"Error storing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/items/batch")
async def add_items_batch(items: List[Item], background_tasks: BackgroundTasks):
    try:
        logger.info(f"Adding {len(items)} items to index")
        
        # Add items to vector index
        background_tasks.add_task(
            vector_service.index_items,
            items
        )
        
        return {
            "status": "success",
            "message": f"Processing {len(items)} items",
            "count": len(items)
        }
    
    except Exception as e:
        logger.error(f"Error adding items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "vector_search": "operational",
            "rag_service": "operational",
            "database": "operational"
        }
    }

@app.get("/stats")
async def get_stats():
    try:
        stats = await vector_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
