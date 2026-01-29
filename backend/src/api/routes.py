import json
from typing import TYPE_CHECKING, AsyncGenerator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.query_engine.intent_parser import parse_user_query, stream_reasoning
from src.services.recipe_preview import get_recipe_preview_image

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
    image_url: str | None = None
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


class ThinkingResponse(BaseModel):
    reasoning: str | None
    routing_explanation: list[str]


class SearchResponse(BaseModel):
    query: str
    parsed_intent: ParsedIntentResponse
    results: list[RecipeResult]
    source_breakdown: dict[str, int]
    thinking: ThinkingResponse


class RecipeDetailResponse(BaseModel):
    id: int
    title: str
    description: str
    url: str
    image_url: str | None = None
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
                image_url=r.image_url,
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
        thinking=ThinkingResponse(
            reasoning=result.thinking.reasoning if result.thinking else None,
            routing_explanation=result.thinking.routing_explanation
            if result.thinking
            else [],
        ),
    )


def _format_sse(event: str, data: dict) -> str:
    """Format data as Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _generate_search_stream(query: str, limit: int) -> AsyncGenerator[str, None]:
    """Generate SSE events for streaming search progress."""
    engine = _get_search_engine()

    # Phase 1: Stream reasoning
    yield _format_sse("phase", {"phase": "reasoning"})

    async for chunk in stream_reasoning(query):
        yield _format_sse("reasoning_chunk", {"text": chunk})

    # Phase 2: Parse intent with JSON mode
    yield _format_sse("phase", {"phase": "parsing"})
    intent = parse_user_query(query)
    routing = engine._generate_routing_explanation(intent)

    yield _format_sse(
        "intent",
        {
            "parsed_intent": {
                "cuisine": intent.cuisine,
                "diet": intent.diet,
                "course": intent.course,
                "max_prep_time_mins": intent.max_prep_time_mins,
                "max_cook_time_mins": intent.max_cook_time_mins,
                "ingredients_include": intent.ingredients_include,
                "ingredients_exclude": intent.ingredients_exclude,
                "semantic_query": intent.semantic_query,
                "use_kg": intent.use_kg,
                "use_sql": intent.use_sql,
                "use_vector": intent.use_vector,
            },
            "routing_explanation": routing,
        },
    )

    # Phase 3: Execute queries
    yield _format_sse("phase", {"phase": "querying"})
    result = engine.search(query, limit=limit)

    # Phase 4: Send results
    yield _format_sse("phase", {"phase": "complete"})
    yield _format_sse(
        "results",
        {
            "query": result.query,
            "results": [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "url": r.url,
                    "image_url": r.image_url,
                    "cuisine": r.cuisine,
                    "course": r.course,
                    "diet": r.diet,
                    "prep_time_mins": r.prep_time_mins,
                    "cook_time_mins": r.cook_time_mins,
                    "rating": r.rating,
                    "vote_count": r.vote_count,
                    "ingredients": r.ingredients,
                    "final_score": r.final_score,
                    "sources": r.sources,
                }
                for r in result.results
            ],
            "source_breakdown": result.source_breakdown,
        },
    )


@router.post("/search-stream")
async def search_recipes_stream(request: SearchRequest):
    """
    Stream search results with real-time LLM reasoning visibility.

    Returns Server-Sent Events with phases:
    - reasoning: LLM thinking streamed character-by-character
    - parsing: Structured intent extraction
    - querying: Database queries in progress
    - complete: Final results
    """
    return StreamingResponse(
        _generate_search_stream(request.query, request.limit),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
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
        image_url=recipe.image_url if hasattr(recipe, "image_url") else None,
    )


@router.get("/recipes/preview")
async def recipe_preview(url: str = Query(..., description="Recipe URL to inspect")):
    image_url = await get_recipe_preview_image(url)
    if not image_url:
        raise HTTPException(status_code=404, detail="Preview image not found")
    return {"image_url": image_url}
