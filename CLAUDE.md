# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**SME Tour** — 시스템경영공학 종합설계 5조의 "사용자의 제약 조건 및 선호도를 고려한 적응형 유럽 여행 경로 다목적 최적화" 프로젝트입니다.

- **팀명**: SME투어
- **팀장**: 조혁진
- **팀원**: 전진석, 유지웅, 박경민, 손장수, 윤강희
- **Notion**: [SME Tour 홈](https://www.notion.so/90ed32f6b7c282e9827401e4c5a88387)

## Project Goal

사용자가 투입 가능한 한정된 자원(시간 및 예산) 내에서 개별 관광지에 대한 선호도를 가장 효율적으로 충족시킬 수 있는 **지능형 유럽 여행 경로 설계 알고리즘** + 웹 인터페이스.

- **MVP A (현재)**: 15개국 허브 + 내륙 도시를 Clustered TSP로 완주하는 경로 탐색
- **Phase 3 (향후)**: 자원 부족 시 만족도 극대화 부분집합 경로 (Orienteering Problem)

## Architecture

단일 git 모노레포: `engine/`(Python FastAPI) + `frontend/`(Next.js 16) + `k8s/`(배포 manifests).

### Solver Strategy

- **GurobiSolver** (우선): 상용 MIP + DFJ lazy callback. 0.1초. WLS Academic License 환경변수 3개 필요.
- **OrToolsSolver** (fallback): OR-Tools CP-SAT + Iterative DFJ. ~5초. Gurobi 미설치 시 자동 전환.
- `get_solver()` factory가 Gurobi → OR-Tools 자동 분기.

### Objective Function

```text
min Z = W_cost · (Σcost·x / Budget) + W_time · (Σtime·x / Deadline)
```

두 항은 예산/시간 대비 비율로 정규화 (다목적 최적화의 가중합 스칼라화).

### Data Schema

엔진은 `engine/data/processed/`의 두 CSV만 읽음:

- **`Airplane dataset.csv`** (25K rows): `origin_iata`, `dest_iata`, `carriers`, `price_eur_won`, `duration_minutes`
- **`city dataset.csv`** (157 rows): `origin_node`, `destination_node`, `transport_mode`, `price_won`, `duration_min`

## Deployment

| 서비스 | URL | 호스팅 |
|---|---|---|
| 프론트엔드 | <https://sme-tour.json-server.win> | Vercel |
| 엔진 API | <https://api.sme-tour.json-server.win> | 홈랩 K3s |

- **엔진**: `engine/` 변경 → GHA → GHCR push → ArgoCD Image Updater → K3s 자동 롤아웃
- **프론트**: `frontend/` 변경 → Vercel 자동 배포 (rootDirectory=`frontend`)
- **K8s**: `k8s/` 변경 → ArgoCD 자동 sync (ns: `sme-tour`)
- **DNS**: 홈랩 repo `cloudflare/dns.tf` → terraform apply

### 인프라 참고

- IngressClass: **traefik** (nginx 아님)
- TLS: cert-manager `letsencrypt-dns01` ClusterIssuer
- Vercel CNAME: `proxied=false` 필수 (Vercel SSL 발급 위해)

## Common Commands

```bash
# 엔진 로컬 개발
cd engine && uv venv --python 3.12 && uv pip install -e '.[dev]'
uv run pytest -v
uv run uvicorn src.main:app --reload --port 8000

# 최적 경로 호출
curl -s -X POST http://localhost:8000/optimize \
  -H 'Content-Type: application/json' \
  -d '{"budget_won":10000000,"deadline_days":14,"start_hub":"CDG","w_cost":0.5}'

# 데이터 수집 (오프라인, repo root .env.local에 RAPIDAPI_KEY 필요)
cd engine && python collectors/collect_flights.py --date 2026-07-01
```

## Conventions

### Language

- 커밋 메시지, PR 제목/본문, 문서: **한국어**
- 코드 식별자: 영어
- 주석: 한국어 허용

### Secrets

- Git 커밋 대상: `.envrc`, `.envrc.local.example`, `.env.local.example`, `.mcp.json`
- Gitignored: `.envrc.local`, `.env.local`, `engine/data/raw/`, `engine/.venv/`

### Git Workflow

- main 직접 커밋 금지 — PR 통해서만
- 브랜치 작업은 worktree 사용: `~/sme-tour-worktrees/{브랜치명}/`

### Notion MCP

`.mcp.json`에 `notion-sme-tour` 서버를 프로젝트 레벨로 격리. 토큰은 `.envrc.local`의 `NOTION_SME_TOUR_TOKEN`으로 주입.

## External References

- **Notion (종설)**: [홈](https://www.notion.so/90ed32f6b7c282e9827401e4c5a88387) — 주간보고서 DB: `321d32f6-b7c2-80d2-91f7-f7d189d63747`
- **설계 문서**: [docs/superpowers/specs/2026-04-09-sme-tour-web-mvp-a-design.md](docs/superpowers/specs/2026-04-09-sme-tour-web-mvp-a-design.md)
- **구현 계획**: [docs/superpowers/plans/2026-04-09-sme-tour-web-mvp-a.md](docs/superpowers/plans/2026-04-09-sme-tour-web-mvp-a.md)
- **Gurobi WLS**: [Academic Free Tier](https://www.gurobi.com/academia/)

## Known Issues / TODOs

- [ ] **Gurobi WLS 라이센스 발급**: OR-Tools fallback으로 동작 중 (~5초). WLS 발급 시 0.1초로 개선.
- [ ] **OR-Tools 성능 튜닝**: solver.parameters, 초기해 전략 개선 여지.
