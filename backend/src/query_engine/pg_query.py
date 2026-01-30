from dataclasses import dataclass
import psycopg
from pgvector.psycopg import register_vector
from openai import OpenAI
from src.config import get_settings
from src.query_engine.intent_parser import ParsedIntent


@dataclass
class PGRecipeResult:
    """Recipe result from PostgreSQL query."""

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
    distance: float | None = None  # Vector distance (lower is more similar)
    source: str = "sql"  # "sql", "vector", or "sql+vector"


class PostgresQuery:
    def __init__(self):
        settings = get_settings()
        self.conn = psycopg.connect(settings.postgres_url)
        self._ensure_vector_extension()
        register_vector(self.conn)
        self.openai = OpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model

    def close(self):
        self.conn.close()

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for query text."""
        response = self.openai.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    def _ensure_vector_extension(self) -> None:
        """Ensure pgvector extension exists before registering vector type."""
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        self.conn.commit()

    def get_controlled_vocab(self, max_ingredients: int = 150) -> dict[str, list[str]]:
        vocab: dict[str, list[str]] = {
            "cuisines": [],
            "courses": [],
            "diets": [],
            "ingredients": [],
        }

        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT cuisine FROM recipes WHERE cuisine IS NOT NULL ORDER BY cuisine"
            )
            vocab["cuisines"] = [row[0] for row in cur.fetchall() if row[0]]

            cur.execute(
                "SELECT DISTINCT course FROM recipes WHERE course IS NOT NULL ORDER BY course"
            )
            vocab["courses"] = [row[0] for row in cur.fetchall() if row[0]]

            cur.execute(
                "SELECT DISTINCT diet FROM recipes WHERE diet IS NOT NULL ORDER BY diet"
            )
            vocab["diets"] = [row[0] for row in cur.fetchall() if row[0]]

            cur.execute(
                """
                SELECT ingredient
                FROM (
                    SELECT unnest(ingredients) AS ingredient
                    FROM recipes
                    WHERE ingredients IS NOT NULL
                ) expanded
                WHERE ingredient IS NOT NULL AND ingredient <> ''
                GROUP BY ingredient
                ORDER BY COUNT(*) DESC
                LIMIT %s
                """,
                (max_ingredients,),
            )
            vocab["ingredients"] = [row[0] for row in cur.fetchall() if row[0]]

        return vocab

    def search_sql(self, intent: ParsedIntent, limit: int = 20) -> list[PGRecipeResult]:
        """Search recipes using SQL filters only."""
        conditions = []
        params = []

        if intent.cuisine:
            conditions.append("cuisine = %s")
            params.append(intent.cuisine)

        if intent.diet:
            conditions.append("diet = %s")
            params.append(intent.diet)

        if intent.course:
            conditions.append("course = %s")
            params.append(intent.course)

        if intent.max_prep_time_mins:
            conditions.append("prep_time_mins <= %s")
            params.append(intent.max_prep_time_mins)

        if intent.max_cook_time_mins:
            conditions.append("cook_time_mins <= %s")
            params.append(intent.max_cook_time_mins)

        # Ingredient inclusion (case-insensitive partial match)
        if intent.ingredients_include:
            for i, ing in enumerate(intent.ingredients_include):
                conditions.append(
                    f"EXISTS (SELECT 1 FROM unnest(ingredients) AS ing_{i} WHERE ing_{i} ILIKE %s)"
                )
                params.append(f"%{ing}%")

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        params.append(limit)

        query = f"""
            SELECT id, title, description, url, cuisine, course, diet,
                   prep_time_mins, cook_time_mins, rating, vote_count, ingredients
            FROM recipes
            WHERE {where_clause}
            ORDER BY rating DESC
            LIMIT %s
        """

        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return [self._row_to_result(row, source="sql") for row in cur.fetchall()]

    def search_vector(self, query_text: str, limit: int = 20) -> list[PGRecipeResult]:
        """Search recipes using vector similarity only."""
        embedding = self._generate_embedding(query_text)

        query = """
            SELECT id, title, description, url, cuisine, course, diet,
                   prep_time_mins, cook_time_mins, rating, vote_count, ingredients,
                   embedding <=> %s::vector as distance
            FROM recipes
            ORDER BY distance
            LIMIT %s
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (embedding, limit))
            return [
                self._row_to_result(row, source="vector", has_distance=True)
                for row in cur.fetchall()
            ]

    def search_hybrid(
        self, intent: ParsedIntent, limit: int = 20
    ) -> list[PGRecipeResult]:
        """Search recipes using both SQL filters and vector similarity."""
        conditions = []
        params = []

        if intent.cuisine:
            conditions.append("cuisine = %s")
            params.append(intent.cuisine)

        if intent.diet:
            conditions.append("diet = %s")
            params.append(intent.diet)

        if intent.course:
            conditions.append("course = %s")
            params.append(intent.course)

        if intent.max_prep_time_mins:
            conditions.append("prep_time_mins <= %s")
            params.append(intent.max_prep_time_mins)

        if intent.max_cook_time_mins:
            conditions.append("cook_time_mins <= %s")
            params.append(intent.max_cook_time_mins)

        # Ingredient inclusion (case-insensitive partial match)
        if intent.ingredients_include:
            for i, ing in enumerate(intent.ingredients_include):
                conditions.append(
                    f"EXISTS (SELECT 1 FROM unnest(ingredients) AS ing_{i} WHERE ing_{i} ILIKE %s)"
                )
                params.append(f"%{ing}%")

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        where_params = list(params)

        # Generate embedding for semantic query
        semantic_text = intent.semantic_query or intent.cuisine or ""
        if semantic_text:
            embedding = self._generate_embedding(semantic_text)
            query_params = [embedding, *where_params, limit]
            query = f"""
                SELECT id, title, description, url, cuisine, course, diet,
                       prep_time_mins, cook_time_mins, rating, vote_count, ingredients,
                       embedding <=> %s::vector as distance
                FROM recipes
                WHERE {where_clause}
                ORDER BY distance
                LIMIT %s
            """
        else:
            query_params = [*where_params, limit]
            query = f"""
                SELECT id, title, description, url, cuisine, course, diet,
                       prep_time_mins, cook_time_mins, rating, vote_count, ingredients,
                       NULL as distance
                FROM recipes
                WHERE {where_clause}
                ORDER BY rating DESC
                LIMIT %s
            """

        with self.conn.cursor() as cur:
            cur.execute(query, query_params)
            return [
                self._row_to_result(
                    row, source="sql+vector", has_distance=bool(semantic_text)
                )
                for row in cur.fetchall()
            ]

    def get_recipe_by_id(self, recipe_id: int) -> PGRecipeResult | None:
        """Get a single recipe by ID."""
        query = """
            SELECT id, title, description, url, cuisine, course, diet,
                   prep_time_mins, cook_time_mins, rating, vote_count, ingredients
            FROM recipes
            WHERE id = %s
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (recipe_id,))
            row = cur.fetchone()
            if row:
                return self._row_to_result(row, source="sql")
            return None

    def _row_to_result(
        self, row: tuple, source: str, has_distance: bool = False
    ) -> PGRecipeResult:
        """Convert database row to PGRecipeResult."""
        if has_distance:
            return PGRecipeResult(
                id=row[0],
                title=row[1],
                description=row[2] or "",
                url=row[3] or "",
                cuisine=row[4],
                course=row[5],
                diet=row[6],
                prep_time_mins=row[7],
                cook_time_mins=row[8],
                rating=row[9] or 0.0,
                vote_count=row[10] or 0,
                ingredients=row[11] or [],
                distance=row[12],
                source=source,
            )
        else:
            return PGRecipeResult(
                id=row[0],
                title=row[1],
                description=row[2] or "",
                url=row[3] or "",
                cuisine=row[4],
                course=row[5],
                diet=row[6],
                prep_time_mins=row[7],
                cook_time_mins=row[8],
                rating=row[9] or 0.0,
                vote_count=row[10] or 0,
                ingredients=row[11] or [],
                source=source,
            )
