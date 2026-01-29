# Tasks

## Phase 1: Project Setup

- [ ] Create project structure (backend/, frontend/ directories)
- [ ] Initialize backend with uv (`uv init`, pyproject.toml)
- [ ] Add pytest + pytest-asyncio as dev dependencies
- [ ] Create docker-compose.yml for Neo4j + PostgreSQL (pgvector) + API
- [ ] Create backend/src/config.py for API keys and connections
- [ ] Initialize frontend with Vite + React + TypeScript

## Phase 2: Data Ingestion

- [ ] Create backend/src/data_ingestion/csv_parser.py - parse and clean CSV
- [ ] Create backend/src/data_ingestion/kg_loader.py - load into Neo4j
- [ ] Create backend/src/data_ingestion/pg_loader.py - load into PostgreSQL + embeddings
- [ ] Run ingestion and verify data in both databases

## Phase 3: Query Engine

- [ ] Create backend/src/query_engine/intent_parser.py - LLM query understanding
- [ ] Create backend/src/query_engine/kg_query.py - Cypher query builder
- [ ] Create backend/src/query_engine/pg_query.py - SQL + vector queries
- [ ] Create backend/src/query_engine/fusion.py - combine and rank results
- [ ] Test query engine with sample queries

## Phase 4: Backend API

- [ ] Create backend/src/api/main.py - FastAPI app
- [ ] Create backend/src/api/routes.py - /search, /recipes/{id}, /health
- [ ] Add CORS configuration for frontend
- [ ] Create backend/Dockerfile

## Phase 5: Backend Tests

- [ ] Create backend/tests/conftest.py - pytest fixtures (mock DBs, test data)
- [ ] Create backend/tests/test_csv_parser.py - CSV parsing and cleaning
- [ ] Create backend/tests/test_intent_parser.py - LLM intent extraction (mock OpenAI)
- [ ] Create backend/tests/test_kg_query.py - Cypher query generation
- [ ] Create backend/tests/test_pg_query.py - SQL + vector query generation
- [ ] Create backend/tests/test_api.py - FastAPI endpoint tests
- [ ] Run tests: `uv run pytest`

## Phase 6: Frontend

- [ ] Set up API service layer (src/services/api.ts)
- [ ] Create search input component
- [ ] Create recipe results component
- [ ] Create recipe detail view
- [ ] Display query source breakdown (KG/SQL/Vector) for demo
- [ ] Add example query buttons
- [ ] Create frontend/Dockerfile

## Phase 7: Local Integration Testing

- [ ] Run full stack with `docker-compose up`
- [ ] Verify Neo4j browser accessible at localhost:7474
- [ ] Verify PostgreSQL connection and pgvector extension
- [ ] Run data ingestion scripts
- [ ] Verify data in both databases (counts, sample queries)
- [ ] Test API endpoints manually (curl/Postman)
- [ ] Test frontend search functionality end-to-end
- [ ] Verify query source breakdown displays correctly (KG/SQL/Vector)
- [ ] Test all demo queries

## Phase 8: AWS Deployment (EC2 + Docker Compose)

- [ ] Create docker-compose.prod.yml (production config, nginx for frontend)
- [ ] Launch EC2 instance (t3.medium+)
- [ ] Install Docker + Docker Compose on EC2
- [ ] Clone repo and configure environment variables
- [ ] Run `docker-compose -f docker-compose.prod.yml up -d`
- [ ] Run data ingestion on EC2
- [ ] Configure security groups (ports 80, 443)
- [ ] End-to-end testing with EC2 public IP

---

## Demo Queries to Test

- "Indian vegetarian quick" → SQL filters + vector ranking
- "healthy breakfast under 20 minutes" → SQL time filter + semantic search
- "comfort food for dinner" → Vector-heavy (semantic concept)
- "recipes with chicken and rice" → KG ingredient relationships
- "easy dessert" → Vector search + course filter
