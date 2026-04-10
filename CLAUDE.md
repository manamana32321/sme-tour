# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**SME Tour** — 시스템경영공학 종합설계 5조의 "사용자의 제약 조건 및 선호도를 고려한 적응형 유럽 여행 경로 다목적 최적화" 프로젝트입니다.

- **팀명**: SME투어
- **팀장**: 조혁진
- **팀원**: 전진석, 유지웅, 박경민, 손장수, 윤강희
- **Notion**: [SME Tour 홈](https://www.notion.so/90ed32f6b7c282e9827401e4c5a88387)
- **Figma**: [SME Tour Web Design](https://www.figma.com/design/m7zUgf7urseUqpik3y1Gem/SME-Tour-Web-Design) (현재 비어 있음)

## Project Goal

사용자가 투입 가능한 한정된 자원(시간 및 예산) 내에서 개별 관광지에 대한 선호도를 가장 효율적으로 충족시킬 수 있는 **지능형 유럽 여행 경로 설계 알고리즘** + 웹 인터페이스.

- **MVP A (현재)**: 15개국 허브 + 내륙 도시를 Clustered TSP로 완주하는 경로 탐색
- **Phase 3 (향후)**: 자원 부족 시 만족도 극대화 부분집합 경로 (Orienteering Problem)

## Architecture

단일 git 모노레포. `engine/`(Python FastAPI) + `frontend/`(Next.js) + `k8s/`(배포) 구조.

```
sme-tour/
├── engine/                      # Python 최적화 엔진 (FastAPI)
│   ├── data/
│   │   └── processed/
│   │       ├── Airplane dataset.csv   # 항공편 (25K rows, 엔진 입력)
│   │       └── city dataset.csv       # 내륙 지상 이동 (157 rows, 엔진 입력)
│   ├── collectors/              # 데이터 수집 스크립트 (오프라인 전용)
│   │   ├── airports.py          # 15개국 허브 공항 정의
│   │   └── collect_flights.py   # Sky Scrapper API → raw/processed
│   ├── src/
│   │   ├── main.py              # FastAPI 앱 (POST /optimize 등)
│   │   ├── models.py            # Pydantic: OptimizeRequest/Result
│   │   ├── graph.py             # 솔버 독립 가상 노드 그래프 빌더
│   │   ├── data_loader.py       # CSV → Graph 로드
│   │   ├── solvers/
│   │   │   ├── __init__.py      # get_solver() — Gurobi 우선, OR-Tools fallback
│   │   │   ├── base.py          # BaseSolver ABC
│   │   │   ├── gurobi.py       # GurobiSolver (w7 이식, DFJ lazy callback)
│   │   │   └── ortools.py      # OrToolsSolver (Iterative DFJ, CP-SAT)
│   │   └── __init__.py
│   ├── tests/                   # pytest (71 tests, ~21초)
│   ├── Dockerfile
│   └── pyproject.toml           # Python 3.12+, ortools 기본, gurobipy optional
│
├── frontend/                    # Next.js 16 (TODO: Phase 4에서 생성)
│
├── k8s/                         # K8s 배포 manifests (TODO: Phase 2에서 생성)
│
├── docs/
│   └── superpowers/
│       ├── specs/               # 설계 문서
│       └── plans/               # 구현 계획
│
├── .github/workflows/           # CI/CD (TODO: Phase 3에서 생성)
│
├── CLAUDE.md                    # 이 파일
├── .envrc / .envrc.local        # direnv 환경 (시크릿 격리)
├── .mcp.json                    # Notion MCP 서버 (종설 워크스페이스 격리)
└── .gitignore
```

## Mathematical Model

### Approach
**Clustered TSP + DFJ Subtour Elimination**

### Solver Strategy (전략 패턴)

- **GurobiSolver** (우선): 상용 MIP + Branch and Cut lazy callback. 0.1초 solve.
  WLS Academic License 필요 (`GUROBI_LICENSE_ID`/`WLS_ACCESS_ID`/`WLS_SECRET` 환경변수)
- **OrToolsSolver** (fallback): OR-Tools CP-SAT + **Iterative DFJ** (loop 기반).
  무료 오픈소스. ~5초 solve. Gurobi 미설치 or WLS 인증 실패 시 자동 전환.
- `get_solver()` factory가 Gurobi → OR-Tools 자동 분기.

> **Iterative DFJ**: MTZ(O(n²) 정적 제약)는 60+ node에서 timeout → 대신 relaxed 모델로 먼저 풀고,
> NetworkX SCC로 subtour 탐지 후 DFJ cut 추가 → 재풀기 반복. Gurobi lazy callback과 동일 전략을 loop로 구현.

### Node Structure (Virtual Graph)

- `H`: 허브 공항 노드 (`{IATA}_Entry`, `{IATA}_Exit`)
- `C`: 내륙 도시 노드 (`{CityName}_City`)
- `V = H ∪ C`: 전체 가상 노드 (실데이터: 60 nodes, 5964 edges)

### Objective Function

```text
min Z = W_cost · (Σcost·x / Budget) + W_time · (Σtime·x / Deadline)
```

두 항은 각각 예산/시간 대비 비율로 정규화되어 단위가 통합됨 (다목적 최적화의 가중합 스칼라화).

### Data Schema (Engine Inputs)

엔진은 `engine/data/processed/`의 두 CSV만 읽습니다:

**`Airplane dataset.csv`** (25K rows) — 국가간 항공 이동
- `origin_iata`, `dest_iata`, `carriers`, `price_eur_won`, `duration_minutes`

**`city dataset.csv`** (157 rows) — 내륙 지상 이동
- `origin_node`, `destination_node`, `transport_mode`, `price_won`, `duration_min`

CSV 스키마는 엔진 코드와 정확히 일치 — 변환 레이어 불필요.

## 15개국 허브 공항

`engine/collectors/airports.py` 참조. 2026-03 기준 터키(IST) → 덴마크(CPH)로 교체됨.

| 국가 | 도시 | IATA |
|---|---|---|
| 프랑스 | 파리 | CDG |
| 이탈리아 | 로마 | FCO |
| 스위스 | 취리히 | ZRH |
| 영국 | 런던 | LHR |
| 오스트리아 | 비엔나 | VIE |
| 독일 | 베를린 | BER |
| 네덜란드 | 암스테르담 | AMS |
| 벨기에 | 브뤼셀 | BRU |
| 덴마크 | 코펜하겐 | CPH |
| 폴란드 | 바르샤바 | WAW |
| 스페인 | 바르셀로나 | BCN |
| 포르투갈 | 리스본 | LIS |
| 크로아티아 | 자그레브 | ZAG |
| 헝가리 | 부다페스트 | BUD |
| 체코 | 프라하 | PRG |

## Common Commands

### 엔진 로컬 개발

```bash
cd engine

# venv (uv 사용)
uv venv --python 3.12
uv pip install -e '.[dev]'

# Gurobi 선택 설치 (WLS credentials 필요)
uv pip install -e '.[gurobi]'
export GUROBI_LICENSE_ID="..."
export GUROBI_WLS_ACCESS_ID="..."
export GUROBI_WLS_SECRET="..."

# 테스트
uv run pytest -v

# FastAPI 실행 (OR-Tools fallback 자동)
uv run uvicorn src.main:app --reload --port 8000

# 최적 경로 호출
curl -s -X POST http://localhost:8000/optimize \
  -H 'Content-Type: application/json' \
  -d '{"budget_won":10000000,"deadline_days":14,"start_hub":"CDG","w_cost":0.5}'
```

### 데이터 수집 (오프라인)

```bash
# repo root의 .env.local에 RAPIDAPI_KEY 설정 필요
cd engine
python collectors/collect_flights.py --date 2026-07-01
python collectors/collect_flights.py --date 2026-07-01 --resume  # 중단 재개
```

### Notion MCP (종설 워크스페이스 격리)

`.mcp.json`에 `notion-sme-tour` 서버를 프로젝트 레벨로 격리. 토큰은 `.envrc.local`의 `NOTION_SME_TOUR_TOKEN`으로 주입. 세션 시작 시 Claude Code가 자동 로드.

## Conventions

### Language
- 커밋 메시지, PR 제목/본문, 문서: **한국어**
- 코드 식별자: 영어
- 주석: 한국어 허용

### Secrets
- Git 커밋 대상: `.envrc`, `.envrc.local.example`, `.env.local.example`, `.mcp.json`
- Gitignored: `.envrc.local`, `.env.local`, `engine/data/raw/`, `engine/.venv/`
- 토큰 노출 시 즉시 regenerate

### Git Workflow
- main 직접 커밋 금지 — PR 통해서만
- 브랜치 작업은 worktree 사용: `~/sme-tour-worktrees/{브랜치명}/`

## External References

- **Notion (종설)**: [홈](https://www.notion.so/90ed32f6b7c282e9827401e4c5a88387) — 주간보고서 DB: `321d32f6-b7c2-80d2-91f7-f7d189d63747`
- **Figma**: [SME Tour Web Design](https://www.figma.com/design/m7zUgf7urseUqpik3y1Gem/SME-Tour-Web-Design) (비어 있음)
- **설계 문서**: [docs/superpowers/specs/2026-04-09-sme-tour-web-mvp-a-design.md](docs/superpowers/specs/2026-04-09-sme-tour-web-mvp-a-design.md)
- **구현 계획**: [docs/superpowers/plans/2026-04-09-sme-tour-web-mvp-a.md](docs/superpowers/plans/2026-04-09-sme-tour-web-mvp-a.md)
- **Gurobi WLS**: https://www.gurobi.com/academia/ (Academic Free Tier 확인됨)
- **RapidAPI (Sky Scrapper)**: [Sky Scrapper API](https://rapidapi.com/apiheya/api/sky-scrapper)

## Known Issues / TODOs

- [ ] **Gurobi WLS 라이센스 발급**: 팀원 중 학생 계정으로 WLS 신청 필요. 발급 전까지 OR-Tools fallback으로 동작.
- [ ] **OR-Tools Iterative DFJ 성능**: 실데이터에서 ~5초. Gurobi(0.1초) 대비 느리지만 허용 범위. 최적화 여지 있음 (solver.parameters 튜닝, 초기해 전략).
- [ ] **Frontend scaffold**: Next.js 16 + Tailwind + shadcn/ui. Phase 4에서 `frontend/` 생성 예정.
- [ ] **K8s 배포 매니페스트**: Phase 2에서 `k8s/` 생성 (Deployment, Ingress, SealedSecret, ArgoCD App).
- [ ] **CI/CD**: Phase 3에서 `.github/workflows/` 생성 (engine-build, frontend-ci).
- [ ] **Cloudflare DNS**: `api.sme-tour.json-server.win` A 레코드 + `sme-tour.json-server.win` CNAME.
- [ ] **Prometheus metrics**: `/metrics` 엔드포인트 + ServiceMonitor. Phase 2에서 추가.
- [ ] **collect_flights.py 산출물 정리**: `flights_*.csv`, `cost_matrix_*.csv`, `duration_matrix_*.csv`는 수집 스크립트의 분석 결과물이며 엔진 미사용. git에서 삭제 완료.
