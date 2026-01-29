from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

if TYPE_CHECKING:
    from src.query_engine.fusion import RecipeSearchEngine


def _get_search_engine() -> "RecipeSearchEngine":
    from src.api.main import get_search_engine

    return get_search_engine()


router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    limit: int = 20


class ParsedIntentResponse(BaseModel):
    cuisine: str | None
    diet: str | None
    course: str | None
    max_prep_time_mins: int | None
    max_cook_time_mins: int | None
    ingredients_include: list[str] | None
    ingredients_exclude: list[str] | None
    semantic_query: str | None
    use_kg: bool
    use_sql: bool
    use_vector: bool


class RecipeResult(BaseModel):
    id: int
    title: str
    description: str
    url: str
    cuisine: str | None
    course: str | None
    diet: str | None
    prep_time_mins: int | None
    cook_time_mins: int | None
    rating: float
    vote_count: int
    ingredients: list[str]
    final_score: float
    sources: list[str]


class SearchResponse(BaseModel):
    query: str
    parsed_intent: ParsedIntentResponse
    results: list[RecipeResult]
    source_breakdown: dict[str, int]


class RecipeDetailResponse(BaseModel):
    id: int
    title: str
    description: str
    url: str
    cuisine: str | None
    course: str | None
    diet: str | None
    prep_time_mins: int | None
    cook_time_mins: int | None
    rating: float
    vote_count: int
    ingredients: list[str]


class HealthResponse(BaseModel):
    status: str
    message: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", message="Recipe Ideator API is running")


@router.post("/search", response_model=SearchResponse)
async def search_recipes(request: SearchRequest):
    """
    Search for recipes using natural language query.

    The query is parsed to extract:
    - Structured filters (cuisine, diet, course, time)
    - Semantic concepts for vector search
    - Ingredient requirements for graph traversal

    Results are fused from Knowledge Graph, SQL, and Vector searches.
    """
    engine = _get_search_engine()
    result = engine.search(request.query, limit=request.limit)

    return SearchResponse(
        query=result.query,
        parsed_intent=ParsedIntentResponse(
            cuisine=result.parsed_intent.cuisine,
            diet=result.parsed_intent.diet,
            course=result.parsed_intent.course,
            max_prep_time_mins=result.parsed_intent.max_prep_time_mins,
            max_cook_time_mins=result.parsed_intent.max_cook_time_mins,
            ingredients_include=result.parsed_intent.ingredients_include,
            ingredients_exclude=result.parsed_intent.ingredients_exclude,
            semantic_query=result.parsed_intent.semantic_query,
            use_kg=result.parsed_intent.use_kg,
            use_sql=result.parsed_intent.use_sql,
            use_vector=result.parsed_intent.use_vector,
        ),
        results=[
            RecipeResult(
                id=r.id,
                title=r.title,
                description=r.description,
                url=r.url,
                cuisine=r.cuisine,
                course=r.course,
                diet=r.diet,
                prep_time_mins=r.prep_time_mins,
                cook_time_mins=r.cook_time_mins,
                rating=r.rating,
                vote_count=r.vote_count,
                ingredients=r.ingredients,
                final_score=r.final_score,
                sources=r.sources,
            )
            for r in result.results
        ],
        source_breakdown=result.source_breakdown,
    )


@router.get("/recipes/{recipe_id}", response_model=RecipeDetailResponse)
async def get_recipe(recipe_id: int):
    """Get a single recipe by ID."""
    engine = _get_search_engine()
    recipe = engine.pg_query.get_recipe_by_id(recipe_id)

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return RecipeDetailResponse(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description,
        url=recipe.url,
        cuisine=recipe.cuisine,
        course=recipe.course,
        diet=recipe.diet,
        prep_time_mins=recipe.prep_time_mins,
        cook_time_mins=recipe.cook_time_mins,
        rating=recipe.rating,
        vote_count=recipe.vote_count,
        ingredients=recipe.ingredients,
    )
