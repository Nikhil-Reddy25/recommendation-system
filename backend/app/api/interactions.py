from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import get_db
import models

router = APIRouter()

class InteractionCreate(BaseModel):
    user_id: str
    item_id: int
    interaction_type: str  # view, click, purchase, rating
    interaction_value: Optional[float] = None
    metadata: Optional[dict] = {}

class InteractionResponse(BaseModel):
    id: int
    user_id: str
    item_id: int
    interaction_type: str
    interaction_value: Optional[float] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

@router.post("/interactions", response_model=InteractionResponse)
async def create_interaction(
    interaction: InteractionCreate,
    db: Session = Depends(get_db)
):
    """
    Record a user interaction with an item
    """
    try:
        db_interaction = models.UserInteraction(
            user_id=interaction.user_id,
            item_id=interaction.item_id,
            interaction_type=interaction.interaction_type,
            interaction_value=interaction.interaction_value,
            metadata=interaction.metadata
        )
        db.add(db_interaction)
        db.commit()
        db.refresh(db_interaction)
        
        return db_interaction
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interactions/{user_id}", response_model=List[InteractionResponse])
async def get_user_interactions(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get interaction history for a user
    """
    interactions = db.query(models.UserInteraction).filter(
        models.UserInteraction.user_id == user_id
    ).order_by(models.UserInteraction.timestamp.desc()).limit(limit).all()
    
    return interactions
