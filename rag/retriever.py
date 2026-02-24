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

    # asyncpg는 Python list를 pgvector 타입으로 자동 변환하지 않으므로
    # 벡터를 문자열로 변환하고 SQL에서 명시적으로 CAST하여 처리
    query_vec_str = "[" + ",".join(map(str, query_vec)) + "]"

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
            1 - (e.embedding <=> CAST(:query_vec AS vector)) AS similarity
        FROM perfumes p
        JOIN brands b ON b.id = p.brand_id
        JOIN perfume_embeddings e ON e.perfume_id = p.id
        ORDER BY e.embedding <=> CAST(:query_vec AS vector)
        LIMIT :limit
        """
    )

    rows = (await db.execute(stmt, {"query_vec": query_vec_str, "limit": limit})).mappings().all()

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
