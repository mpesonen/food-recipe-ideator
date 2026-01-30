"""Utilities for caching and formatting controlled vocabulary values from Postgres."""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.query_engine.intent_parser import ParsedIntent

VOCAB_PATH = (
    Path(__file__).resolve().parents[2] / "recipes-data" / "controlled_vocab.json"
)

INGREDIENT_KEYWORD_HINTS: dict[str, list[str]] = {
    "soy": ["Tofu", "Tempeh", "Soybeans"],
    "soy-based": ["Tofu", "Tempeh", "Soybeans"],
    "soybean": ["Soybeans"],
    "bean curd": ["Tofu"],
    "garbanzo": ["Chickpeas"],
    "chickpea": ["Chickpeas", "Chana Dal"],
}


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _tokenize(value: str | None) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", (value or "").lower()) if token]


def load_cached_vocab() -> dict[str, list[str]] | None:
    if not VOCAB_PATH.exists():
        return None
    try:
        with VOCAB_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return None

    return {key: list(value) for key, value in data.items() if isinstance(value, list)}


def save_vocab(vocab: dict[str, list[str]]) -> None:
    VOCAB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with VOCAB_PATH.open("w", encoding="utf-8") as f:
        json.dump(vocab, f, indent=2, ensure_ascii=False)


def format_vocab_for_prompt(
    vocab: dict[str, list[str]], ingredient_limit: int = 40
) -> str:
    sections: list[str] = []

    def format_list(name: str, values: list[str], limit: int | None = None) -> None:
        if not values:
            return
        subset = values if limit is None else values[:limit]
        extra = len(values) - len(subset)
        entry = f"- {name}: {', '.join(subset)}"
        if extra > 0:
            entry += f" (+{extra} more)"
        sections.append(entry)

    format_list("Cuisines", vocab.get("cuisines", []), limit=30)
    format_list("Courses", vocab.get("courses", []), limit=20)
    format_list("Diets", vocab.get("diets", []), limit=20)
    format_list("Ingredients", vocab.get("ingredients", []), limit=ingredient_limit)

    if not sections:
        return ""

    header = "Use only the following controlled values when setting structured filters or ingredient names:"
    return "\n".join([header, *sections])


def ensure_vocab(pg_query) -> tuple[dict[str, list[str]], str]:
    vocab = load_cached_vocab()
    if vocab is None or not vocab.get("cuisines"):
        vocab = pg_query.get_controlled_vocab()
        save_vocab(vocab)

    prompt_snippet = format_vocab_for_prompt(vocab)
    return vocab, prompt_snippet


def map_value_to_vocab(
    value: str | None,
    options: list[str],
    *,
    keyword_hints: dict[str, list[str]] | None = None,
    threshold: float = 0.6,
) -> str | None:
    if not value or not options:
        return None

    normalized_value = _normalize_text(value)
    if not normalized_value:
        return None

    normalized_options = {opt: _normalize_text(opt) for opt in options}

    for opt, norm in normalized_options.items():
        if norm == normalized_value:
            return opt

    lower_value = value.lower()
    if keyword_hints:
        for keyword, preferred in keyword_hints.items():
            if keyword in lower_value:
                for target in preferred:
                    match = next(
                        (opt for opt in options if opt.lower() == target.lower()),
                        None,
                    )
                    if match:
                        return match

    best_option = None
    best_score = 0.0
    value_tokens = _tokenize(value)

    for opt, norm_opt in normalized_options.items():
        score = SequenceMatcher(None, normalized_value, norm_opt).ratio()
        if value_tokens:
            opt_tokens = set(_tokenize(opt))
            overlap = len([t for t in value_tokens if t in opt_tokens]) / len(
                value_tokens
            )
            score = max(score, overlap)
            if any(token and token in norm_opt for token in value_tokens):
                score = max(score, 0.72)
        if score > best_score:
            best_score = score
            best_option = opt

    if best_option and best_score >= threshold:
        return best_option
    return None


def apply_vocab_constraints(
    intent: "ParsedIntent", vocab: dict[str, list[str]]
) -> "ParsedIntent":
    def normalize_field(field: str, key: str, threshold: float = 0.65):
        value = getattr(intent, field)
        if not value:
            setattr(intent, field, None)
            return None
        mapped = map_value_to_vocab(value, vocab.get(key, []), threshold=threshold)
        setattr(intent, field, mapped)
        return mapped

    normalize_field("cuisine", "cuisines", threshold=0.7)
    normalize_field("course", "courses", threshold=0.7)
    normalize_field("diet", "diets", threshold=0.7)

    def normalize_ingredient_list(values: list[str] | None) -> list[str] | None:
        if not values:
            return None
        normalized: list[str] = []
        for ingredient in values:
            mapped = map_value_to_vocab(
                ingredient,
                vocab.get("ingredients", []),
                keyword_hints=INGREDIENT_KEYWORD_HINTS,
                threshold=0.5,
            )
            if mapped and mapped not in normalized:
                normalized.append(mapped)
        return normalized or None

    intent.ingredients_include = normalize_ingredient_list(intent.ingredients_include)
    intent.ingredients_exclude = normalize_ingredient_list(intent.ingredients_exclude)

    return intent
