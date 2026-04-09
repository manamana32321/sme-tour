# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**SME Tour** — 시스템경영공학 종합설계 5조의 "사용자의 제약 조건 및 선호도를 고려한 적응형 유럽 여행 경로 다목적 최적화" 프로젝트입니다.

- **팀명**: SME투어
- **팀장**: 조혁진
- **팀원**: 전진석, 유지웅, 박경민, 손장수, 윤강희
- **Notion**: [SME Tour 홈](https://www.notion.so/90ed32f6b7c282e9827401e4c5a88387)
- **Figma**: [SME Tour Web Design](https://www.figma.com/design/m7zUgf7urseUqpik3y1Gem/SME-Tour-Web-Design)

## Project Goal

사용자가 투입 가능한 한정된 자원(시간 및 예산) 내에서 개별 관광지에 대한 선호도를 가장 효율적으로 충족시킬 수 있는 **지능형 유럽 여행 경로 설계 알고리즘**.

- **자원 충분**: 모든 목적지를 효율적으로 방문하는 완주 경로 (TSP)
- **자원 부족**: 전체 만족도를 극대화하는 최적 부분집합 경로 (Orienteering Problem)

## Mathematical Model

### Approach
**Clustered TSP + DFJ Subtour Elimination** (Branch and Cut, lazy constraints)
- 2-stage TSP 대신 Clustered TSP 채택
- MTZ 정적 제거가 아닌 DFJ lazy constraint 방식으로 cut 필요 시에만 추가

### Node Structure (Virtual Graph)
허브 공항은 `Entry` / `Exit` 가상 노드로 분할하고, 내륙 도시는 단일 노드로 둡니다.
- `H`: 허브 공항 노드 집합 (각각 `Entry`, `Exit`)
- `C`: 내륙 도시 노드 집합
- `V = H ∪ C`: 전체 가상 노드 집합

### Edges
- **항공 (국가 간)**: `{hub}_Exit → {hub}_Entry`
- **지상 내륙 이동**: `{hub}_Entry → city`, `city → {hub}_Exit`, `city → city`

### Objective Function
```
min Z = W_cost · (total_cost / Budget) + W_time · (total_time / Deadline)
```
기본 가중치는 `W_cost = W_time = 0.5`.

### Constraints
- 모든 내륙 도시 정확히 1회 방문, 허브 흐름 보존
- `sum(Cost · x) ≤ Budget`
- `sum(Time · x) ≤ Deadline`
- DFJ 부차 순환 제거 (Branch and Cut, lazy)

### Implementation
- **Solver**: Gurobi (Python `gurobipy`)
- **Status**: 프로토타입 코드 존재 (주간 보고서 w6, w7에 첨부) — repo에는 아직 커밋되지 않음 (TODO)
- **License note**: Gurobi는 상용 솔버, 학생 라이센스 필요. Vercel serverless 등에서 실행 불가

## Architecture

```
sme-tour/
├── data/
│   ├── raw/              # API 원본 JSON (gitignored, large)
│   │   └── 2026-06-01/   # 날짜별 폴더, 국가쌍별 .json
│   └── processed/
│       ├── flights_2026-06-01.csv         # 전체 항공편 요약
│       ├── cost_matrix_2026-06-01.csv     # 허브간 최저가 매트릭스
│       └── duration_matrix_2026-06-01.csv # 허브간 최단시간 매트릭스
├── scripts/
│   ├── airports.py           # 15개국 허브 공항 정의
│   └── collect_flights.py    # Sky Scrapper API → raw/processed 수집
├── .env.local                # RAPIDAPI_KEY (gitignored, collect_flights.py가 직접 파싱)
├── .env.local.example        # RapidAPI 템플릿
├── .envrc                    # direnv — .env.local + .envrc.local 로드
├── .envrc.local              # 민감 토큰 (gitignored, Notion 등)
├── .envrc.local.example      # direnv 토큰 템플릿
└── .mcp.json                 # project-level MCP 서버 (notion-sme-tour 격리)
```

### Data Schema (Engine Inputs)

엔진은 다음 두 CSV를 입력으로 받습니다 (현재 repo 파일명과 다르므로 **향후 통합 필요**):

**`Airplane dataset.csv`** — 국가간 항공 이동
- `origin_iata`, `dest_iata`, `carriers`, `price_eur_won`, `duration_minutes`

**`city dataset.csv`** — 내륙 지상 이동
- `origin_node`, `destination_node`, `transport_mode`, `price_won`, `duration_min`

> 현재 repo의 `flights_2026-06-01.csv`는 `price_eur`/`duration_minutes`를 쓰고 있어 엔진 스키마(`price_eur_won`)와 **컬럼명 불일치**. 통합 시 변환 레이어 필요.

## 15개국 허브 공항

`scripts/airports.py` 참조. 2026-03 기준 터키(IST) → 덴마크(CPH)로 교체됨.

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

## Timeline (15주차 계획)

| Week | Milestone | Status |
|---|---|---|
| 2 | 프로젝트 계획서 | ✅ |
| 3 | 주간보고서 (초기) | ✅ |
| 4-5 | 데이터 수집 | ✅ (항공) / ⏳ (도시) |
| 6-7 | 수리 모형 모델링 | ✅ (Clustered TSP + Gurobi 프로토타입) |
| 8 | 중간발표 (문제정의/데이터/모형) | ✅ |
| 9-10 | 확장성 논의 (선호도 가중치, 실시간 휴리스틱) | 진행 중 |
| **11-12** | **웹 개발 (1)(2)** | **← 현재** |
| 13 | 실 사용자 평가검증 (교수님 요구) | 예정 |
| 14 | 최종발표 | 예정 |

## Common Commands

### 데이터 수집

```bash
# 단일 날짜 항공편 수집 (210 국가쌍)
python scripts/collect_flights.py --date 2026-07-01

# 중단된 지점부터 재개
python scripts/collect_flights.py --date 2026-07-01 --resume
```

스크립트는 `.env.local`의 `RAPIDAPI_KEY`를 직접 파싱하므로 **direnv 로드 없이도 작동**합니다. 다만 Notion MCP 등을 쓰려면 `direnv allow` 후 셸이 `.envrc.local`을 로드해야 합니다.

### Notion MCP (종설 워크스페이스 격리)

`.mcp.json`에 `notion-sme-tour` 서버를 프로젝트 레벨로 격리. 토큰은 `.envrc.local`의 `NOTION_SME_TOUR_TOKEN`로 주입됩니다. 홈랩 등 다른 프로젝트의 Notion 커넥터와 **워크스페이스 오염 없음**.

세션 시작 시 Claude Code가 `.mcp.json`을 로드해 `mcp__notion-sme-tour__*` 도구가 활성화됩니다. 도구 활성화 후 필요한 권한을 사용자에게 승인받습니다.

## Conventions

### Language
- 커밋 메시지, PR 제목/본문, 문서: **한국어**
- 코드 식별자: 영어
- 주석: 한국어 허용

### Secrets
- Git 커밋 대상: `.envrc`, `.envrc.local.example`, `.env.local.example`, `.mcp.json`
- Gitignored: `.envrc.local`, `.env.local`, `data/raw/`
- 토큰 노출 시 즉시 Notion/RapidAPI에서 regenerate

### Git Workflow
- main 직접 커밋 금지 — PR 통해서만
- 브랜치 작업은 worktree 사용: `~/sme-tour-worktrees/{브랜치명}/`

## External References

- **Notion 워크스페이스 (종설)**: [홈](https://www.notion.so/90ed32f6b7c282e9827401e4c5a88387) — 주간보고서 DB: `321d32f6-b7c2-80d2-91f7-f7d189d63747`
- **Figma**: [SME Tour Web Design](https://www.figma.com/design/m7zUgf7urseUqpik3y1Gem/SME-Tour-Web-Design)
- **RapidAPI (Sky Scrapper)**: https://rapidapi.com/apiheya/api/sky-scrapper
- **Sky Scrapper 엔드포인트**: `GET /api/v1/flights/searchAirport`, `GET /api/v1/flights/searchFlights`

## Known Issues / TODOs

- [ ] **엔진 코드 repo 통합**: 현재 Gurobi 코드는 Notion 첨부 형태로만 존재 — repo 구조(예: `engine/`) 확정 후 커밋 필요
- [ ] **도시/지상 이동 데이터 수집**: `city dataset.csv` 스키마 정의 및 수집 스크립트 작성
- [ ] **데이터 스키마 통합**: `flights_*.csv`의 컬럼명과 엔진이 기대하는 `Airplane dataset.csv` 스키마 정합성 확보
- [ ] **Gurobi 라이센스**: 학교/학생 라이센스 확보 여부 확인, 배포 환경(Vercel serverless 불가) 결정 필요
- [ ] **웹 인터페이스 설계**: 현재 브레인스토밍 진행 중 — `docs/superpowers/specs/` 참조
