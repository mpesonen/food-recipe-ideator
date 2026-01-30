import pytest
from unittest.mock import MagicMock, patch

from src.query_engine.intent_parser import ParsedIntent
from src.query_engine.fusion import FusedRecipeResult, SearchResponse, Thinking


@pytest.fixture
def mock_search_result():
    """Create a mock search result."""
    return SearchResponse(
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
        thinking=Thinking(reasoning="Test reasoning", routing_explanation=["Test route"]),
    )


@pytest.fixture
def mock_recipe():
    """Create a mock recipe for get_recipe_by_id."""
    from src.query_engine.pg_query import PGRecipeResult
    return PGRecipeResult(
        id=1,
        title="Test Recipe",
        description="A test recipe",
        url="https://example.com/recipe",
        cuisine="Italian",
        course="Dinner",
        diet="Vegetarian",
        prep_time_mins=20,
        cook_time_mins=30,
        rating=4.5,
        vote_count=100,
        ingredients=["pasta", "tomato"],
    )


class TestHealthEndpoint:
    def test_health_check(self):
        """Test health endpoint returns ok status."""
        from fastapi.testclient import TestClient

        # Mock the search engine to avoid database connections
        with patch("src.api.main.RecipeSearchEngine") as MockEngine:
            mock_engine = MagicMock()
            MockEngine.return_value = mock_engine

            from src.api.main import app
            with TestClient(app) as client:
                response = client.get("/api/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "ok"
                assert "message" in data


class TestSearchEndpoint:
    def test_search_returns_results(self, mock_search_result):
        """Test search endpoint returns parsed intent and results."""
        from fastapi.testclient import TestClient

        with patch("src.api.main.RecipeSearchEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_engine.search.return_value = mock_search_result
            mock_engine._generate_routing_explanation.return_value = ["Test route"]
            MockEngine.return_value = mock_engine

            from src.api.main import app
            with TestClient(app) as client:
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

    def test_search_with_default_limit(self, mock_search_result):
        """Test search with default limit."""
        from fastapi.testclient import TestClient

        with patch("src.api.main.RecipeSearchEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_engine.search.return_value = mock_search_result
            MockEngine.return_value = mock_engine

            from src.api.main import app
            with TestClient(app) as client:
                response = client.post(
                    "/api/search",
                    json={"query": "quick pasta"}
                )

                assert response.status_code == 200
                mock_engine.search.assert_called_once()


class TestRecipeDetailEndpoint:
    def test_get_recipe_found(self, mock_recipe):
        """Test getting an existing recipe."""
        from fastapi.testclient import TestClient

        with patch("src.api.main.RecipeSearchEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_engine.pg_query.get_recipe_by_id.return_value = mock_recipe
            MockEngine.return_value = mock_engine

            from src.api.main import app
            with TestClient(app) as client:
                response = client.get("/api/recipes/1")

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == 1
                assert data["title"] == "Test Recipe"

    def test_get_recipe_not_found(self):
        """Test getting a non-existent recipe."""
        from fastapi.testclient import TestClient

        with patch("src.api.main.RecipeSearchEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_engine.pg_query.get_recipe_by_id.return_value = None
            MockEngine.return_value = mock_engine

            from src.api.main import app
            with TestClient(app) as client:
                response = client.get("/api/recipes/99999")
                assert response.status_code == 404


class TestSearchStreamEndpoint:
    def test_search_stream_returns_sse(self, mock_search_result):
        """Test search-stream endpoint returns Server-Sent Events."""
        from fastapi.testclient import TestClient

        with patch("src.api.main.RecipeSearchEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_engine.search.return_value = mock_search_result
            mock_engine._generate_routing_explanation.return_value = ["Test route"]
            MockEngine.return_value = mock_engine

            # Mock the stream_reasoning async generator
            async def mock_stream_reasoning(query):
                yield "Test "
                yield "reasoning "
                yield "text"

            with patch("src.api.routes.stream_reasoning", mock_stream_reasoning):
                with patch("src.api.routes.parse_user_query") as mock_parse:
                    mock_parse.return_value = mock_search_result.parsed_intent

                    from src.api.main import app
                    with TestClient(app) as client:
                        response = client.post(
                            "/api/search-stream",
                            json={"query": "Indian vegetarian", "limit": 10}
                        )

                        assert response.status_code == 200
                        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

                        # Verify SSE format in response
                        content = response.text
                        assert "event:" in content
                        assert "data:" in content
