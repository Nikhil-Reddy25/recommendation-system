from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import logging

from database import engine, get_db
import models
from app.api import recommendations, items, interactions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Recommendation System API",
    description="Personalized recommendation engine using vector similarity and RAG",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
app.include_router(items.router, prefix="/api/v1", tags=["items"])
app.include_router(interactions.router, prefix="/api/v1", tags=["interactions"])

@app.get("/")
async def root():
    return {
        "message": "Recommendation System API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
