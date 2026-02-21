# Sillage

Fragrantica 기반 향수 수집 + PostgreSQL/pgvector RAG API.

## 필수 조건
- Docker / Docker Compose
- Python 3.11+
- PostgreSQL (docker-compose의 `pgvector/pgvector:pg16` 사용 권장)
- Redis

## 실행 (로컬)

1. 환경 변수 준비
```bash
cp .env.example .env
```
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `POSTGRES_PASSWORD`는 필수

2. 서비스 시작
```bash
docker compose up -d --build
```

3. 헬스체크
```bash
curl http://localhost:8000/health
```

## API
- `GET /api/brands`
- `GET /api/brands/{slug}/perfumes`
- `GET /api/perfumes/{slug}`
- `POST /api/perfumes/search`
  - body: `{ "query": "string", "limit": 10 }`
- `GET /api/perfumes/trending`
- `GET /health`

## 크롤러 실행

기본적으로 크롤러는 무한 순환입니다.
- 전체 순환: `python -m crawler.worker`
- 1회 실행 테스트(브랜드 1개, `max_pages=10`):
```bash
python -m crawler.worker --once --brand Dior --max-pages 10
```
- 다중 브랜드 1회 테스트:
```bash
python -m crawler.worker --once --brand Dior --brand Chanel --max-pages 10
```

## 배포(이미지 빌드 + 배포)
GitHub Actions는 `main` 브랜치 push 기준으로 동작하며 다음 단계를 수행합니다.
- test
- build(`Dockerfile`, `Dockerfile.crawler` 이미지 빌드/푸시)
- deploy(SSH로 서버 배포, `api`/`crawler` 롤링 업)

필요 Secrets:
- `ANTHROPIC_API_KEY`
- `POSTGRES_PASSWORD`
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`

## 마이그레이션
```bash
alembic upgrade head
```
