from neo4j import GraphDatabase
from src.data_ingestion.csv_parser import Recipe
from src.config import get_settings


class KnowledgeGraphLoader:
    def __init__(self):
        settings = get_settings()
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Clear all nodes and relationships."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def create_constraints(self):
        """Create uniqueness constraints for better performance."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Recipe) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Cuisine) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Diet) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (co:Course) REQUIRE co.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.name IS UNIQUE",
        ]
        with self.driver.session() as session:
            for constraint in constraints:
                session.run(constraint)

    def load_recipes(self, recipes: list[Recipe], batch_size: int = 100):
        """Load recipes and their relationships into Neo4j."""
        # First, create all unique nodes
        self._create_dimension_nodes(recipes)

        # Then create recipes with relationships in batches
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            self._load_recipe_batch(batch)
            print(f"Loaded {min(i + batch_size, len(recipes))}/{len(recipes)} recipes to Neo4j")

    def _create_dimension_nodes(self, recipes: list[Recipe]):
        """Create unique Cuisine, Diet, Course, and Ingredient nodes."""
        cuisines = set()
        diets = set()
        courses = set()
        ingredients = set()

        for recipe in recipes:
            if recipe.cuisine:
                cuisines.add(recipe.cuisine)
            if recipe.diet:
                diets.add(recipe.diet)
            if recipe.course:
                courses.add(recipe.course)
            for ing in recipe.ingredients:
                ingredients.add(ing)

        with self.driver.session() as session:
            # Create cuisines
            if cuisines:
                session.run(
                    "UNWIND $names AS name MERGE (c:Cuisine {name: name})",
                    names=list(cuisines)
                )

            # Create diets
            if diets:
                session.run(
                    "UNWIND $names AS name MERGE (d:Diet {name: name})",
                    names=list(diets)
                )

            # Create courses
            if courses:
                session.run(
                    "UNWIND $names AS name MERGE (co:Course {name: name})",
                    names=list(courses)
                )

            # Create ingredients in batches (can be many)
            ing_list = list(ingredients)
            for i in range(0, len(ing_list), 500):
                batch = ing_list[i:i + 500]
                session.run(
                    "UNWIND $names AS name MERGE (i:Ingredient {name: name})",
                    names=batch
                )

    def _load_recipe_batch(self, recipes: list[Recipe]):
        """Load a batch of recipes with their relationships."""
        with self.driver.session() as session:
            for recipe in recipes:
                # Create recipe node
                session.run(
                    """
                    MERGE (r:Recipe {id: $id})
                    SET r.title = $title,
                        r.rating = $rating,
                        r.prep_time_mins = $prep_time_mins,
                        r.cook_time_mins = $cook_time_mins
                    """,
                    id=recipe.id,
                    title=recipe.title,
                    rating=recipe.rating,
                    prep_time_mins=recipe.prep_time_mins,
                    cook_time_mins=recipe.cook_time_mins,
                )

                # Create relationships
                if recipe.cuisine:
                    session.run(
                        """
                        MATCH (r:Recipe {id: $recipe_id})
                        MATCH (c:Cuisine {name: $cuisine})
                        MERGE (r)-[:HAS_CUISINE]->(c)
                        """,
                        recipe_id=recipe.id,
                        cuisine=recipe.cuisine,
                    )

                if recipe.diet:
                    session.run(
                        """
                        MATCH (r:Recipe {id: $recipe_id})
                        MATCH (d:Diet {name: $diet})
                        MERGE (r)-[:HAS_DIET]->(d)
                        """,
                        recipe_id=recipe.id,
                        diet=recipe.diet,
                    )

                if recipe.course:
                    session.run(
                        """
                        MATCH (r:Recipe {id: $recipe_id})
                        MATCH (co:Course {name: $course})
                        MERGE (r)-[:HAS_COURSE]->(co)
                        """,
                        recipe_id=recipe.id,
                        course=recipe.course,
                    )

                # Create ingredient relationships
                for ingredient in recipe.ingredients:
                    session.run(
                        """
                        MATCH (r:Recipe {id: $recipe_id})
                        MATCH (i:Ingredient {name: $ingredient})
                        MERGE (r)-[:CONTAINS]->(i)
                        """,
                        recipe_id=recipe.id,
                        ingredient=ingredient,
                    )

    def get_stats(self) -> dict:
        """Get statistics about the loaded data."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (r:Recipe) WITH count(r) as recipes
                MATCH (c:Cuisine) WITH recipes, count(c) as cuisines
                MATCH (d:Diet) WITH recipes, cuisines, count(d) as diets
                MATCH (co:Course) WITH recipes, cuisines, diets, count(co) as courses
                MATCH (i:Ingredient) WITH recipes, cuisines, diets, courses, count(i) as ingredients
                RETURN recipes, cuisines, diets, courses, ingredients
                """
            )
            record = result.single()
            return {
                'recipes': record['recipes'],
                'cuisines': record['cuisines'],
                'diets': record['diets'],
                'courses': record['courses'],
                'ingredients': record['ingredients'],
            }
