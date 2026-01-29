from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.query_engine.fusion import RecipeSearchEngine


# Global search engine instance
search_engine: RecipeSearchEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize and cleanup resources."""
    global search_engine
    # Startup
    search_engine = RecipeSearchEngine()
    yield
    # Shutdown
    if search_engine:
        search_engine.close()


app = FastAPI(
    title="Recipe Ideator API",
    description="LLM-powered recipe search using Knowledge Graph + Vector Database",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")


def get_search_engine() -> RecipeSearchEngine:
    """Get the global search engine instance."""
    if search_engine is None:
        raise RuntimeError("Search engine not initialized")
    return search_engine
