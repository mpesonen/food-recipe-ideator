import pytest
from unittest.mock import MagicMock, patch

from src.query_engine.intent_parser import ParsedIntent
from src.query_engine.kg_query import KGRecipeResult, KnowledgeGraphQuery


class TestKGRecipeResult:
    def test_default_score(self):
        result = KGRecipeResult(
            id=1,
            title="Test Recipe",
            rating=4.5,
            prep_time_mins=20,
            cook_time_mins=30,
        )
        assert result.score == 1.0

    def test_with_custom_score(self):
        result = KGRecipeResult(
            id=1,
            title="Test Recipe",
            rating=4.5,
            prep_time_mins=20,
            cook_time_mins=30,
            score=5.0,
        )
        assert result.score == 5.0


class TestKnowledgeGraphQuerySearch:
    @patch("src.query_engine.kg_query.get_settings")
    @patch("src.query_engine.kg_query.GraphDatabase")
    def test_search_with_cuisine_filter(self, mock_graph_db, mock_settings):
        mock_settings.return_value.neo4j_uri = "bolt://localhost:7687"
        mock_settings.return_value.neo4j_user = "neo4j"
        mock_settings.return_value.neo4j_password = "password"

        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([
            {"id": 1, "title": "Butter Chicken", "rating": 4.8, "prep_time_mins": 20, "cook_time_mins": 30}
        ]))
        mock_session.run.return_value = mock_result

        kg_query = KnowledgeGraphQuery()
        intent = ParsedIntent(cuisine="Indian", use_kg=True)

        results = kg_query.search(intent, limit=10)

        # Verify query was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args

        # Check query contains cuisine match clause
        query = call_args[0][0]
        assert "HAS_CUISINE" in query
        assert "$cuisine" in query

        # Check params
        params = call_args[0][1]
        assert params["cuisine"] == "Indian"
        assert params["limit"] == 10

        # Verify results
        assert len(results) == 1
        assert results[0].title == "Butter Chicken"

    @patch("src.query_engine.kg_query.get_settings")
    @patch("src.query_engine.kg_query.GraphDatabase")
    def test_search_with_diet_filter(self, mock_graph_db, mock_settings):
        mock_settings.return_value.neo4j_uri = "bolt://localhost:7687"
        mock_settings.return_value.neo4j_user = "neo4j"
        mock_settings.return_value.neo4j_password = "password"

        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.run.return_value = mock_result

        kg_query = KnowledgeGraphQuery()
        intent = ParsedIntent(diet="Vegetarian", use_kg=True)

        kg_query.search(intent, limit=10)

        call_args = mock_session.run.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "HAS_DIET" in query
        assert params["diet"] == "Vegetarian"

    @patch("src.query_engine.kg_query.get_settings")
    @patch("src.query_engine.kg_query.GraphDatabase")
    def test_search_with_ingredients(self, mock_graph_db, mock_settings):
        mock_settings.return_value.neo4j_uri = "bolt://localhost:7687"
        mock_settings.return_value.neo4j_user = "neo4j"
        mock_settings.return_value.neo4j_password = "password"

        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.run.return_value = mock_result

        kg_query = KnowledgeGraphQuery()
        intent = ParsedIntent(ingredients_include=["chicken", "rice"], use_kg=True)

        kg_query.search(intent, limit=10)

        call_args = mock_session.run.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        # Check case-insensitive ingredient matching
        assert "toLower" in query
        assert "CONTAINS" in query
        assert params["ing_0"] == "chicken"
        assert params["ing_1"] == "rice"

    @patch("src.query_engine.kg_query.get_settings")
    @patch("src.query_engine.kg_query.GraphDatabase")
    def test_search_with_time_constraints(self, mock_graph_db, mock_settings):
        mock_settings.return_value.neo4j_uri = "bolt://localhost:7687"
        mock_settings.return_value.neo4j_user = "neo4j"
        mock_settings.return_value.neo4j_password = "password"

        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.run.return_value = mock_result

        kg_query = KnowledgeGraphQuery()
        intent = ParsedIntent(max_prep_time_mins=30, max_cook_time_mins=45, use_kg=True)

        kg_query.search(intent, limit=10)

        call_args = mock_session.run.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "prep_time_mins <= $max_prep_time" in query
        assert "cook_time_mins <= $max_cook_time" in query
        assert params["max_prep_time"] == 30
        assert params["max_cook_time"] == 45

    @patch("src.query_engine.kg_query.get_settings")
    @patch("src.query_engine.kg_query.GraphDatabase")
    def test_search_combined_filters(self, mock_graph_db, mock_settings):
        mock_settings.return_value.neo4j_uri = "bolt://localhost:7687"
        mock_settings.return_value.neo4j_user = "neo4j"
        mock_settings.return_value.neo4j_password = "password"

        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([
            {"id": 1, "title": "Quick Indian Veg", "rating": 4.5, "prep_time_mins": 15, "cook_time_mins": 20}
        ]))
        mock_session.run.return_value = mock_result

        kg_query = KnowledgeGraphQuery()
        intent = ParsedIntent(
            cuisine="Indian",
            diet="Vegetarian",
            max_prep_time_mins=30,
            ingredients_include=["paneer"],
            use_kg=True,
        )

        results = kg_query.search(intent, limit=10)

        call_args = mock_session.run.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "HAS_CUISINE" in query
        assert "HAS_DIET" in query
        assert "prep_time_mins" in query
        assert "toLower" in query
        assert params["cuisine"] == "Indian"
        assert params["diet"] == "Vegetarian"
        assert len(results) == 1


