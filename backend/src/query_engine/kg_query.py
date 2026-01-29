from dataclasses import dataclass
from neo4j import GraphDatabase
from src.config import get_settings
from src.query_engine.intent_parser import ParsedIntent


@dataclass
class KGRecipeResult:
    """Recipe result from Knowledge Graph query."""
    id: int
    title: str
    rating: float
    prep_time_mins: int | None
    cook_time_mins: int | None
    score: float = 1.0  # KG match score


class KnowledgeGraphQuery:
    def __init__(self):
        settings = get_settings()
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def close(self):
        self.driver.close()

    def search(self, intent: ParsedIntent, limit: int = 20) -> list[KGRecipeResult]:
        """Search recipes using Knowledge Graph based on parsed intent."""
        # Build dynamic Cypher query based on intent
        match_clauses = ["MATCH (r:Recipe)"]
        where_clauses = []
        params = {"limit": limit}

        # Add cuisine filter
        if intent.cuisine:
            match_clauses.append("MATCH (r)-[:HAS_CUISINE]->(c:Cuisine {name: $cuisine})")
            params["cuisine"] = intent.cuisine

        # Add diet filter
        if intent.diet:
            match_clauses.append("MATCH (r)-[:HAS_DIET]->(d:Diet {name: $diet})")
            params["diet"] = intent.diet

        # Add course filter
        if intent.course:
            match_clauses.append("MATCH (r)-[:HAS_COURSE]->(co:Course {name: $course})")
            params["course"] = intent.course

        # Add ingredient filters (case-insensitive partial match)
        if intent.ingredients_include:
            for i, ingredient in enumerate(intent.ingredients_include):
                param_name = f"ing_{i}"
                match_clauses.append(
                    f"MATCH (r)-[:CONTAINS]->(i{i}:Ingredient) WHERE toLower(i{i}.name) CONTAINS toLower(${param_name})"
                )
                params[param_name] = ingredient

        # Add time constraints
        if intent.max_prep_time_mins:
            where_clauses.append("r.prep_time_mins <= $max_prep_time")
            params["max_prep_time"] = intent.max_prep_time_mins

        if intent.max_cook_time_mins:
            where_clauses.append("r.cook_time_mins <= $max_cook_time")
            params["max_cook_time"] = intent.max_cook_time_mins

        # Build query
        query_parts = match_clauses
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        query_parts.append("RETURN DISTINCT r.id as id, r.title as title, r.rating as rating, r.prep_time_mins as prep_time_mins, r.cook_time_mins as cook_time_mins")
        query_parts.append("ORDER BY r.rating DESC")
        query_parts.append("LIMIT $limit")

        query = "\n".join(query_parts)

        with self.driver.session() as session:
            result = session.run(query, params)
            recipes = []
            for record in result:
                recipes.append(KGRecipeResult(
                    id=record["id"],
                    title=record["title"],
                    rating=record["rating"] or 0.0,
                    prep_time_mins=record["prep_time_mins"],
                    cook_time_mins=record["cook_time_mins"],
                ))
            return recipes

    def find_similar_by_ingredients(self, recipe_id: int, limit: int = 10) -> list[KGRecipeResult]:
        """Find recipes with similar ingredients using graph traversal."""
        query = """
        MATCH (r1:Recipe {id: $recipe_id})-[:CONTAINS]->(i:Ingredient)<-[:CONTAINS]-(r2:Recipe)
        WHERE r1 <> r2
        WITH r2, count(i) as shared_ingredients
        RETURN r2.id as id, r2.title as title, r2.rating as rating,
               r2.prep_time_mins as prep_time_mins, r2.cook_time_mins as cook_time_mins,
               shared_ingredients
        ORDER BY shared_ingredients DESC, r2.rating DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, recipe_id=recipe_id, limit=limit)
            recipes = []
            for record in result:
                recipes.append(KGRecipeResult(
                    id=record["id"],
                    title=record["title"],
                    rating=record["rating"] or 0.0,
                    prep_time_mins=record["prep_time_mins"],
                    cook_time_mins=record["cook_time_mins"],
                    score=record["shared_ingredients"],
                ))
            return recipes

    def get_recipes_by_ingredient_combination(
        self,
        ingredients: list[str],
        limit: int = 20
    ) -> list[KGRecipeResult]:
        """Find recipes containing all specified ingredients."""
        if not ingredients:
            return []

        # Build dynamic query for multiple ingredients (case-insensitive partial match)
        match_clauses = ["MATCH (r:Recipe)"]
        for i, ing in enumerate(ingredients):
            match_clauses.append(
                f"MATCH (r)-[:CONTAINS]->(i{i}:Ingredient) WHERE toLower(i{i}.name) CONTAINS toLower($ing_{i})"
            )

        params = {f"ing_{i}": ing for i, ing in enumerate(ingredients)}
        params["limit"] = limit

        query = "\n".join(match_clauses) + """
        RETURN DISTINCT r.id as id, r.title as title, r.rating as rating,
               r.prep_time_mins as prep_time_mins, r.cook_time_mins as cook_time_mins
        ORDER BY r.rating DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, params)
            recipes = []
            for record in result:
                recipes.append(KGRecipeResult(
                    id=record["id"],
                    title=record["title"],
                    rating=record["rating"] or 0.0,
                    prep_time_mins=record["prep_time_mins"],
                    cook_time_mins=record["cook_time_mins"],
                ))
            return recipes
