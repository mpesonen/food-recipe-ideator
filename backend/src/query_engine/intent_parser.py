import json
from dataclasses import dataclass
from openai import OpenAI
from src.config import get_settings


@dataclass
class ParsedIntent:
    """Parsed intent from user query."""
    cuisine: str | None = None
    diet: str | None = None
    course: str | None = None
    max_prep_time_mins: int | None = None
    max_cook_time_mins: int | None = None
    ingredients_include: list[str] | None = None
    ingredients_exclude: list[str] | None = None
    semantic_query: str | None = None
    use_kg: bool = False
    use_sql: bool = False
    use_vector: bool = False


SYSTEM_PROMPT = """You are a query parser for a recipe search system. Extract structured filters and semantic meaning from user queries.

The system has three query paths:
1. SQL - for structured filters (cuisine, diet, course, time constraints)
2. Vector - for semantic similarity (fuzzy concepts like "comfort food", "healthy", "easy")
3. Knowledge Graph (KG) - for ingredient relationships and "recipes similar to X"

Analyze the user's query and extract:
- cuisine: specific cuisine type (Indian, Italian, Mexican, etc.) - exact match
- diet: dietary restriction (Vegetarian, Vegan, Non-Vegetarian, etc.) - exact match
- course: meal type (Breakfast, Lunch, Dinner, Snack, Dessert, etc.) - exact match
- max_prep_time_mins: maximum prep time in minutes (interpret "quick" as 30, "fast" as 20)
- max_cook_time_mins: maximum cook time in minutes
- ingredients_include: specific ingredients that must be present
- ingredients_exclude: ingredients to avoid
- semantic_query: the semantic/conceptual part for vector search
- use_kg: true if query involves ingredient relationships or "similar to" patterns
- use_sql: true if there are structured filters
- use_vector: true if there are semantic/conceptual terms

Respond with valid JSON only."""


def parse_user_query(query: str) -> ParsedIntent:
    """Parse user query into structured intent using LLM."""
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Parse this recipe search query: {query}"}
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    result = json.loads(response.choices[0].message.content)

    return ParsedIntent(
        cuisine=result.get('cuisine'),
        diet=result.get('diet'),
        course=result.get('course'),
        max_prep_time_mins=result.get('max_prep_time_mins'),
        max_cook_time_mins=result.get('max_cook_time_mins'),
        ingredients_include=result.get('ingredients_include'),
        ingredients_exclude=result.get('ingredients_exclude'),
        semantic_query=result.get('semantic_query'),
        use_kg=result.get('use_kg', False),
        use_sql=result.get('use_sql', False),
        use_vector=result.get('use_vector', False),
    )
