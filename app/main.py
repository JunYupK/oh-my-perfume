from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.brands import router as brands_router
from app.api.routes.perfumes import router as perfumes_router

app = FastAPI(title="Sillage")

app.include_router(brands_router)
app.include_router(perfumes_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
