import pinecone
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class VectorSearchService:
    def __init__(self):
        self.model = SentenceTransformer(os.getenv('HUGGINGFACE_MODEL'))
        
        pinecone.init(
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT')
        )
        
        self.index_name = os.getenv('PINECONE_INDEX_NAME')
        
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                self.index_name,
                dimension=int(os.getenv('EMBEDDING_DIMENSION', 384)),
                metric='cosine'
            )
        
        self.index = pinecone.Index(self.index_name)
        logger.info(f"Vector search service initialized with index: {self.index_name}")
    
    async def search(self, user_id: str, context: Optional[str] = None, top_k: int = 50) -> List[Dict]:
        try:
            # Generate query embedding
            if context:
                query_vector = self.model.encode(context).tolist()
            else:
                # Use user preferences as query
                query_vector = await self._get_user_embedding(user_id)
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )
            
            candidates = []
            for match in results['matches']:
                candidates.append({
                    'item_id': match['id'],
                    'score': float(match['score']),
                    'metadata': match.get('metadata', {})
                })
            
            logger.info(f"Found {len(candidates)} candidates for user {user_id}")
            return candidates
        
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            raise
    
    async def index_items(self, items: List[Dict]):
        try:
            vectors = []
            for item in items:
                # Generate embedding
                text = f"{item['title']} {item['description']}"
                embedding = self.model.encode(text).tolist()
                
                vectors.append((
                    item['item_id'],
                    embedding,
                    {
                        'title': item['title'],
                        'category': item['category'],
                        'description': item['description'][:500]
                    }
                ))
            
            # Batch upsert to Pinecone
            self.index.upsert(vectors=vectors)
            logger.info(f"Indexed {len(items)} items successfully")
        
        except Exception as e:
            logger.error(f"Error indexing items: {str(e)}")
            raise
    
    async def _get_user_embedding(self, user_id: str) -> List[float]:
        # Placeholder: In production, fetch user preferences and create embedding
        # For now, return a random embedding
        return np.random.randn(int(os.getenv('EMBEDDING_DIMENSION', 384))).tolist()
    
    async def get_stats(self) -> Dict:
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}
