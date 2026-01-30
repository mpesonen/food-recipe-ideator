import pytest
from unittest.mock import MagicMock, patch, call

from src.query_engine.intent_parser import ParsedIntent
from src.query_engine.pg_query import PGRecipeResult, PostgresQuery


class TestPGRecipeResult:
    def test_default_values(self):
        result = PGRecipeResult(
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
        assert result.distance is None
        assert result.source == "sql"

    def test_with_distance_and_source(self):
        result = PGRecipeResult(
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
            distance=0.25,
            source="vector",
        )
        assert result.distance == 0.25
        assert result.source == "vector"


class TestPostgresQuerySearchSQL:
    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_search_sql_with_cuisine_filter(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor.fetchall.return_value = [
            (1, "Pasta Primavera", "A veggie pasta", "https://example.com", "Italian", "Dinner", "Vegetarian", 15, 25, 4.5, 100, ["pasta", "vegetables"])
        ]

        pg_query = PostgresQuery()
        intent = ParsedIntent(cuisine="Italian", use_sql=True)

        results = pg_query.search_sql(intent, limit=10)

        # Get the last call (first is vector extension setup)
        assert mock_cursor.execute.call_count == 2
        call_args = mock_cursor.execute.call_args_list[1]
        query = call_args[0][0]
        params = call_args[0][1]

        assert "cuisine = %s" in query
        assert "Italian" in params
        assert len(results) == 1
        assert results[0].cuisine == "Italian"

    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_search_sql_with_diet_filter(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor.fetchall.return_value = []

        pg_query = PostgresQuery()
        intent = ParsedIntent(diet="Vegetarian", use_sql=True)

        pg_query.search_sql(intent, limit=10)

        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "diet = %s" in query
        assert "Vegetarian" in params

    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_search_sql_with_time_constraints(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor.fetchall.return_value = []

        pg_query = PostgresQuery()
        intent = ParsedIntent(max_prep_time_mins=20, max_cook_time_mins=30, use_sql=True)

        pg_query.search_sql(intent, limit=10)

        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "prep_time_mins <= %s" in query
        assert "cook_time_mins <= %s" in query
        assert 20 in params
        assert 30 in params

    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_search_sql_with_ingredients(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor.fetchall.return_value = []

        pg_query = PostgresQuery()
        intent = ParsedIntent(ingredients_include=["chicken", "rice"], use_sql=True)

        pg_query.search_sql(intent, limit=10)

        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        # Check case-insensitive ingredient matching with ILIKE
        assert "ILIKE" in query
        assert "unnest" in query
        assert "%chicken%" in params
        assert "%rice%" in params


class TestPostgresQuerySearchVector:
    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_search_vector(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock embedding response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock()]
        mock_embedding_response.data[0].embedding = [0.1] * 1536
        mock_client.embeddings.create.return_value = mock_embedding_response

        mock_cursor.fetchall.return_value = [
            (1, "Comfort Food", "Warm and cozy", "https://example.com", "American", "Dinner", None, 30, 45, 4.2, 50, ["chicken", "gravy"], 0.15)
        ]

        pg_query = PostgresQuery()
        results = pg_query.search_vector("comfort food for dinner", limit=10)

        # Verify embedding was created
        mock_client.embeddings.create.assert_called_once()

        # Verify query uses vector similarity
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        assert "<=>" in query  # pgvector distance operator
        assert "distance" in query

        assert len(results) == 1
        assert results[0].source == "vector"
        assert results[0].distance == 0.15


class TestPostgresQuerySearchHybrid:
    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_search_hybrid_with_filters_and_semantic(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock()]
        mock_embedding_response.data[0].embedding = [0.1] * 1536
        mock_client.embeddings.create.return_value = mock_embedding_response

        mock_cursor.fetchall.return_value = [
            (1, "Indian Veggie Delight", "Spicy veggies", "https://example.com", "Indian", "Dinner", "Vegetarian", 15, 25, 4.7, 200, ["vegetables", "spices"], 0.12)
        ]

        pg_query = PostgresQuery()
        intent = ParsedIntent(
            cuisine="Indian",
            diet="Vegetarian",
            semantic_query="spicy vegetable curry",
            use_sql=True,
            use_vector=True,
        )

        results = pg_query.search_hybrid(intent, limit=10)

        # Verify embedding was created for semantic query
        mock_client.embeddings.create.assert_called()
        embed_call = mock_client.embeddings.create.call_args
        assert "spicy vegetable curry" in str(embed_call)

        # Verify query has both SQL filters and vector similarity
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        assert "cuisine = %s" in query
        assert "diet = %s" in query
        assert "<=>" in query

        assert len(results) == 1
        assert results[0].source == "sql+vector"

    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_search_hybrid_without_semantic_query(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_cursor.fetchall.return_value = [
            (1, "Italian Pasta", "Classic pasta", "https://example.com", "Italian", "Dinner", "Vegetarian", 15, 20, 4.5, 150, ["pasta"], None)
        ]

        pg_query = PostgresQuery()
        intent = ParsedIntent(
            cuisine="Italian",
            diet="Vegetarian",
            use_sql=True,
            use_vector=True,
        )

        results = pg_query.search_hybrid(intent, limit=10)

        # Should fall back to using cuisine for embedding
        mock_client.embeddings.create.assert_called()

        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        assert "cuisine = %s" in query


class TestPostgresQueryGetRecipeById:
    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_get_recipe_by_id_found(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor.fetchone.return_value = (
            1, "Test Recipe", "A delicious recipe", "https://example.com", "Italian", "Dinner", "Vegetarian", 20, 30, 4.5, 100, ["pasta"]
        )

        pg_query = PostgresQuery()
        result = pg_query.get_recipe_by_id(1)

        # Get the last call (first is vector extension setup)
        assert mock_cursor.execute.call_count == 2
        call_args = mock_cursor.execute.call_args_list[1]
        assert call_args[0][1] == (1,)

        assert result is not None
        assert result.id == 1
        assert result.title == "Test Recipe"

    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_get_recipe_by_id_not_found(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor.fetchone.return_value = None

        pg_query = PostgresQuery()
        result = pg_query.get_recipe_by_id(99999)

        assert result is None


class TestPostgresQueryRowToResult:
    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_row_to_result_without_distance(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        pg_query = PostgresQuery()

        row = (1, "Recipe", "Description", "https://url.com", "Italian", "Dinner", "Vegetarian", 15, 25, 4.5, 100, ["ingredient"])
        result = pg_query._row_to_result(row, source="sql", has_distance=False)

        assert result.id == 1
        assert result.title == "Recipe"
        assert result.distance is None
        assert result.source == "sql"

    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_row_to_result_with_distance(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        pg_query = PostgresQuery()

        row = (1, "Recipe", "Description", "https://url.com", "Italian", "Dinner", "Vegetarian", 15, 25, 4.5, 100, ["ingredient"], 0.25)
        result = pg_query._row_to_result(row, source="vector", has_distance=True)

        assert result.id == 1
        assert result.distance == 0.25
        assert result.source == "vector"

    @patch("src.query_engine.pg_query.OpenAI")
    @patch("src.query_engine.pg_query.register_vector")
    @patch("src.query_engine.pg_query.psycopg.connect")
    @patch("src.query_engine.pg_query.get_settings")
    def test_row_to_result_handles_null_values(self, mock_settings, mock_connect, mock_register, mock_openai):
        mock_settings.return_value.postgres_url = "postgresql://test"
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        pg_query = PostgresQuery()

        row = (1, "Recipe", None, None, None, None, None, None, None, None, None, None)
        result = pg_query._row_to_result(row, source="sql", has_distance=False)

        assert result.id == 1
        assert result.description == ""
        assert result.url == ""
        assert result.rating == 0.0
        assert result.vote_count == 0
        assert result.ingredients == []
