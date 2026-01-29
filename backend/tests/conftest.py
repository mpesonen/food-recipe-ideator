import pytest
from unittest.mock import MagicMock, patch

from src.data_ingestion.csv_parser import Recipe


@pytest.fixture
def sample_recipes() -> list[Recipe]:
    """Sample recipes for testing."""
    return [
        Recipe(
            id=0,
            title="Butter Chicken",
            url="https://example.com/butter-chicken",
            description="A creamy and delicious Indian curry",
            cuisine="Indian",
            course="Dinner",
            diet="Non-Vegetarian",
            prep_time_mins=20,
            cook_time_mins=30,
            rating=4.8,
            vote_count=500,
            ingredients=["Chicken", "Butter", "Tomato", "Cream", "Spices"],
            instructions="Cook chicken, add sauce...",
            author="Chef A",
            tags="curry, indian, creamy",
            category="Main Course",
        ),
        Recipe(
            id=1,
            title="Vegetable Biryani",
            url="https://example.com/veg-biryani",
            description="Fragrant rice dish with mixed vegetables",
            cuisine="Indian",
            course="Lunch",
            diet="Vegetarian",
            prep_time_mins=30,
            cook_time_mins=45,
            rating=4.5,
            vote_count=300,
            ingredients=["Rice", "Mixed Vegetables", "Spices", "Ghee"],
            instructions="Layer rice and vegetables...",
            author="Chef B",
            tags="biryani, vegetarian, rice",
            category="Main Course",
        ),
        Recipe(
            id=2,
            title="Quick Pasta",
            url="https://example.com/quick-pasta",
            description="Simple and quick Italian pasta",
            cuisine="Italian",
            course="Dinner",
            diet="Vegetarian",
            prep_time_mins=10,
            cook_time_mins=15,
            rating=4.2,
            vote_count=200,
            ingredients=["Pasta", "Tomato Sauce", "Garlic", "Olive Oil"],
            instructions="Boil pasta, add sauce...",
            author="Chef C",
            tags="pasta, quick, italian",
            category="Main Course",
        ),
    ]


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch("src.query_engine.intent_parser.OpenAI") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client

        # Mock chat completions response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"cuisine": "Indian", "diet": "Vegetarian", "use_sql": true, "use_vector": true}'
        mock_client.chat.completions.create.return_value = mock_response

        yield mock_client


@pytest.fixture
def mock_embeddings():
    """Mock OpenAI embeddings for testing."""
    with patch("src.query_engine.pg_query.OpenAI") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client

        # Mock embeddings response
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1] * 1536  # Fake embedding
        mock_client.embeddings.create.return_value = mock_response

        yield mock_client
