from __future__ import annotations

from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

from crawler.filters import build_filter_chain


def build_brand_strategy(on_state_change, resume_state=None, max_pages: int = 200) -> BFSDeepCrawlStrategy:
    filter_chain = build_filter_chain()

    return BFSDeepCrawlStrategy(
        max_depth=2,
        include_external=False,
        max_pages=max_pages,
        filter_chain=filter_chain,
        on_state_change=on_state_change,
        resume_state=resume_state,
    )
