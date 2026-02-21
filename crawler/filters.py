from __future__ import annotations

from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter


def build_filter_chain() -> FilterChain:
    return FilterChain(
        [
            URLPatternFilter(patterns=["*/designers/*", "*/perfume/*"]),
        ]
    )
