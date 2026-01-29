"""Utilities for fetching and caching preview images for recipe URLs."""

from __future__ import annotations

import time
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx

CACHE_TTL_SECONDS = 60 * 60 * 6  # 6 hours
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36"
)

_cache: dict[str, tuple[Optional[str], float]] = {}


class _PreviewHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta_tags: list[dict[str, str]] = []
        self.img_tags: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attr_dict = {name.lower(): value for name, value in attrs if name and value}
        lower_tag = tag.lower()
        if lower_tag == "meta":
            self.meta_tags.append(attr_dict)
        elif lower_tag == "img":
            self.img_tags.append(attr_dict)


def _normalize_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    return url


def _absolutize(candidate: str, base_url: httpx.URL) -> Optional[str]:
    if not candidate:
        return None
    if candidate.startswith("//"):
        return f"{base_url.scheme}:{candidate}"
    if candidate.startswith("http://") or candidate.startswith("https://"):
        return candidate
    try:
        return urljoin(str(base_url), candidate)
    except Exception:
        return None


def _cache_get(url: str) -> Optional[str]:
    cached = _cache.get(url)
    if not cached:
        return None
    value, expires = cached
    if expires < time.time():
        _cache.pop(url, None)
        return None
    return value


def _cache_set(url: str, value: Optional[str]) -> None:
    _cache[url] = (value, time.time() + CACHE_TTL_SECONDS)


async def get_recipe_preview_image(url: str) -> Optional[str]:
    normalized = _normalize_url(url)
    if not normalized:
        return None

    cached = _cache_get(normalized)
    if cached is not None:
        return cached

    image_url = await _fetch_preview_image(normalized)
    _cache_set(normalized, image_url)
    return image_url


async def _fetch_preview_image(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(
            timeout=10,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError:
        return None

    parser = _PreviewHTMLParser()
    parser.feed(response.text)
    parser.close()

    preferred_meta = {
        "og:image",
        "og:image:secure_url",
        "twitter:image",
        "twitter:image:src",
    }

    for meta in parser.meta_tags:
        meta_name = (meta.get("property") or meta.get("name") or "").lower()
        if meta_name in preferred_meta:
            candidate = meta.get("content")
            image = _absolutize(candidate or "", response.url)
            if image:
                return image

    for attrs in parser.img_tags:
        candidate = (
            attrs.get("data-src") or attrs.get("data-original") or attrs.get("src")
        )
        if not candidate and attrs.get("srcset"):
            candidate = attrs["srcset"].split(",")[0].strip().split(" ")[0]
        image = _absolutize(candidate or "", response.url)
        if image:
            return image

    return None
