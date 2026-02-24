from __future__ import annotations

from crawl4ai import LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

from app.core.config import settings
from app.schemas.crawler import PerfumeExtractSchema


def build_extraction_strategy() -> LLMExtractionStrategy:
    return LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="anthropic/claude-sonnet-4-6",
            api_token=settings.anthropic_api_key,
        ),
        schema=PerfumeExtractSchema,
        instruction=(
            """
            이 향수 상세 페이지에서 다음 정보를 추출하세요.
            - name: 향수명 (영문)
            - brand: 브랜드명 (영문)
            - year: 출시 연도 (없으면 null)
            - concentration: EDP/EDT/Parfum/EDC/EDP Intense 중 하나
            - gender: Men/Women/Unisex 중 하나
            - accords: 향 계열 목록. 각 항목은 {"name": "Floral", "strength": 0.8} 형태로,
              strength는 페이지의 시각적 바 너비를 0.0~1.0으로 추정한 값
            - top_notes / middle_notes / base_notes: 노트 목록
            """
        ),
        input_format="html",
    )
