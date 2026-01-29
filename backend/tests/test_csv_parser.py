import pytest
from src.data_ingestion.csv_parser import (
    parse_time_to_minutes,
    parse_ingredients,
    clean_text,
    get_unique_values,
)


class TestParseTimeToMinutes:
    def test_minutes_only(self):
        assert parse_time_to_minutes("15 M") == 15
        assert parse_time_to_minutes("30 M") == 30

    def test_hours_only(self):
        assert parse_time_to_minutes("1 H") == 60
        assert parse_time_to_minutes("2 H") == 120

    def test_hours_and_minutes(self):
        assert parse_time_to_minutes("1 H 30 M") == 90
        assert parse_time_to_minutes("2 H 15 M") == 135

    def test_lowercase(self):
        assert parse_time_to_minutes("15 m") == 15
        assert parse_time_to_minutes("1 h 30 m") == 90

    def test_none_or_empty(self):
        assert parse_time_to_minutes(None) is None
        assert parse_time_to_minutes("") is None
        assert parse_time_to_minutes("   ") is None

    def test_invalid_format(self):
        assert parse_time_to_minutes("quick") is None


class TestParseIngredients:
    def test_pipe_separated(self):
        result = parse_ingredients("Chicken|Butter|Tomato")
        assert result == ["Chicken", "Butter", "Tomato"]

    def test_with_whitespace(self):
        result = parse_ingredients("Chicken | Butter | Tomato")
        assert result == ["Chicken", "Butter", "Tomato"]

    def test_empty_entries(self):
        result = parse_ingredients("Chicken||Butter")
        assert result == ["Chicken", "Butter"]

    def test_none_or_empty(self):
        assert parse_ingredients(None) == []
        assert parse_ingredients("") == []


class TestCleanText:
    def test_normal_text(self):
        assert clean_text("Hello World") == "Hello World"

    def test_whitespace(self):
        assert clean_text("  Hello World  ") == "Hello World"

    def test_none(self):
        assert clean_text(None) == ""


class TestGetUniqueValues:
    def test_extracts_unique_values(self, sample_recipes):
        unique = get_unique_values(sample_recipes)

        assert "Indian" in unique["cuisines"]
        assert "Italian" in unique["cuisines"]
        assert len(unique["cuisines"]) == 2

        assert "Vegetarian" in unique["diets"]
        assert "Non-Vegetarian" in unique["diets"]

        assert "Dinner" in unique["courses"]
        assert "Lunch" in unique["courses"]

        assert "Chicken" in unique["ingredients"]
        assert "Pasta" in unique["ingredients"]
