from dataclasses import dataclass, field
from src.query_engine.intent_parser import ParsedIntent, parse_user_query
from src.query_engine.kg_query import KnowledgeGraphQuery, KGRecipeResult
from src.query_engine.pg_query import PostgresQuery, PGRecipeResult


@dataclass
class FusedRecipeResult:
    """Combined recipe result with source information."""

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
    sources: list[str] = field(default_factory=list)
    image_url: str | None = None


@dataclass
class Thinking:
    """LLM reasoning and routing explanation for transparency."""

    reasoning: str | None
    routing_explanation: list[str]


@dataclass
class SearchResponse:
    """Complete search response with results and metadata."""

    query: str
    parsed_intent: ParsedIntent
    results: list[FusedRecipeResult]
    source_breakdown: dict[str, int]  # Count per source
    thinking: Thinking | None = None


class RecipeSearchEngine:
    """Main search engine that orchestrates all query paths."""

    def __init__(self):
        self.kg_query = KnowledgeGraphQuery()
        self.pg_query = PostgresQuery()

    def close(self):
        self.kg_query.close()
        self.pg_query.close()

    def _generate_routing_explanation(self, intent: ParsedIntent) -> list[str]:
        """Generate human-readable explanations of which query paths are used and why."""
        explanations = []

        if intent.use_kg or intent.ingredients_include:
            if intent.ingredients_include:
                explanations.append(
                    f"Knowledge Graph: searching for recipes with {', '.join(intent.ingredients_include)}"
                )
            else:
                explanations.append(
                    "Knowledge Graph: exploring ingredient relationships"
                )

        if intent.use_sql and intent.use_vector:
            filters = []
            if intent.cuisine:
                filters.append(f"cuisine={intent.cuisine}")
            if intent.diet:
                filters.append(f"diet={intent.diet}")
            if intent.max_prep_time_mins:
                filters.append(f"prep<={intent.max_prep_time_mins}min")
            filter_str = f" ({', '.join(filters)})" if filters else ""
            explanations.append(
                f"SQL+Vector: hybrid search combining filters{filter_str} with semantic similarity"
            )
        elif intent.use_vector and intent.semantic_query:
            explanations.append(
                f"Vector: semantic search for '{intent.semantic_query}'"
            )
        elif intent.use_sql:
            filters = []
            if intent.cuisine:
                filters.append(f"cuisine={intent.cuisine}")
            if intent.diet:
                filters.append(f"diet={intent.diet}")
            if intent.course:
                filters.append(f"course={intent.course}")
            filter_str = ", ".join(filters) if filters else "structured filters"
            explanations.append(f"SQL: filtering by {filter_str}")

        if not explanations:
            explanations.append("Default: hybrid search with semantic similarity")

        return explanations

    def search(self, query: str, limit: int = 20) -> SearchResponse:
        """Execute search across all relevant query paths and fuse results."""
        # Parse user intent
        intent = parse_user_query(query)

        # Collect results from different sources
        kg_results: list[KGRecipeResult] = []
        pg_results: list[PGRecipeResult] = []

        # Execute Knowledge Graph query if relevant
        if intent.use_kg or intent.ingredients_include:
            kg_results = self.kg_query.search(intent, limit=limit * 2)

        # Execute PostgreSQL query (hybrid SQL + vector if semantic query exists)
        if intent.use_sql and intent.use_vector:
            pg_results = self.pg_query.search_hybrid(intent, limit=limit * 2)
        elif intent.use_vector and intent.semantic_query:
            pg_results = self.pg_query.search_vector(
                intent.semantic_query, limit=limit * 2
            )
        elif intent.use_sql:
            pg_results = self.pg_query.search_sql(intent, limit=limit * 2)
        else:
            # Default to hybrid search
            pg_results = self.pg_query.search_hybrid(intent, limit=limit * 2)

        # Fuse results
        fused = self._fuse_results(kg_results, pg_results, limit)

        # Calculate source breakdown
        source_breakdown = {"kg": 0, "sql": 0, "vector": 0, "sql+vector": 0}
        for result in fused:
            for source in result.sources:
                if source in source_breakdown:
                    source_breakdown[source] += 1

        # Generate thinking/reasoning data
        thinking = Thinking(
            reasoning=intent.reasoning,
            routing_explanation=self._generate_routing_explanation(intent),
        )

        return SearchResponse(
            query=query,
            parsed_intent=intent,
            results=fused,
            source_breakdown=source_breakdown,
            thinking=thinking,
        )

    def _fuse_results(
        self,
        kg_results: list[KGRecipeResult],
        pg_results: list[PGRecipeResult],
        limit: int,
    ) -> list[FusedRecipeResult]:
        """Fuse results from different sources with scoring."""
        # Use recipe ID as key for deduplication
        results_by_id: dict[int, FusedRecipeResult] = {}

        # Process PostgreSQL results (have full recipe data)
        for pg_result in pg_results:
            # Calculate score based on vector distance and rating
            if pg_result.distance is not None:
                # Convert distance to similarity (lower distance = higher similarity)
                vector_score = 1.0 / (1.0 + pg_result.distance)
            else:
                vector_score = 0.5

            # Combine with rating (normalized to 0-1)
            rating_score = pg_result.rating / 5.0 if pg_result.rating else 0.5
            final_score = 0.6 * vector_score + 0.4 * rating_score

            results_by_id[pg_result.id] = FusedRecipeResult(
                id=pg_result.id,
                title=pg_result.title,
                description=pg_result.description,
                url=pg_result.url,
                cuisine=pg_result.cuisine,
                course=pg_result.course,
                diet=pg_result.diet,
                prep_time_mins=pg_result.prep_time_mins,
                cook_time_mins=pg_result.cook_time_mins,
                rating=pg_result.rating,
                vote_count=pg_result.vote_count,
                ingredients=pg_result.ingredients,
                final_score=final_score,
                sources=[pg_result.source],
            )

        # Process KG results and merge/boost scores
        for kg_result in kg_results:
            if kg_result.id in results_by_id:
                # Boost score for recipes found in both sources
                existing = results_by_id[kg_result.id]
                existing.final_score *= 1.2  # 20% boost
                if "kg" not in existing.sources:
                    existing.sources.append("kg")
            else:
                # Need to fetch full recipe data from PostgreSQL
                full_recipe = self.pg_query.get_recipe_by_id(kg_result.id)
                if full_recipe:
                    rating_score = kg_result.rating / 5.0 if kg_result.rating else 0.5
                    results_by_id[kg_result.id] = FusedRecipeResult(
                        id=full_recipe.id,
                        title=full_recipe.title,
                        description=full_recipe.description,
                        url=full_recipe.url,
                        cuisine=full_recipe.cuisine,
                        course=full_recipe.course,
                        diet=full_recipe.diet,
                        prep_time_mins=full_recipe.prep_time_mins,
                        cook_time_mins=full_recipe.cook_time_mins,
                        rating=full_recipe.rating,
                        vote_count=full_recipe.vote_count,
                        ingredients=full_recipe.ingredients,
                        final_score=rating_score,
                        sources=["kg"],
                    )

        # Sort by final score and limit
        sorted_results = sorted(
            results_by_id.values(), key=lambda x: x.final_score, reverse=True
        )

        return sorted_results[:limit]
