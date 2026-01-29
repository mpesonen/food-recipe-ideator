import re
from pathlib import Path
from dataclasses import dataclass
import pandas as pd


@dataclass
class Recipe:
    id: int
    title: str
    url: str
    description: str
    cuisine: str
    course: str
    diet: str
    prep_time_mins: int | None
    cook_time_mins: int | None
    rating: float
    vote_count: int
    ingredients: list[str]
    instructions: str
    author: str
    tags: str
    category: str


def parse_time_to_minutes(time_str: str | None) -> int | None:
    """Convert time string like '15 M', '1 H 30 M' to minutes."""
    if not time_str or pd.isna(time_str):
        return None

    time_str = str(time_str).strip().upper()
    if not time_str:
        return None

    total_minutes = 0

    # Match hours
    hours_match = re.search(r'(\d+)\s*H', time_str)
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60

    # Match minutes
    mins_match = re.search(r'(\d+)\s*M', time_str)
    if mins_match:
        total_minutes += int(mins_match.group(1))

    return total_minutes if total_minutes > 0 else None


def parse_ingredients(ingredients_str: str | None) -> list[str]:
    """Parse pipe-separated ingredients into a list."""
    if not ingredients_str or pd.isna(ingredients_str):
        return []

    ingredients = [
        ing.strip()
        for ing in str(ingredients_str).split('|')
        if ing.strip()
    ]
    return ingredients


def clean_text(text: str | None) -> str:
    """Clean text field, handling NaN and whitespace."""
    if text is None or pd.isna(text):
        return ""
    return str(text).strip()


def load_recipes(csv_path: str | Path) -> list[Recipe]:
    """Load and parse recipes from CSV file."""
    df = pd.read_csv(csv_path)

    recipes = []
    for idx, row in df.iterrows():
        recipe = Recipe(
            id=idx,
            title=clean_text(row.get('recipe_title')),
            url=clean_text(row.get('url')),
            description=clean_text(row.get('description')),
            cuisine=clean_text(row.get('cuisine')),
            course=clean_text(row.get('course')),
            diet=clean_text(row.get('diet')),
            prep_time_mins=parse_time_to_minutes(row.get('prep_time')),
            cook_time_mins=parse_time_to_minutes(row.get('cook_time')),
            rating=float(row.get('rating', 0)) if pd.notna(row.get('rating')) else 0.0,
            vote_count=int(row.get('vote_count', 0)) if pd.notna(row.get('vote_count')) else 0,
            ingredients=parse_ingredients(row.get('ingredients')),
            instructions=clean_text(row.get('instructions')),
            author=clean_text(row.get('author')),
            tags=clean_text(row.get('tags')),
            category=clean_text(row.get('category')),
        )
        recipes.append(recipe)

    return recipes


def get_unique_values(recipes: list[Recipe]) -> dict[str, set[str]]:
    """Extract unique values for cuisines, courses, diets, and ingredients."""
    cuisines = set()
    courses = set()
    diets = set()
    ingredients = set()

    for recipe in recipes:
        if recipe.cuisine:
            cuisines.add(recipe.cuisine)
        if recipe.course:
            courses.add(recipe.course)
        if recipe.diet:
            diets.add(recipe.diet)
        for ing in recipe.ingredients:
            ingredients.add(ing)

    return {
        'cuisines': cuisines,
        'courses': courses,
        'diets': diets,
        'ingredients': ingredients,
    }
