from __future__ import annotations

from sqlalchemy import text

from crawler.embedder import embed_text


async def search_perfumes(query: str, limit: int, db):
    normalized_query = query.strip()
    if not normalized_query:
        return []

    query_vec = await embed_text(normalized_query)
    if limit < 1:
        limit = 10
    if limit > 50:
        limit = 50

    stmt = text(
        """
        SELECT
            p.id AS perfume_id,
            p.name,
            b.name AS brand_name,
            p.fragrantica_url AS url,
            p.year,
            p.concentration,
            p.gender,
            1 - (e.embedding <=> :query_vec) AS similarity
        FROM perfumes p
        JOIN brands b ON b.id = p.brand_id
        JOIN perfume_embeddings e ON e.perfume_id = p.id
        ORDER BY e.embedding <=> :query_vec
        LIMIT :limit
        """
    )

    rows = (await db.execute(stmt, {"query_vec": query_vec, "limit": limit})).mappings().all()

    return [
        {
            "perfume_id": row["perfume_id"],
            "name": row["name"],
            "brand_name": row["brand_name"],
            "url": row["url"],
            "year": row["year"],
            "concentration": row["concentration"],
            "gender": row["gender"],
            "similarity": float(row["similarity"]),
        }
        for row in rows
    ]
