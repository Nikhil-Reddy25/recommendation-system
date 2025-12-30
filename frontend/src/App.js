import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [userId, setUserId] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchRecommendations = async () => {
    if (!userId) {
      setError('Please enter a user ID');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/recommendations/${userId}?limit=10`
      );
      setRecommendations(response.data);
    } catch (err) {
      setError('Failed to fetch recommendations. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 AI Recommendation System</h1>
        <p>Powered by Vector Similarity Search & RAG</p>
        
        <div className="search-container">
          <input
            type="text"
            placeholder="Enter User ID (e.g., user_123)"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && fetchRecommendations()}
          />
          <button onClick={fetchRecommendations} disabled={loading}>
            {loading ? 'Loading...' : 'Get Recommendations'}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {recommendations.length > 0 && (
          <div className="recommendations">
            <h2>Recommended for You</h2>
            <div className="recommendations-grid">
              {recommendations.map((item) => (
                <div key={item.item_id} className="recommendation-card">
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                  <div className="score">Score: {item.score.toFixed(2)}</div>
                  {item.explanation && (
                    <div className="explanation">{item.explanation}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
