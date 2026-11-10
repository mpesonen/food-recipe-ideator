#!/usr/bin/env bash
# Deploy the Recipe Ideator on a Raspberry Pi (or any arm64/amd64 Docker host).
# First run restores data from backups/; later runs just rebuild + restart.
#
#   backups/recipes.sql            Postgres dump (pg_dump, plain SQL)
#   backups/neo4j-local/neo4j.dump Neo4j 5 dump (neo4j-admin database dump)
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE=(docker compose -f docker-compose.pi.yml)
PG_DUMP=backups/recipes.sql
NEO4J_DUMP_DIR=backups/neo4j-local

[ -f .env ] || { echo "ERROR: .env missing (needs at least OPENAI_API_KEY)"; exit 1; }
set -a; source .env; set +a
PGU=${POSTGRES_USER:-recipe_user}
PGD=${POSTGRES_DB:-recipes}

echo "==> Building images (first build on a Pi takes a few minutes)"
"${COMPOSE[@]}" build

# --- Neo4j: load dump into an empty database (must be stopped while loading)
echo "==> Checking Neo4j data"
"${COMPOSE[@]}" up -d --wait neo4j
NODES=$("${COMPOSE[@]}" exec -T neo4j cypher-shell -u neo4j -p "${NEO4J_LOCAL_PASSWORD:-recipe_pass}" \
  --format plain "MATCH (n) RETURN count(n)" | tail -1)
if [ "${NODES:-0}" = "0" ]; then
  [ -f "$NEO4J_DUMP_DIR/neo4j.dump" ] || { echo "ERROR: $NEO4J_DUMP_DIR/neo4j.dump not found"; exit 1; }
  echo "    Graph empty -> loading $NEO4J_DUMP_DIR/neo4j.dump"
  "${COMPOSE[@]}" stop neo4j
  "${COMPOSE[@]}" run --rm --no-deps -v "$PWD/$NEO4J_DUMP_DIR:/backups" neo4j \
    neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true
  "${COMPOSE[@]}" up -d --wait neo4j
else
  echo "    Graph has $NODES nodes, skipping load"
fi

# --- Postgres: restore dump if the recipes table doesn't exist yet
echo "==> Checking Postgres data"
"${COMPOSE[@]}" up -d --wait postgres
HAS_TABLE=$("${COMPOSE[@]}" exec -T postgres psql -U "$PGU" -d "$PGD" -tAc \
  "SELECT to_regclass('public.recipes') IS NOT NULL")
if [ "$HAS_TABLE" != "t" ]; then
  [ -f "$PG_DUMP" ] || { echo "ERROR: $PG_DUMP not found"; exit 1; }
  echo "    Restoring $PG_DUMP (takes a minute)"
  "${COMPOSE[@]}" exec -T postgres psql -q -U "$PGU" -d "$PGD" -v ON_ERROR_STOP=1 < "$PG_DUMP" >/dev/null
else
  echo "    recipes table exists, skipping restore"
fi

echo "==> Starting all services"
"${COMPOSE[@]}" up -d --wait

for _ in $(seq 1 30); do
  if curl -sf http://localhost/api/health >/dev/null; then
    echo "==> API healthy at http://localhost"; exit 0
  fi
  sleep 2
done
echo "WARNING: health check failed -> ${COMPOSE[*]} logs api"; exit 1
