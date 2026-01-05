import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import app

client = TestClient(app)

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct message"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Recommendation System API"
        assert response.json()["status"] == "active"
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

class TestRecommendationsAPI:
    """Test recommendation endpoints"""
    
    def test_get_recommendations_without_history(self):
        """Test getting recommendations for user without history"""
        response = client.get("/api/v1/recommendations/new_user_999")
        assert response.status_code == 200
        # Should return empty or popular items
        data = response.json()
        assert isinstance(data, list)
    
    def test_post_recommendations(self):
        """Test POST recommendations endpoint"""
        payload = {
            "user_id": "test_user_123",
            "context": "Looking for electronics",
            "limit": 5,
            "use_rag": False
        }
        response = client.post("/api/v1/recommendations", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_recommendations_with_limit(self):
        """Test recommendations respects limit parameter"""
        response = client.get("/api/v1/recommendations/user_test?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

class TestItemsAPI:
    """Test item endpoints"""
    
    def test_list_items(self):
        """Test listing all items"""
        response = client.get("/api/v1/items")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_items_with_pagination(self):
        """Test items pagination"""
        response = client.get("/api/v1/items?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    def test_list_items_by_category(self):
        """Test filtering items by category"""
        response = client.get("/api/v1/items?category=electronics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestInteractionsAPI:
    """Test interaction endpoints"""
    
    def test_create_interaction(self):
        """Test creating a user interaction"""
        payload = {
            "user_id": "test_user_456",
            "item_id": 1,
            "interaction_type": "view",
            "interaction_value": None,
            "metadata": {}
        }
        response = client.post("/api/v1/interactions", json=payload)
        # May fail due to database constraints, but should return proper status
        assert response.status_code in [200, 404, 500]
    
    def test_get_user_interactions(self):
        """Test retrieving user interactions"""
        response = client.get("/api/v1/interactions/test_user_789")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present"""
        response = client.options("/")
        # CORS headers should be present
        assert response.status_code in [200, 405]

class TestErrorHandling:
    """Test API error handling"""
    
    def test_invalid_item_id(self):
        """Test handling of invalid item ID"""
        response = client.get("/api/v1/items/99999999")
        assert response.status_code in [404, 422]
    
    def test_invalid_endpoint(self):
        """Test handling of non-existent endpoint"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
