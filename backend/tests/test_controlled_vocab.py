from src.query_engine.intent_parser import ParsedIntent
from src.services.controlled_vocab import (
    INGREDIENT_KEYWORD_HINTS,
    apply_vocab_constraints,
    map_value_to_vocab,
)


def test_map_value_to_vocab_keyword_hint_soy():
    options = ["Tofu", "Tempeh", "Paneer"]
    result = map_value_to_vocab(
        "soy-based bean protein",
        options,
        keyword_hints=INGREDIENT_KEYWORD_HINTS,
    )
    assert result == "Tofu"


def test_apply_vocab_constraints_normalizes_ingredients():
    vocab = {
        "cuisines": [],
        "courses": [],
        "diets": [],
        "ingredients": ["Tofu", "Tempeh", "Paneer"],
    }
    intent = ParsedIntent(ingredients_include=["soy-based bean protein"])
    normalized = apply_vocab_constraints(intent, vocab)
    assert normalized.ingredients_include == ["Tofu"]