class TestKnowledgeGraphQuerySimilar:
    @patch("src.query_engine.kg_query.get_settings")
    @patch("src.query_engine.kg_query.GraphDatabase")
    def test_find_similar_by_ingredients(self, mock_graph_db, mock_settings):
        mock_settings.return_value.neo4j_uri = "bolt://localhost:7687"
        mock_settings.return_value.neo4j_user = "neo4j"
        mock_settings.return_value.neo4j_password = "password"

        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([
            {"id": 2, "title": "Similar Recipe", "rating": 4.0, "prep_time_mins": 25, "cook_time_mins": 35, "shared_ingredients": 3}
        ]))
        mock_session.run.return_value = mock_result

        kg_query = KnowledgeGraphQuery()
        results = kg_query.find_similar_by_ingredients(recipe_id=1, limit=5)

        mock_session.run.assert_called_once()
        assert len(results) == 1
        assert results[0].score == 3  # shared_ingredients count


class TestKnowledgeGraphQueryIngredientCombination:
    @patch("src.query_engine.kg_query.get_settings")
    @patch("src.query_engine.kg_query.GraphDatabase")
    def test_get_recipes_by_ingredient_combination(self, mock_graph_db, mock_settings):
        mock_settings.return_value.neo4j_uri = "bolt://localhost:7687"
        mock_settings.return_value.neo4j_user = "neo4j"
        mock_settings.return_value.neo4j_password = "password"

        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([
            {"id": 1, "title": "Chicken Rice", "rating": 4.5, "prep_time_mins": 20, "cook_time_mins": 30}
        ]))
        mock_session.run.return_value = mock_result

        kg_query = KnowledgeGraphQuery()
        results = kg_query.get_recipes_by_ingredient_combination(["chicken", "rice"], limit=10)

        call_args = mock_session.run.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        # Verify case-insensitive matching
        assert "toLower" in query
        assert params["ing_0"] == "chicken"
        assert params["ing_1"] == "rice"
        assert len(results) == 1

    @patch("src.query_engine.kg_query.get_settings")
    @patch("src.query_engine.kg_query.GraphDatabase")
    def test_empty_ingredients_returns_empty_list(self, mock_graph_db, mock_settings):
        mock_settings.return_value.neo4j_uri = "bolt://localhost:7687"
        mock_settings.return_value.neo4j_user = "neo4j"
        mock_settings.return_value.neo4j_password = "password"

        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        kg_query = KnowledgeGraphQuery()
        results = kg_query.get_recipes_by_ingredient_combination([], limit=10)

        assert results == []
