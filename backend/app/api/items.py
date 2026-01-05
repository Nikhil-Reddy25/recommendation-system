from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import get_db
import models
from app.services.vector_service import VectorService

router = APIRouter()
vector_service = VectorService()

class ItemCreate(BaseModel):
    title: str
    description: str
    category: str
    price: float
    metadata: Optional[dict] = {}

class ItemResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    price: float
    vector_id: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.post("/items", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new item and generate embeddings
    """
    try:
        # Generate embedding
        text_for_embedding = f"{item.title} {item.description} {item.category}"
        vector_id = vector_service.add_item_vector(
            text=text_for_embedding,
            metadata={
                "title": item.title,
                "category": item.category,
                "price": item.price
            }
        )
        
        # Create database entry
        db_item = models.Item(
            title=item.title,
            description=item.description,
            category=item.category,
            price=item.price,
            item_metadata=item.metadata,
            vector_id=vector_id
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        return db_item
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items", response_model=List[ItemResponse])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all items with optional category filter
    """
    query = db.query(models.Item)
    
    if category:
        query = query.filter(models.Item.category == category)
    
    items = query.offset(skip).limit(limit).all()
    return items

@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific item by ID
    """
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return item
