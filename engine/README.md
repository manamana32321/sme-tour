# SME Tour Engine

FastAPI + Gurobi 기반 유럽 여행 경로 최적화 엔진. Clustered TSP + DFJ Subtour Elimination (Branch and Cut with lazy constraints)으로 15개국 허브 + 내륙 도시를 탐색합니다.

## 요구사항

- Python 3.12+
- Gurobi WLS Academic License ([발급](https://www.gurobi.com/academia/))
- Docker (배포용)

## 로컬 개발

```bash
# 의존성 설치 (dev deps 포함)
pip install -e '.[dev]'

# Gurobi WLS credentials 환경변수 설정
export GUROBI_LICENSE_ID="..."
export GUROBI_WLS_ACCESS_ID="..."
export GUROBI_WLS_SECRET="..."

# FastAPI 실행
uvicorn src.main:app --reload

# 테스트
pytest
```

## 엔드포인트

| Method | Path | Description |
|---|---|---|
| `POST` | `/optimize` | 최적 경로 계산 |
| `GET` | `/healthz` | Liveness probe |
| `GET` | `/readyz` | Readiness probe (그래프 + 솔버 초기화) |
| `GET` | `/metrics` | Prometheus scrape |

## 데이터 수집

`collectors/`의 Python 스크립트는 Sky Scrapper API로 항공편 데이터를 수집합니다. 엔진 런타임엔 필요 없고 오프라인으로만 실행:

```bash
# repo root의 .env.local에 RAPIDAPI_KEY 설정
cd engine
python collectors/collect_flights.py --date 2026-07-01
```

## 참조

- [설계 문서](../docs/superpowers/specs/2026-04-09-sme-tour-web-mvp-a-design.md)
- [구현 계획](../docs/superpowers/plans/2026-04-09-sme-tour-web-mvp-a.md)
