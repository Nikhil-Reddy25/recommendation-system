import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Item, UserInteraction, Recommendation
from datetime import datetime

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def test_db():
    """Create a test database for each test"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)
    db = TestSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(engine)

class TestItemModel:
    """Test cases for Item model"""
    
    def test_create_item(self, test_db):
        """Test creating a new item"""
        item = Item(
            title="Test Product",
            description="A test product description",
            category="electronics",
            price=99.99,
            item_metadata={"brand": "TestBrand"},
            vector_id="vec_123"
        )
        test_db.add(item)
        test_db.commit()
        
        assert item.id is not None
        assert item.title == "Test Product"
        assert item.price == 99.99
        assert item.created_at is not None
    
    def test_item_unique_vector_id(self, test_db):
        """Test that vector_id must be unique"""
        item1 = Item(
            title="Product 1",
            description="Description 1",
            category="cat1",
            price=10.0,
            vector_id="vec_duplicate"
        )
        item2 = Item(
            title="Product 2",
            description="Description 2",
            category="cat2",
            price=20.0,
            vector_id="vec_duplicate"
        )
        
        test_db.add(item1)
        test_db.commit()
        
        test_db.add(item2)
        with pytest.raises(Exception):
            test_db.commit()
    
    def test_query_items_by_category(self, test_db):
        """Test querying items by category"""
        item1 = Item(
            title="Laptop",
            description="A laptop",
            category="electronics",
            price=1000.0,
            vector_id="vec_1"
        )
        item2 = Item(
            title="Shirt",
            description="A shirt",
            category="clothing",
            price=25.0,
            vector_id="vec_2"
        )
        
        test_db.add_all([item1, item2])
        test_db.commit()
        
        electronics = test_db.query(Item).filter(Item.category == "electronics").all()
        assert len(electronics) == 1
        assert electronics[0].title == "Laptop"

class TestUserInteractionModel:
    """Test cases for UserInteraction model"""
    
    def test_create_interaction(self, test_db):
        """Test creating a user interaction"""
        interaction = UserInteraction(
            user_id="user_123",
            item_id=1,
            interaction_type="view",
            interaction_value=None
        )
        test_db.add(interaction)
        test_db.commit()
        
        assert interaction.id is not None
        assert interaction.user_id == "user_123"
        assert interaction.timestamp is not None
    
    def test_interaction_with_rating(self, test_db):
        """Test creating an interaction with a rating value"""
        interaction = UserInteraction(
            user_id="user_456",
            item_id=2,
            interaction_type="rating",
            interaction_value=4.5
        )
        test_db.add(interaction)
        test_db.commit()
        
        assert interaction.interaction_value == 4.5
    
    def test_query_user_interactions(self, test_db):
        """Test querying interactions for a specific user"""
        interactions = [
            UserInteraction(user_id="user_789", item_id=1, interaction_type="view"),
            UserInteraction(user_id="user_789", item_id=2, interaction_type="click"),
            UserInteraction(user_id="user_000", item_id=3, interaction_type="view")
        ]
        test_db.add_all(interactions)
        test_db.commit()
        
        user_interactions = test_db.query(UserInteraction).filter(
            UserInteraction.user_id == "user_789"
        ).all()
        
        assert len(user_interactions) == 2

class TestRecommendationModel:
    """Test cases for Recommendation model"""
    
    def test_create_recommendation(self, test_db):
        """Test creating a recommendation"""
        rec = Recommendation(
            user_id="user_123",
            item_id=1,
            score=0.95,
            recommendation_type="vector",
            context="Based on viewing history"
        )
        test_db.add(rec)
        test_db.commit()
        
        assert rec.id is not None
        assert rec.score == 0.95
        assert rec.created_at is not None
    
    def test_recommendation_types(self, test_db):
        """Test different recommendation types"""
        recs = [
            Recommendation(user_id="user_1", item_id=1, score=0.9, recommendation_type="vector"),
            Recommendation(user_id="user_1", item_id=2, score=0.8, recommendation_type="rag"),
            Recommendation(user_id="user_1", item_id=3, score=0.7, recommendation_type="hybrid")
        ]
        test_db.add_all(recs)
        test_db.commit()
        
        hybrid_recs = test_db.query(Recommendation).filter(
            Recommendation.recommendation_type == "hybrid"
        ).all()
        
        assert len(hybrid_recs) == 1
        assert hybrid_recs[0].score == 0.7
