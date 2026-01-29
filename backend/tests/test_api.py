import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.query_engine.intent_parser import ParsedIntent
from src.query_engine.fusion import FusedRecipeResult, SearchResponse


@pytest.fixture
def mock_search_engine():
    """Mock the search engine for API tests."""
    with patch("src.api.main.search_engine") as mock:
        mock_engine = MagicMock()
        mock.return_value = mock_engine

        # Setup search response
        mock_result = SearchResponse(
            query="Indian vegetarian",
            parsed_intent=ParsedIntent(
                cuisine="Indian",
                diet="Vegetarian",
                use_sql=True,
                use_vector=True,
            ),
            results=[
                FusedRecipeResult(
                    id=1,
                    title="Vegetable Biryani",
                    description="Fragrant rice dish",
                    url="https://example.com/biryani",
                    cuisine="Indian",
                    course="Lunch",
                    diet="Vegetarian",
                    prep_time_mins=30,
                    cook_time_mins=45,
                    rating=4.5,
                    vote_count=300,
                    ingredients=["Rice", "Vegetables"],
                    final_score=0.85,
                    sources=["sql+vector"],
                )
            ],
            source_breakdown={"sql+vector": 1, "kg": 0, "sql": 0, "vector": 0},
        )
        mock_engine.search.return_value = mock_result

        yield mock_engine


@pytest.fixture
def client(mock_search_engine):
    """Create test client with mocked search engine."""
    with patch("src.api.main.get_search_engine", return_value=mock_search_engine):
        from src.api.main import app
        with TestClient(app) as client:
            yield client


class TestHealthEndpoint:
    def test_health_check(self):
        """Test health endpoint returns ok status."""
        # Need to import app directly for this simple test
        from src.api.main import app
        with TestClient(app) as client:
            response = client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"


class TestSearchEndpoint:
    def test_search_returns_results(self, client, mock_search_engine):
        """Test search endpoint returns parsed intent and results."""
        response = client.post(
            "/api/search",
            json={"query": "Indian vegetarian", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["query"] == "Indian vegetarian"
        assert data["parsed_intent"]["cuisine"] == "Indian"
        assert data["parsed_intent"]["diet"] == "Vegetarian"
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Vegetable Biryani"

    def test_search_with_default_limit(self, client, mock_search_engine):
        """Test search with default limit."""
        response = client.post(
            "/api/search",
            json={"query": "quick pasta"}
        )

        assert response.status_code == 200
        mock_search_engine.search.assert_called_once()


class TestRecipeDetailEndpoint:
    def test_get_recipe_not_found(self):
        """Test getting a non-existent recipe."""
        from src.api.main import app

        with patch("src.api.main.get_search_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.pg_query.get_recipe_by_id.return_value = None
            mock_get_engine.return_value = mock_engine

            with TestClient(app) as client:
                response = client.get("/api/recipes/99999")
                assert response.status_code == 404
