from __future__ import annotations

import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sillage"
    environment: str = "local"
    database_url: str = "postgresql+asyncpg://sillage:password@postgres:5432/sillage"
    redis_url: str = "redis://redis:6379"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    crawler_target_brands: str = (
        "Dior,Chanel,Tom-Ford,Creed,Jo-Malone-London,Diptyque,Le-Labo,Maison-Margiela,"
        "Byredo,Acqua-di-Parma,Guerlain,Hermes,Yves-Saint-Laurent,Giorgio-Armani,Versace"
    )
    crawler_max_pages_per_brand: int = 200

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @staticmethod
    def _parse_brands(raw: str) -> list[str]:
        if not raw:
            return []

        stripped = raw.strip()
        if not stripped:
            return []

        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]

        return [item.strip() for item in stripped.split(",") if item.strip()]

    @property
    def crawler_target_brands_list(self) -> list[str]:
        return self._parse_brands(self.crawler_target_brands)


settings = Settings()
