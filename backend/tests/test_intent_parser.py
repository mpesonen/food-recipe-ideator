import pytest
import json
from unittest.mock import MagicMock, patch

from src.query_engine.intent_parser import parse_user_query, ParsedIntent


class TestParseUserQuery:
    @patch("src.query_engine.intent_parser.OpenAI")
    @patch("src.query_engine.intent_parser.get_settings")
    def test_parses_cuisine_and_diet(self, mock_settings, mock_openai):
        # Setup mocks
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.llm_model = "gpt-4o-mini"

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "cuisine": "Indian",
            "diet": "Vegetarian",
            "use_sql": True,
            "use_vector": True,
            "semantic_query": "Indian vegetarian food"
        })
        mock_client.chat.completions.create.return_value = mock_response

        # Test
        result = parse_user_query("Indian vegetarian dishes")

        assert result.cuisine == "Indian"
        assert result.diet == "Vegetarian"
        assert result.use_sql is True
        assert result.use_vector is True

    @patch("src.query_engine.intent_parser.OpenAI")
    @patch("src.query_engine.intent_parser.get_settings")
    def test_parses_time_constraint(self, mock_settings, mock_openai):
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.llm_model = "gpt-4o-mini"

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "max_prep_time_mins": 30,
            "semantic_query": "quick easy meal",
            "use_sql": True,
            "use_vector": True
        })
        mock_client.chat.completions.create.return_value = mock_response

        result = parse_user_query("quick easy meal")

        assert result.max_prep_time_mins == 30
        assert result.use_sql is True

    @patch("src.query_engine.intent_parser.OpenAI")
    @patch("src.query_engine.intent_parser.get_settings")
    def test_parses_ingredients(self, mock_settings, mock_openai):
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.llm_model = "gpt-4o-mini"

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "ingredients_include": ["chicken", "rice"],
            "use_kg": True,
            "use_sql": True
        })
        mock_client.chat.completions.create.return_value = mock_response

        result = parse_user_query("recipes with chicken and rice")

        assert result.ingredients_include == ["chicken", "rice"]
        assert result.use_kg is True


class TestParsedIntent:
    def test_default_values(self):
        intent = ParsedIntent()

        assert intent.cuisine is None
        assert intent.diet is None
        assert intent.use_kg is False
        assert intent.use_sql is False
        assert intent.use_vector is False

    def test_with_values(self):
        intent = ParsedIntent(
            cuisine="Italian",
            diet="Vegetarian",
            max_prep_time_mins=30,
            use_sql=True,
        )

        assert intent.cuisine == "Italian"
        assert intent.diet == "Vegetarian"
        assert intent.max_prep_time_mins == 30
        assert intent.use_sql is True
