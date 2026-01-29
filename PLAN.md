# LLM-Powered Food Recipe Ideator

## Overview
A demo application combining **Knowledge Graph**, **Vector Search**, and **Relational Queries** to intelligently query ~8,000 food recipes. An LLM orchestrates queries across all three data stores for optimal results.

**Deployment:** AWS-hosted
**Frontend:** React + Vite
**Backend:** FastAPI

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    EC2 Instance (Docker Compose)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│  │  React   │  │ FastAPI  │  │ PostgreSQL│  │   Neo4j     │  │
│  │ (nginx)  │  │  :8000   │  │ +pgvector │  │   :7474     │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │
└──────────────────────────────────────────────────────────────┘
         Same docker-compose.yml for local & production
```

### Query Flow

```
User Query ("Indian vegetarian quick")
        │
        ▼
┌───────────────────┐
│  LLM Orchestrator │  ← Parses intent, decides query strategy
└───────────────────┘
        │
   ┌────┼────────┐
   ▼    ▼        ▼
┌────┐ ┌────┐ ┌────────┐
│ KG │ │ SQL│ │ Vector │
└────┘ └────┘ └────────┘
 Neo4j  PostgreSQL + pgvector
   │       │        │
   └───────┼────────┘
           ▼
   ┌───────────────┐
   │ Result Fusion │
   └───────────────┘
           │
           ▼
   Final Recommendations
```

### Three Query Paths

| Path | Technology | Best For |
|------|------------|----------|
| Knowledge Graph | Neo4j | Relationship traversal, "recipes with similar ingredients to X" |
| Relational | PostgreSQL | Structured filters, aggregations, ratings, time constraints |
| Vector | pgvector | Semantic similarity, "comfort food", "healthy", fuzzy matching |

---

## Data Model

### Knowledge Graph (Neo4j)

**Nodes:**
- `Recipe` - id, title
- `Cuisine` - name (Mexican, Indian, Italian...)
- `Diet` - name (Vegetarian, Vegan, Non-Vegetarian...)
- `Course` - name (Dinner, Lunch, Breakfast, Snack...)
- `Ingredient` - name (extracted from ingredients field)

**Relationships:**
- `(Recipe)-[:HAS_CUISINE]->(Cuisine)`
- `(Recipe)-[:HAS_DIET]->(Diet)`
- `(Recipe)-[:HAS_COURSE]->(Course)`
- `(Recipe)-[:CONTAINS]->(Ingredient)`

### PostgreSQL + pgvector

**Tables:**

```sql
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    title TEXT,
    description TEXT,
    url TEXT,
    cuisine TEXT,
    course TEXT,
    diet TEXT,
    prep_time_mins INT,
    cook_time_mins INT,
    rating FLOAT,
    vote_count INT,
    ingredients TEXT[],
    instructions TEXT,
    embedding vector(1536)  -- pgvector for semantic search
);

CREATE INDEX ON recipes USING ivfflat (embedding vector_cosine_ops);
```

---

## Query Processing Flow

Example: "Indian vegetarian quick"

1. **LLM Intent Parsing** → Extracts:
   - Cuisine filter: "Indian"
   - Diet filter: "Vegetarian"
   - Time constraint: "quick" → prep_time < 30 min
   - Semantic query: "quick Indian vegetarian meal"

2. **Query Routing** → LLM decides:
   - Use **SQL** for structured filters (cuisine, diet, time)
   - Use **Vector** for semantic ranking
   - Use **KG** if ingredient relationships needed

3. **PostgreSQL Query**:

   ```sql
   SELECT *, embedding <=> $query_embedding AS distance
   FROM recipes
   WHERE cuisine = 'Indian'
     AND diet = 'Vegetarian'
     AND prep_time_mins <= 30
   ORDER BY distance
   LIMIT 10;
   ```

4. **Result Fusion** → Combine scores, rank by relevance + rating

---

## Technology Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| LLM | OpenAI GPT-4o-mini | Intent parsing |
| Knowledge Graph | Neo4j (Docker) | Graph queries |
| Relational + Vector | PostgreSQL + pgvector (Docker) | SQL + vector search |
| Embeddings | text-embedding-3-small | 1536 dimensions |
| Backend | FastAPI (Docker) | REST API |
| Frontend | React + Vite (nginx Docker) | Static build served by nginx |
| Deployment | EC2 + Docker Compose | Same setup local & prod |

---

## Project Structure

```
food-recipe-ideator/
├── recipes-data/
│   └── food_recipes.csv
├── backend/
│   ├── src/
│   │   ├── data_ingestion/
│   │   │   ├── csv_parser.py
│   │   │   ├── kg_loader.py
│   │   │   └── pg_loader.py
│   │   ├── query_engine/
│   │   │   ├── intent_parser.py
│   │   │   ├── kg_query.py
│   │   │   ├── pg_query.py
│   │   │   └── fusion.py
│   │   ├── api/
│   │   │   ├── main.py
│   │   │   └── routes.py
│   │   └── config.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_csv_parser.py
│   │   ├── test_intent_parser.py
│   │   ├── test_kg_query.py
│   │   ├── test_pg_query.py
│   │   └── test_api.py
│   ├── pyproject.toml
│   ├── uv.lock
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml          # Local dev: Neo4j + PostgreSQL + API
├── PLAN.md
└── TASKS.md
```

---

## API Endpoints

```
POST /api/search
  Body: { "query": "Indian vegetarian quick" }
  Response: {
    "results": [...],
    "sources": { "kg": [...], "sql": [...], "vector": [...] }
  }

GET /api/recipes/{id}
  Response: { "recipe": {...} }

GET /api/health
  Response: { "status": "ok" }
```

---

## Verification

**Local Development:**

1. `docker-compose up` → All services running
2. Neo4j browser at http://localhost:7474
3. pgAdmin at http://localhost:5050 (default `admin@recipes.local` / `admin123`; override via `PGADMIN_DEFAULT_EMAIL` & `PGADMIN_DEFAULT_PASSWORD`)
4. API at http://localhost:8000
5. Frontend at http://localhost:3000
6. Run ingestion: `docker-compose exec api python -m src.data_ingestion.run`
7. Test search: `curl -X POST localhost:8000/api/search -d '{"query": "Indian vegetarian"}'`

**AWS Deployment:**

1. Launch EC2 instance (t3.medium or larger)
2. Install Docker + Docker Compose
3. Clone repo, set environment variables
4. `docker-compose -f docker-compose.prod.yml up -d`
5. Run ingestion once
6. Test with EC2 public IP
