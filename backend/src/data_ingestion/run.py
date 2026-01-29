#!/usr/bin/env python
"""Data ingestion script to load recipes into Neo4j and PostgreSQL."""

import argparse
from pathlib import Path

from src.data_ingestion.csv_parser import load_recipes
from src.data_ingestion.kg_loader import KnowledgeGraphLoader
from src.data_ingestion.pg_loader import PostgresLoader


def main():
    parser = argparse.ArgumentParser(description="Load recipe data into databases")
    parser.add_argument(
        "--csv",
        type=str,
        default="recipes-data/food_recipes.csv",
        help="Path to the CSV file"
    )
    parser.add_argument(
        "--skip-neo4j",
        action="store_true",
        help="Skip loading to Neo4j"
    )
    parser.add_argument(
        "--skip-postgres",
        action="store_true",
        help="Skip loading to PostgreSQL"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of recipes to load (for testing)"
    )

    args = parser.parse_args()

    # Load recipes from CSV
    csv_path = Path(args.csv)
    if not csv_path.exists():
        # Try from app root in Docker
        csv_path = Path("/app") / args.csv

    print(f"Loading recipes from {csv_path}...")
    recipes = load_recipes(csv_path)

    if args.limit:
        recipes = recipes[:args.limit]

    print(f"Loaded {len(recipes)} recipes from CSV")

    # Load to Neo4j
    if not args.skip_neo4j:
        print("\n--- Loading to Neo4j ---")
        kg_loader = KnowledgeGraphLoader()
        try:
            print("Creating constraints...")
            kg_loader.create_constraints()

            print("Clearing existing data...")
            kg_loader.clear_database()

            print("Loading recipes...")
            kg_loader.load_recipes(recipes)

            stats = kg_loader.get_stats()
            print(f"\nNeo4j Stats:")
            print(f"  Recipes: {stats['recipes']}")
            print(f"  Cuisines: {stats['cuisines']}")
            print(f"  Diets: {stats['diets']}")
            print(f"  Courses: {stats['courses']}")
            print(f"  Ingredients: {stats['ingredients']}")
        finally:
            kg_loader.close()

    # Load to PostgreSQL
    if not args.skip_postgres:
        print("\n--- Loading to PostgreSQL ---")
        pg_loader = PostgresLoader()
        try:
            print("Creating schema...")
            pg_loader.create_schema()

            print("Loading recipes with embeddings...")
            pg_loader.load_recipes(recipes)

            print("Creating vector index...")
            pg_loader.create_vector_index()

            stats = pg_loader.get_stats()
            print(f"\nPostgreSQL Stats:")
            print(f"  Total recipes: {stats['total_recipes']}")
            print(f"  Cuisines: {stats['cuisines']}")
            print(f"  Diets: {stats['diets']}")
            print(f"  Courses: {stats['courses']}")
            print(f"  With embeddings: {stats['with_embeddings']}")
        finally:
            pg_loader.close()

    print("\n--- Data ingestion complete! ---")


if __name__ == "__main__":
    main()
