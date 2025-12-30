import openai
import os
from typing import List, Dict
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class RAGReRankingService:
    """Re-ranks recommendation candidates using LLM for better contextual relevance."""
    
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.temperature = 0.3
        logger.info(f"Initialized RAG service with model: {self.model}")
    
    async def rerank(self, candidates: List[Dict], context: str, top_k: int = 10) -> List[Dict]:
        """
        Re-rank candidates using LLM for semantic understanding.
        
        Args:
            candidates: List of candidate items from vector search
            context: User's query context
            top_k: Number of items to return
            
        Returns:
            Re-ranked list of candidates
        """
        if not candidates:
            return []
        
        try:
            # Limit candidates to avoid token limits
            candidates_subset = candidates[:min(len(candidates), 50)]
            
            # Build prompt with candidate information
            items_list = []
            for idx, item in enumerate(candidates_subset, 1):
                title = item.get('metadata', {}).get('title', 'Unknown')
                desc = item.get('metadata', {}).get('description', '')[:150]
                items_list.append(f"{idx}. {title}: {desc}")
            
            items_text = "\n".join(items_list)
            
            prompt = self._build_ranking_prompt(context, items_text, top_k)
            
            # Get LLM rankings
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=150
            )
            
            rankings_text = response.choices[0].message.content.strip()
            
            # Parse and validate rankings
            rankings = self._parse_rankings(rankings_text, len(candidates_subset))
            
            # Reorder candidates based on LLM output
            reranked = []
            for rank_idx in rankings[:top_k]:
                if rank_idx < len(candidates_subset):
                    reranked.append(candidates_subset[rank_idx])
            
            # Fill remaining slots with original order if needed
            if len(reranked) < top_k:
                for candidate in candidates_subset:
                    if candidate not in reranked and len(reranked) < top_k:
                        reranked.append(candidate)
            
            logger.info(f"Re-ranked {len(candidates)} candidates down to {len(reranked)}")
            return reranked
            
        except Exception as e:
            logger.error(f"Error in RAG re-ranking: {str(e)}")
            # Fallback: return original top-k candidates
            return candidates[:top_k]
    
    def _build_ranking_prompt(self, context: str, items_text: str, top_k: int) -> str:
        """Build the ranking prompt for the LLM."""
        return f"""You are a recommendation expert. A user is looking for: "{context}"

Here are the candidate items:
{items_text}

Rank these items by relevance to the user's request. Return ONLY the top {top_k} item numbers as a comma-separated list (e.g., "5,1,3,7,2").

Your ranking:"""
    
    def _parse_rankings(self, rankings_text: str, max_index: int) -> List[int]:
        """Parse LLM output into list of indices."""
        try:
            # Extract numbers from response
            numbers = []
            for part in rankings_text.replace(' ', '').split(','):
                part = part.strip()
                if part.isdigit():
                    num = int(part) - 1  # Convert to 0-indexed
                    if 0 <= num < max_index:
                        numbers.append(num)
            
            return numbers if numbers else list(range(min(10, max_index)))
            
        except Exception as e:
            logger.warning(f"Failed to parse rankings: {e}. Using default order.")
            return list(range(min(10, max_index)))
    
    async def explain_recommendation(self, item: Dict, context: str) -> str:
        """
        Generate a natural language explanation for why this item was recommended.
        
        Args:
            item: The recommended item
            context: User's original context
            
        Returns:
            Human-readable explanation
        """
        try:
            title = item.get('metadata', {}).get('title', 'This item')
            description = item.get('metadata', {}).get('description', '')[:200]
            
            prompt = f"""Explain in 1-2 sentences why "{title}" is a good match for someone looking for: "{context}"

Item description: {description}

Explanation:"""
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return "This item matches your preferences based on semantic similarity."
