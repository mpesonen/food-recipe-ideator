import psycopg
from pgvector.psycopg import register_vector
from openai import OpenAI
from src.data_ingestion.csv_parser import Recipe
from src.config import get_settings


class PostgresLoader:
    def __init__(self):
        settings = get_settings()
        self.conn = psycopg.connect(settings.postgres_url)
        register_vector(self.conn)
        self.openai = OpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model
        self.embedding_dimensions = settings.embedding_dimensions

    def close(self):
        self.conn.close()

    def create_schema(self):
        """Create the recipes table with pgvector support."""
        with self.conn.cursor() as cur:
            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Drop existing table if exists
            cur.execute("DROP TABLE IF EXISTS recipes")

            # Create recipes table
            cur.execute(f"""
                CREATE TABLE recipes (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT,
                    description TEXT,
                    cuisine TEXT,
                    course TEXT,
                    diet TEXT,
                    prep_time_mins INTEGER,
                    cook_time_mins INTEGER,
                    rating FLOAT,
                    vote_count INTEGER,
                    ingredients TEXT[],
                    instructions TEXT,
                    author TEXT,
                    tags TEXT,
                    category TEXT,
                    embedding vector({self.embedding_dimensions})
                )
            """)

            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON recipes(cuisine)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_diet ON recipes(diet)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_course ON recipes(course)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_prep_time ON recipes(prep_time_mins)")

            self.conn.commit()

    def create_vector_index(self):
        """Create IVFFlat index for vector similarity search after data is loaded."""
        with self.conn.cursor() as cur:
            # IVFFlat index - lists should be sqrt(n) for best performance
            # For ~8000 recipes, sqrt(8000) ≈ 89, so we use 100 lists
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_recipes_embedding
                ON recipes USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            self.conn.commit()

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text using OpenAI."""
        response = self.openai.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    def _create_embedding_text(self, recipe: Recipe) -> str:
        """Create text for embedding from recipe fields."""
        parts = [f"Title: {recipe.title}"]

        if recipe.description:
            parts.append(f"Description: {recipe.description}")

        if recipe.cuisine:
            parts.append(f"Cuisine: {recipe.cuisine}")

        if recipe.diet:
            parts.append(f"Diet: {recipe.diet}")

        if recipe.course:
            parts.append(f"Course: {recipe.course}")

        if recipe.ingredients:
            parts.append(f"Ingredients: {', '.join(recipe.ingredients[:10])}")  # Limit ingredients

        if recipe.tags:
            parts.append(f"Tags: {recipe.tags}")

        return " | ".join(parts)

    def load_recipes(self, recipes: list[Recipe], batch_size: int = 50):
        """Load recipes with embeddings into PostgreSQL."""
        with self.conn.cursor() as cur:
            for i in range(0, len(recipes), batch_size):
                batch = recipes[i:i + batch_size]

                # Generate embeddings for batch
                texts = [self._create_embedding_text(r) for r in batch]
                embeddings = self._batch_generate_embeddings(texts)

                # Insert batch
                for recipe, embedding in zip(batch, embeddings):
                    cur.execute(
                        """
                        INSERT INTO recipes (
                            id, title, url, description, cuisine, course, diet,
                            prep_time_mins, cook_time_mins, rating, vote_count,
                            ingredients, instructions, author, tags, category, embedding
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            recipe.id,
                            recipe.title,
                            recipe.url,
                            recipe.description,
                            recipe.cuisine,
                            recipe.course,
                            recipe.diet,
                            recipe.prep_time_mins,
                            recipe.cook_time_mins,
                            recipe.rating,
                            recipe.vote_count,
                            recipe.ingredients,
                            recipe.instructions,
                            recipe.author,
                            recipe.tags,
                            recipe.category,
                            embedding,
                        )
                    )

                self.conn.commit()
                print(f"Loaded {min(i + batch_size, len(recipes))}/{len(recipes)} recipes to PostgreSQL")

    def _batch_generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in a single API call."""
        response = self.openai.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def get_stats(self) -> dict:
        """Get statistics about the loaded data."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM recipes")
            total = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT cuisine) FROM recipes WHERE cuisine IS NOT NULL")
            cuisines = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT diet) FROM recipes WHERE diet IS NOT NULL")
            diets = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT course) FROM recipes WHERE course IS NOT NULL")
            courses = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM recipes WHERE embedding IS NOT NULL")
            with_embeddings = cur.fetchone()[0]

            return {
                'total_recipes': total,
                'cuisines': cuisines,
                'diets': diets,
                'courses': courses,
                'with_embeddings': with_embeddings,
            }
