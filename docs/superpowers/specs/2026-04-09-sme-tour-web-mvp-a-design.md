# SME Tour 웹 인터페이스 — MVP A 설계 문서

| 항목 | 내용 |
|---|---|
| **작성일** | 2026-04-09 (KST) |
| **작성자** | JSON (웹개발 담당) + Claude |
| **상태** | Draft — 사용자 리뷰 대기 |
| **대상 스코프** | MVP A (Thin Playground) |
| **예상 데드라인** | 2026-05-31 (종설 5월 말 + 13주차 실사용자 평가 전) |

## 1. Overview

### 1.1 프로젝트 정체

**SME투어**는 시스템경영공학 종합설계 5조의 "사용자의 제약 조건(예산, 기간) 및 선호도를 고려한 적응형 유럽 여행 경로 다목적 최적화" 프로젝트입니다. 팀원은 조혁진(팀장), 전진석, 유지웅, 박경민, 손장수, 윤강희이며, 수학적 모형(Clustered TSP + DFJ Subtour Elimination)과 데이터 수집은 이미 완료되어 있고, 이번 문서는 **12주차 "시뮬레이션 인터페이스" 개발**을 구체화합니다.

### 1.2 MVP A의 목적

1. **1차 목적**: 비개발자 팀원들에게 **"웹에서 엔진이 실제로 동작하는 모습"** 을 감 잡게 하기
2. **2차 목적**: 13주차 **실사용자 평가검증**에 사용할 수 있는 최소 동작 가능 서비스

이 두 목적을 **하나의 앱**으로 충족합니다. 별도 데모판/평가판 이원화는 하지 않습니다.

> **용어 주의**: "15개국 완주"라는 표현은 **15개 허브 공항 + 각 국가의 내륙 도시(Brno, NCE 등)** 까지 모두 방문하는 Clustered TSP를 의미합니다. MVP A에서 이 제약은 완화하지 않으며(OP 모드는 Phase 3), 경로 해는 허브 수십 개 + 내륙 도시 수십 개 = 전체 약 60+ 노드를 지나는 순환 경로입니다.

### 1.3 핵심 설계 원칙

- **URL = 입력값의 Single Source of Truth** — 결과 저장 없이 공유 가능
- **엔진은 블랙박스** — 웹은 `POST /optimize`만 알면 됨
- **팀 인프라 재활용** — Vercel(프론트) + 홈랩 K3s(백엔드). 추가 유료 서비스 0
- **YAGNI** — Phase 2/3 기능은 이 문서에 목록만 유지, 구현 금지

## 2. Goals / Non-Goals

### 2.1 Goals (MVP A)

- ✅ 사용자가 예산/기간/출발공항/가중치를 입력하면 경로를 보여준다
- ✅ 결과는 지도 + 에지 리스트 + 요약 카드로 시각화
- ✅ URL 공유로 타인이 같은 결과를 볼 수 있다 (입력 재계산 방식)
- ✅ 엔진의 실제 Gurobi solver 결과를 사용 (목업/더미 금지)
- ✅ 적절한 에러/로딩/infeasible 상태 UX 제공
- ✅ 홈랩 K3s에 배포, Vercel에 프론트 배포, CI/CD 자동화
- ✅ 한국어 전용 UI

### 2.2 Non-Goals (MVP A 범위 밖)

- ❌ 사용자 계정 / 인증
- ❌ 결과 저장 / 히스토리 / 즐겨찾기
- ❌ 경로 비교 기능
- ❌ 내륙 도시 선호도 입력 (고급 UX)
- ❌ 슬라이더 실시간 재계산 (debounce 재fetch)
- ❌ 다국어 지원 (영어/기타)
- ❌ WCAG 접근성 컴플라이언스 (shadcn 기본 수준 유지, 그 이상 작업 없음)
- ❌ OR-Tools/SCIP 등 대체 솔버 (Gurobi only)
- ❌ Orienteering Problem 모드 (부분집합 경로). MVP는 모든 노드 완주(TSP)만
- ❌ Cloudflare Proxy / WAF / Total TLS (현 단계는 proxied=false)

## 3. Constraints & Assumptions

### 3.1 기술적 가정

| # | 가정 | 근거 | 깨지면 |
|---|---|---|---|
| A1 | **Gurobi WLS Free Academic License**를 발급받을 수 있다 | 2026-04-09 gurobi.com/academia/ 공식 확인 — Academic Named-User / **WLS** / Site License 3종 무료. WLS는 "cloud-based platforms" 명시 지원. 컨테이너 동작은 명시 없지만 WLS 본성상 정상 동작 예상 | Fallback: 사용자 랩탑에서 로컬 실행 + tailscale/ngrok으로 K3s Ingress 대체 |
| A2 | 엔진이 **단일 요청당 30초 이내** 에 해를 찾는다 | w7 실행 로그: 93×5964 모델, 0.1초 solve | Infeasible/Timeout 상태로 처리, 사용자에게 "조건 완화" CTA |
| A3 | `Airplane dataset.csv` + `city dataset.csv` 스키마가 엔진 코드와 정확히 일치 (또는 간단한 변환만 필요) | 실제 다운로드해서 확인 완료, 아래 3.2 참조 | 엔진 측 `data_loader.py`에 변환 레이어 추가 |
| A4 | 홈랩 K3s에 Gurobi 런타임을 포함한 Docker 이미지 배포 가능 | 기존 SealedSecret + ArgoCD Image Updater 인프라 활용 가능 | — |
| A5 | 실사용자 평가는 팀 + 주변인 수준의 소규모 (동시 접속 ≤ 10) | 종설 프로젝트 규모 | replicas 증설 또는 요청 큐잉 |

### 3.2 CSV 스키마 실제 검증 결과

Notion "데이터 통합" 페이지에서 다운로드한 CSV 파일 확인:

**`Airplane dataset.csv`** (3,551 KB, 25,053 rows)
```
origin_country, origin_iata, dest_country, dest_iata, departure, arrival,
duration_minutes, stop_count, carriers, price_eur_won, price_eur,
segment_count, itinerary_id
```
엔진 코드(w7)가 읽는 컬럼: `origin_iata`, `dest_iata`, `carriers`, `price_eur_won`, `duration_minutes`
**→ 정확히 일치, 변환 불필요.** 엔진이 사용하지 않는 추가 컬럼(`price_eur`, `segment_count`, `itinerary_id` 등)은 무시됨.

**`city dataset.csv`** (7.9 KB, 157 rows)
```
country, origin_node, destination_node, option_id, transport_mode,
price_won, duration_hours, duration_min
```
엔진 코드가 읽는 컬럼: `origin_node`, `destination_node`, `transport_mode`, `price_won`, `duration_min`
**→ 정확히 일치, 변환 불필요.** 추가 컬럼(`country`, `option_id`, `duration_hours`)은 무시됨.

리스크 **M1 (CSV 스키마 드리프트)** 은 이 검증으로 **해소**.

### 3.3 제약

- **팀 내 웹 개발자 1명**: 사용자만 웹 기술 스택 경험 보유
- **엔진 코드 소유**: 팀 공동 저작, 저작권/라이센스 제약 없음 (사용자 확인)
- **배포 비용**: 추가 월정액 0원 (Vercel Hobby + 기존 홈랩)
- **도메인**: `json-server.win` 사용자 개인 소유, 무료 사용 가능

## 4. Architecture

### 4.1 상위 컴포넌트 다이어그램

```
┌────────────────────────────────────────────────────────────┐
│  User Browser                                              │
│  (Vercel Edge Cache + React 19 client)                     │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTPS, static assets + SSR
                       ▼
┌────────────────────────────────────────────────────────────┐
│  Next.js 16 on Vercel                                      │
│  ├ App Router / React Server Components                    │
│  ├ /            Landing + Input Form (nuqs in URL)         │
│  ├ /result      Map + Route List + Summary                 │
│  └ fetch() → https://api.sme-tour.json-server.win/optimize │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTPS, CORS, JSON POST
                       ▼
┌────────────────────────────────────────────────────────────┐
│  Cloudflare DNS (json-server.win zone)                     │
│  └ api.sme-tour → 홈랩 Ingress (TLS via cert-manager DNS01)│
│     (proxied=false, 3-level subdomain)                     │
└──────────────────────┬─────────────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────────────┐
│  Homelab K3s (json-server-1)                               │
│  ├ Ingress (ingress-nginx) api.sme-tour.json-server.win    │
│  ├ Service: sme-tour-engine (ClusterIP:80)                 │
│  └ Deployment: sme-tour-engine (FastAPI, 1 replica)        │
│      ├ Init: load CSVs → Graph (once at startup)           │
│      ├ Init: Gurobi env (WLS AccessID/Secret)              │
│      ├ POST /optimize   solver.solve(graph, req) → JSON    │
│      ├ GET  /healthz    (liveness)                         │
│      └ GET  /readyz     (solver initialized + WLS valid)   │
└────────────────────────────────────────────────────────────┘
```

### 4.2 저장소 구조

단일 git 저장소(sme-tour) 내 모노레포 구조:

```
sme-tour/
├── engine/
│   ├── data/
│   │   ├── raw/                   # gitignored (API 원본)
│   │   └── processed/
│   │       ├── Airplane dataset.csv
│   │       └── city dataset.csv
│   ├── collectors/                # 기존 scripts/ 이름 개선
│   │   ├── airports.py
│   │   └── collect_flights.py
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app
│   │   ├── graph.py               # 솔버 독립 그래프 빌더
│   │   ├── models.py              # Pydantic models (Request/Result)
│   │   ├── solvers/
│   │   │   ├── __init__.py        # get_solver() factory
│   │   │   ├── base.py            # BaseSolver ABC
│   │   │   └── gurobi.py          # GurobiSolver (w7 기반)
│   │   ├── data_loader.py         # CSV loading + 정규화
│   │   └── metrics.py             # Prometheus counters/histograms
│   ├── tests/
│   │   ├── test_graph.py
│   │   ├── test_solver.py
│   │   └── fixtures/
│   │       └── mini.csv           # 작은 테스트 그래프
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── README.md
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   ├── providers.tsx          # NuqsAdapter + ThemeProvider
│   │   ├── page.tsx               # / Landing + Form
│   │   ├── result/
│   │   │   ├── page.tsx           # /result (RSC, searchParams 기반)
│   │   │   ├── loading.tsx
│   │   │   └── error.tsx
│   │   └── not-found.tsx
│   ├── components/
│   │   ├── form/
│   │   │   ├── optimize-form.tsx
│   │   │   ├── hub-select.tsx
│   │   │   ├── budget-slider.tsx
│   │   │   ├── deadline-slider.tsx
│   │   │   └── weight-slider.tsx
│   │   ├── result/
│   │   │   ├── result-view.tsx
│   │   │   ├── top-bar.tsx
│   │   │   ├── summary-cards.tsx
│   │   │   ├── route-map.tsx      # Leaflet, dynamic import
│   │   │   ├── route-list.tsx     # virtualized
│   │   │   └── route-edge-card.tsx
│   │   ├── shared/
│   │   │   ├── infeasible-banner.tsx
│   │   │   ├── error-state.tsx
│   │   │   └── copy-url-button.tsx
│   │   └── ui/                    # shadcn/ui generated
│   ├── lib/
│   │   ├── api.ts                 # fetch wrapper, Zod validation
│   │   ├── schemas.ts             # Zod mirrors
│   │   ├── nuqs-parsers.ts
│   │   ├── hubs.ts                # 15 hubs constant + coordinates
│   │   ├── format.ts              # KRW, duration, etc.
│   │   └── icons.ts               # category → emoji mapping
│   ├── hooks/
│   │   └── use-optimize.ts        # (optional) client-side refetch
│   ├── public/
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── README.md
│
├── k8s/                           # 백엔드 배포 manifests
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── servicemonitor.yaml
│   ├── sealed-secret-gurobi.yaml  # WLS credentials
│   ├── kustomization.yaml
│   └── argocd-app.yaml
│
├── .github/
│   └── workflows/
│       ├── engine-build.yml       # Docker → GHCR
│       └── frontend-ci.yml        # (Vercel이 자동 배포하지만 type-check/lint용)
│
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-09-sme-tour-web-mvp-a-design.md  # this file
│
├── CLAUDE.md
├── README.md
├── .envrc
├── .envrc.local                   # gitignored — NOTION_SME_TOUR_TOKEN
├── .envrc.local.example
├── .env.local                     # gitignored — RAPIDAPI_KEY (기존)
├── .env.local.example
├── .gitignore
└── .mcp.json                      # notion-sme-tour server
```

### 4.3 핵심 결정 근거

1. **백엔드는 홈랩 K3s 단일 replica로 충분** — 엔진 solve가 0.1~3초 + 소규모 평가 트래픽. Pod 리소스: `requests: 500m/512Mi`, `limits: 2000m/2Gi`. 그래프(수 MB)는 앱 시작 시 1회 로드 후 모든 요청에서 공유 (stateless).
2. **헬스체크 분리**: `/healthz`는 FastAPI liveness만. `/readyz`는 Graph 빌드 완료 + Gurobi WLS env 초기화 성공까지 검증.
3. **TLS는 cert-manager DNS01 (Cloudflare)** — `api.sme-tour.json-server.win`은 멀티레벨 서브도메인, `proxied=false` + `letsencrypt-dns` ClusterIssuer.
4. **CORS 정책** — `https://sme-tour.json-server.win`, `https://*.vercel.app`, `http://localhost:3000`(로컬 개발) 허용. 메서드: GET/POST/OPTIONS. 자격증명 불요.
5. **Gurobi 라이센스는 SealedSecret**으로 K8s에 주입 — WLS credentials(`LicenseID`, `WLSAccessID`, `WLSSecret`) 3개 환경변수.
6. **데이터 CSV는 이미지 내부에 COPY** — 데이터가 작고(3.5MB + 7.9KB), 코드와 버전이 묶여야 재현 가능.

## 5. Engine API Contract

### 5.1 Pydantic 모델

```python
# engine/src/models.py
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field, computed_field

class Status(str, Enum):
    OPTIMAL    = "optimal"       # 최적해 발견
    FEASIBLE   = "feasible"      # 실행 가능한 해 (타임아웃 내 최적 미확인)
    INFEASIBLE = "infeasible"    # 제약 만족 불가
    TIMEOUT    = "timeout"       # 솔버 시간 초과

class OptimizeRequest(BaseModel):
    budget_won:    int   = Field(..., ge=1_000_000, le=30_000_000, description="총 예산 (KRW)")
    deadline_days: int   = Field(..., ge=3,        le=30,          description="여행 기간 (일)")
    start_hub:     str   = Field(..., min_length=3, max_length=3,  description="출발 공항 IATA")
    w_cost:        float = Field(0.5, ge=0.0,     le=1.0,          description="비용 가중치 (0=시간우선, 1=비용우선)")

    @computed_field
    @property
    def w_time(self) -> float:
        return 1.0 - self.w_cost

    @computed_field
    @property
    def deadline_minutes(self) -> int:
        return self.deadline_days * 24 * 60

class RouteEdge(BaseModel):
    from_node:    str
    to_node:      str
    mode:         str                                   # "Air_RyanAir" 등
    category:     Literal["air", "ground", "hub_stay"]  # UI 아이콘 사전 계산
    cost_won:     int
    time_minutes: int

class OptimizeResult(BaseModel):
    status:              Status
    route:               list[RouteEdge]
    total_cost_won:      int
    total_time_minutes:  int
    objective_value:     float
    solve_time_ms:       int
    solver:              Literal["gurobi"]
    visited_iata:        list[str]
    visited_cities:      list[str]
    engine_version:      str  # "sme-tour-engine 0.1.0 (abc1234)"
```

### 5.2 엔드포인트

| Method | Path | Description |
|---|---|---|
| `POST` | `/optimize` | 최적 경로 계산 (핵심) |
| `GET` | `/meta/version` | 엔진 버전, 데이터 버전 |
| `GET` | `/healthz` | K8s liveness |
| `GET` | `/readyz` | 그래프 로드 + WLS 초기화 완료 여부 |
| `GET` | `/metrics` | Prometheus scrape |

### 5.3 예시 요청/응답

**요청**
```http
POST /optimize HTTP/1.1
Host: api.sme-tour.json-server.win
Content-Type: application/json

{
  "budget_won":    10000000,
  "deadline_days": 14,
  "start_hub":     "CDG",
  "w_cost":        0.5
}
```

**응답 (성공)**
```json
{
  "status": "optimal",
  "route": [
    { "from_node": "CDG_Entry", "to_node": "NCE_City", "mode": "Ground_Train",
      "category": "ground", "cost_won": 50000, "time_minutes": 402 },
    { "from_node": "NCE_City",  "to_node": "LYS_City", "mode": "Ground_Train",
      "category": "ground", "cost_won": 33000, "time_minutes": 330 }
  ],
  "total_cost_won":     4187641,
  "total_time_minutes": 11340,
  "objective_value":    0.4897180323794,
  "solve_time_ms":      103,
  "solver":             "gurobi",
  "visited_iata":       ["CDG","PRG","CPH","WAW","AMS","ZAG","VIE","FCO","BUD","BER","ZRH","LIS","BCN","BRU","LHR"],
  "visited_cities":     ["NCE_City","LYS_City","Brno_City","Cesky Krumlov_City"],
  "engine_version":     "sme-tour-engine 0.1.0 (abc1234)"
}
```

### 5.4 상태 코드 매핑

| HTTP | Body `status` | 의미 | 프론트 동작 |
|---|---|---|---|
| `200` | `optimal` / `feasible` | 정상 해 | 결과 화면 렌더 |
| `200` | `infeasible` | 제약 만족 불가 | "조건이 너무 빡빡합니다" 안내 + 완화 CTA |
| `422` | — | Pydantic 검증 실패 | 폼 필드별 에러 표시 |
| `500` | — | Gurobi/로직 예외 | "일시 오류" Toast |
| `504` | `timeout` | 30초 초과 | 재시도 CTA |

### 5.5 Gurobi 통합

```python
# engine/src/solvers/gurobi.py (개요)
import os
import gurobipy as gp
from gurobipy import GRB
import networkx as nx
from ..graph import Graph
from ..models import OptimizeRequest, OptimizeResult, Status
from .base import BaseSolver

class GurobiSolver(BaseSolver):
    name = "gurobi"

    def __init__(self):
        # WLS credentials via environment (injected via K8s SealedSecret)
        with gp.Env(empty=True) as env:
            env.setParam("LicenseID",    os.environ["GUROBI_LICENSE_ID"])
            env.setParam("WLSAccessID",  os.environ["GUROBI_WLS_ACCESS_ID"])
            env.setParam("WLSSecret",    os.environ["GUROBI_WLS_SECRET"])
            env.start()
            self._env = env

    def solve(self, graph: Graph, req: OptimizeRequest) -> OptimizeResult:
        # 기존 w7 코드의 모델 구성을 이 메서드에 이식
        m = gp.Model("SME_Tour", env=self._env)
        m.Params.LazyConstraints = 1
        m.Params.NumericFocus = 3
        m.Params.TimeLimit = 30            # 30초 하드 캡
        # ... 변수, 제약, 목적함수, callback, optimize ...
        # 해를 RouteEdge 리스트로 변환
        return OptimizeResult(...)
```

## 6. Frontend Design

### 6.1 라우트와 와이어프레임

**`/` — Landing + Input Form**
```
┌────────────────────────────────────────────────────────┐
│  SME Tour                          [GitHub] [테마]    │
├────────────────────────────────────────────────────────┤
│   🇪🇺 적응형 유럽 여행 경로 최적화                    │
│   예산과 일정을 입력하면 최적 경로를 찾아드립니다       │
│                                                        │
│   ┌────────────────────────────────────────┐          │
│   │ 출발 공항   [ CDG · 파리 · 🇫🇷  ▼ ]    │          │
│   │ 예산 (원)   [████████────] ₩10,000,000 │          │
│   │             ₩1M ←────────→ ₩30M        │          │
│   │ 기간 (일)   [████────────] 14          │          │
│   │             3일 ←────────→ 30일        │          │
│   │ 우선 순위   [─────●────────]           │          │
│   │             💰 비용   ⏱ 시간           │          │
│   │  [   ✨ 최적 경로 찾기   ]             │          │
│   └────────────────────────────────────────┘          │
│                                                        │
│   ℹ️ 엔진은 15개 유럽 허브와 내륙 도시를 Clustered    │
│      TSP로 탐색합니다.                                 │
└────────────────────────────────────────────────────────┘
```

**`/result?budget_won=10000000&deadline_days=14&start_hub=CDG&w_cost=0.5`**
```
┌──────────────────────────────────────────────────────────┐
│ ← 입력 수정 │ CDG · ₩1000만 · 14일 · ⚖ 균형  [🔗 공유]  │
├──────────────────────────────────────────────────────────┤
│ ┌────────────┬────────────┬────────────┬─────────────┐  │
│ │ 💰 418만원 │ ⏱ 7일 21h  │ 🌍 15개국  │ ⚙ Gurobi    │  │
│ │ total cost │ total time │ countries  │   103ms     │  │
│ └────────────┴────────────┴────────────┴─────────────┘  │
│                                                          │
│  ┌───────────────────────┐  ┌────────────────────────┐  │
│  │    🗺 Leaflet Map     │  │ 📍 경로 상세 (60 steps)│  │
│  │  ─ 허브 공항 마커      │  │                        │  │
│  │  ─ 비행 노선 (색곡선)  │  │ 01 🏘 CDG → NCE_City   │  │
│  │  ─ 지상 이동 (점선)    │  │    Ground · 50k · 6h42m│  │
│  │  ─ 방문 국가 하이라이트│  │ 02 🏘 NCE → LYS        │  │
│  │  (zoom/pan 가능)       │  │    Ground · 33k · 5h30m│  │
│  │                       │  │ 03 ✈ CDG_Exit → PRG    │  │
│  │                       │  │    Air_CZA · 246k ·1h45│  │
│  │                       │  │ (스크롤 계속...)       │  │
│  │ 모바일: 지도 위, 리스트 │                        │  │
│  │       아래             │                        │  │
│  └───────────────────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 6.2 핵심 설계 결정

1. **URL 쿼리 = SSOT** — nuqs의 `useQueryStates`로 4개 파라미터를 URL에 직결. 입력 변경 → URL 자동 갱신. `/result`는 `searchParams`를 RSC에서 파싱해 초기 fetch 수행 (SSR friendly).
2. **지도는 Client Component + dynamic import** — Leaflet은 `window` 참조가 있어 SSR 불가. `next/dynamic` + `{ ssr: false }` + Suspense로 코드 분할. 지도 번들이 `/` 경로의 초기 로드에 포함되지 않음.
3. **허브 공항 좌표는 프론트 상수** — 15개뿐이고 변화 없음. `lib/hubs.ts`에 하드코딩:
   ```ts
   export const HUBS = {
     CDG: { country_kr: "프랑스", city_kr: "파리",  iata: "CDG", lat: 49.0097, lon:  2.5479 },
     FCO: { country_kr: "이탈리아", city_kr: "로마", iata: "FCO", lat: 41.8003, lon: 12.2389 },
     // 15개 전부
   } as const;
   ```
   엔진의 `/meta/hubs` API는 **의도적으로 만들지 않음** (오버엔지니어링 방지).
4. **Zod로 응답 검증** — 백엔드 Pydantic과 수동 미러링. 스키마 변경 시 한쪽만 수정하면 드리프트 → 구현 후 contract test 1개 추가로 방어.
5. **route-list는 virtualized** (`@tanstack/react-virtual`) — 60+ 에지 렌더 성능 & 모바일 메모리 보호.
6. **공유 URL = 입력 URL** — 결과 저장 없이 매 방문 시 FastAPI 재호출. 엔진 0.1초 수준이라 UX 영향 미미.

## 7. Error & Loading Strategy

### 7.1 로딩 상태

| 위치 | 구현 | UX |
|---|---|---|
| `/result` 초기 로드 | `app/result/loading.tsx` (Next.js convention) | 지도/카드/리스트 자리에 shadcn `Skeleton` |
| 폼 제출 시 | 버튼 `disabled + Loader2 spinner` | "계산 중..." 텍스트 |
| 재시도 (URL 변경) | Suspense 재트리거 | 부드러운 전환 |

### 7.2 에러 분류 및 UX

| Kind | 트리거 | UI | Recovery |
|---|---|---|---|
| **Validation** | Zod 실패(프론트) / Pydantic 422(백) | 필드 아래 빨간 힌트 + 포커스 | 입력 수정 |
| **Network** | fetch 실패, offline | 전역 Toast + `<ErrorState/>` | 재시도 |
| **Infeasible** | `status: "infeasible"` (200) | `<InfeasibleBanner/>` | "예산 +20% 로 다시" CTA |
| **Timeout** | HTTP 504 또는 AbortController 30초 | `<TimeoutBanner/>` | 재시도 또는 조건 완화 |
| **Server 5xx** | FastAPI 예외 | `<ErrorState/>` + Toast | 재시도 |
| **Unknown** | 알 수 없는 예외 | `app/result/error.tsx` boundary | Reset 버튼 → `/` |

### 7.3 한국어 UI 문구

- **Infeasible**:
  > 현재 조건에서 15개국 모두 방문할 수 있는 경로를 찾을 수 없어요.
  > 예산을 늘리거나 기간을 더 길게 잡아보세요.
  > [예산 +20%] [기간 +3일]

- **Timeout**:
  > 경로 계산이 시간을 초과했어요. (30초)
  > 서버에 부하가 있거나 조건이 복잡할 수 있습니다.
  > [다시 시도]

- **Network**:
  > 서버에 연결할 수 없어요. 인터넷 상태를 확인해주세요.
  > [다시 시도]

### 7.4 `lib/api.ts` 스켈레톤

```typescript
const TIMEOUT_MS = 30_000;
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

export async function optimize(req: OptimizeRequest): Promise<OptimizeResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE}/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal: controller.signal,
    });
    if (res.status === 504) throw new TimeoutError();
    if (res.status === 422) throw new ValidationError(await res.json());
    if (res.status >= 500) throw new ServerError(res.status);
    if (!res.ok) throw new ApiError(res.status, await res.text());
    return OptimizeResultSchema.parse(await res.json());  // Zod
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw new TimeoutError();
    throw e;
  } finally {
    clearTimeout(timer);
  }
}
```

### 7.5 백엔드 에러 핸들링

```python
# engine/src/main.py
@app.exception_handler(RequestValidationError)
async def validation_handler(_, exc):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.post("/optimize", response_model=OptimizeResult)
def optimize(req: OptimizeRequest) -> OptimizeResult:
    start = time.perf_counter()
    try:
        return SOLVER.solve(GRAPH, req)
    except SolverTimeoutError:
        raise HTTPException(status_code=504, detail="Solver timeout")
    except SolverInfeasibleError:
        return OptimizeResult(
            status=Status.INFEASIBLE,
            route=[], total_cost_won=0, total_time_minutes=0,
            objective_value=0.0,
            solve_time_ms=int((time.perf_counter() - start) * 1000),
            solver="gurobi",
            visited_iata=[], visited_cities=[],
            engine_version=VERSION,
        )
```

Gurobi 측 타임아웃은 `m.Params.TimeLimit = 30`으로 하드 설정.

## 8. Deployment & CI/CD

### 8.1 도메인

| 용도 | 도메인 | 호스팅 | Proxied |
|---|---|---|---|
| **프론트 (prod)** | `sme-tour.json-server.win` | Vercel | ON (Cloudflare 기본) |
| **API (prod)** | `api.sme-tour.json-server.win` | 홈랩 K3s | **false** (cert-manager DNS01) |
| **프론트 프리뷰** | `*.vercel.app` | Vercel 자동 | — |

스테이징 환경은 **생략**. Vercel Preview Deployments가 내부 검토를 대체. 백엔드는 PR에서 이미지 빌드만, 배포는 main merge 후.

### 8.2 프론트엔드 배포

```
Git push → frontend/**
   ↓
Vercel GitHub integration
   ↓
Vercel Build (npm install + next build)
   ↓
   ├ main → sme-tour.json-server.win (production)
   └ 기타  → sme-tour-{sha}.vercel.app (preview)
```

- Vercel 프로젝트 설정:
  - Root Directory: `frontend/`
  - Environment variable: `NEXT_PUBLIC_API_BASE=https://api.sme-tour.json-server.win`

### 8.3 백엔드 빌드 — `.github/workflows/engine-build.yml`

```yaml
name: Build Engine Image
on:
  push:
    branches: [main]
    paths: [engine/**, .github/workflows/engine-build.yml]
  pull_request:
    paths: [engine/**]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/manamana32321/sme-tour-engine
          tags: |
            type=raw,value=latest,enable={{is_default_branch}}
            type=sha,prefix=sha-
      - uses: docker/build-push-action@v5
        with:
          context: engine
          push: ${{ github.event_name == 'push' }}
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 8.4 ArgoCD Application

```yaml
# k8s/argocd-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: sme-tour-engine
  namespace: argocd
  annotations:
    argocd-image-updater.argoproj.io/image-list: engine=ghcr.io/manamana32321/sme-tour-engine
    argocd-image-updater.argoproj.io/engine.update-strategy: digest
    argocd-image-updater.argoproj.io/engine.allow-tags: regexp:^latest$
    argocd-image-updater.argoproj.io/write-back-method: git
spec:
  project: default
  source:
    repoURL: https://github.com/manamana32321/sme-tour
    targetRevision: main
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: sme-tour
  syncPolicy:
    automated: { prune: true, selfHeal: true }
    syncOptions: [CreateNamespace=true]
```

### 8.5 Deployment 핵심

```yaml
# k8s/deployment.yaml (발췌)
spec:
  containers:
    - name: engine
      image: ghcr.io/manamana32321/sme-tour-engine:latest
      ports: [{ containerPort: 8000 }]
      env:
        - name: GUROBI_LICENSE_ID
          valueFrom:
            secretKeyRef: { name: gurobi-wls, key: license_id }
        - name: GUROBI_WLS_ACCESS_ID
          valueFrom:
            secretKeyRef: { name: gurobi-wls, key: access_id }
        - name: GUROBI_WLS_SECRET
          valueFrom:
            secretKeyRef: { name: gurobi-wls, key: secret }
        - name: CORS_ALLOWED_ORIGINS
          value: https://sme-tour.json-server.win,https://*.vercel.app,http://localhost:3000
      livenessProbe:
        httpGet: { path: /healthz, port: 8000 }
        initialDelaySeconds: 10
      readinessProbe:
        httpGet: { path: /readyz, port: 8000 }
        initialDelaySeconds: 5
      resources:
        requests: { cpu: 500m, memory: 512Mi }
        limits:   { cpu: 2000m, memory: 2Gi }
```

`gurobi-wls` Secret은 **SealedSecret**으로 git에 저장 (`k8s/sealed-secret-gurobi.yaml`).

### 8.6 관찰성

| 종류 | 도구 | 구현 |
|---|---|---|
| **로그** | Loki (기존) | FastAPI stdout → Promtail → Loki. JSON logger |
| **메트릭** | Prometheus (기존) | `prometheus-client` + `/metrics` + ServiceMonitor |
| **외부 프로빙** | Blackbox Exporter (기존) | `blackbox-targets` ConfigMap에 `api.sme-tour.json-server.win/healthz` 추가 |
| **알림** | Alertmanager → Telegram (기존) | 기존 `EndpointDown` 규칙 자동 적용 |

**커스텀 메트릭**:
```python
solve_duration = Histogram("sme_tour_solve_duration_seconds", "Solver duration", ["status"])
solve_requests = Counter  ("sme_tour_solve_requests_total",    "Total solve requests", ["status"])
graph_nodes    = Gauge    ("sme_tour_graph_nodes",             "Number of virtual nodes")
```

Grafana 대시보드 1개 provisioned (`k8s/observability/grafana-dashboard.json` — 관찰성 계층은 구현 단계에서 추가).

### 8.7 시크릿

- **`gurobi-wls`** (SealedSecret) — Gurobi WLS credentials (license_id, access_id, secret)
- 그 외 없음 (CORS 화이트리스트는 ConfigMap 또는 env value)

## 9. Risks

### 9.1 Critical

| # | 리스크 | 영향 | 완화 |
|---|---|---|---|
| C1 | **Gurobi WLS Academic의 컨테이너 환경 명시적 지원 확인 안 됨** | 컨테이너 내부에서 WLS 체크인 실패 시 엔진 미동작 | Gurobi WLS Academic Tier 존재는 **공식 확인됨 (2026-04-09)**. "cloud-based platforms" 지원 문구로 컨테이너 동작은 **높은 확률로 OK**. 실패 시 Fallback: 사용자 랩탑에서 엔진 실행 + tailscale로 K3s Ingress 대체. 최악의 경우 support.gurobi.com 문의 |
| C2 | **엔진 코드 repo 이관 필요** | 개발 시작 불가 | 사용자가 직접 w7 코드를 `engine/src/solvers/gurobi.py`로 이관 (팀 공동 저작, 저작권 이슈 없음) |

### 9.2 Medium

| # | 리스크 | 완화 |
|---|---|---|
| M2 | **Infeasible 빈발** — 사용자가 예산 타이트하게 주면 15개국 완주 불가 | 폼에 "권장 예산" 힌트 + Infeasible banner의 원클릭 완화 CTA |
| M3 | **Leaflet 시각 품질** — 기본 OSM 타일 + 기본 marker는 조악 | CartoDB Voyager 타일 교체 + Lucide divIcon + 경로 선 색상. 구현 시 1-2일 할당 |
| M4 | **API 보호 없음** (proxied=false) | 실사용자 평가 전에 CF Proxy(옵션 B: Tunnel 또는 옵션 C: 도메인 평탄화) 재검토. Phase 2 |
| M5 | **ArgoCD Image Updater write-back-method=git 동작 미검증** (이 프로젝트에선 처음) | 초기 배포 시 직접 관찰, 홈랩 다른 프로젝트에서 이미 동작 중이면 신뢰 |
| M6 | **FastAPI cold start 시 Graph 빌드 + WLS 인증 시간** | `/readyz` 통과 조건에 "그래프 빌드 완료 + 워밍업 solve 1회" 포함 |
| M7 | **Gurobi WLS 인증 실패 시 전체 엔진 다운** | `/readyz` 가 인증 검증까지 하므로 K8s가 트래픽 차단. Alertmanager Telegram 알림으로 인지 |

### 9.3 Low

| # | 리스크 | 메모 |
|---|---|---|
| L1 | Next.js 16 API가 내 지식과 다를 수 있음 | 구현 시작 전 context7로 공식 문서 재확인 |
| L2 | `*.vercel.app` CORS는 permissive | 내부 데모 수준엔 허용. 공개 전 화이트리스트 조정 |
| L3 | 지도 줌/팬 시 60+ marker 렌더 성능 | `react-leaflet-cluster` 필요시 추가 |
| L4 | WLS 네트워크 검증 주기적 호출 — 홈랩 인터넷 장애 시 영향 | 기존 모니터링이 ISP 단위 장애를 잡음 |

## 10. Open Questions

1. **Gurobi 학생 WLS 라이센스 실제 발급** — 사용자 또는 팀원 중 이미 학생 계정 보유자가 있는가? (Academic WLS 존재는 확인됨, 발급 절차 진행 필요) 신청 소요 기간 미상
2. **엔진 코드 이관 시점** — 이 문서 승인 후 즉시 이관, 또는 실구현 단계(executing-plans) 초기?
3. **실사용자 평가 구체 일정** — 13주차가 2026년 몇 월 며칠? 이에 역산해서 A 완료 데드라인
4. **홈랩 K3s Gurobi 런타임 크기** — gurobipy + gurobi 11.x (최신) 바이너리 합쳐 약 500MB. Docker 이미지가 커짐 (~1.2GB 예상). GHCR 저장/pull 시간 수용 가능한지

## 11. Future Work (Phase 2/3)

| Phase | 항목 | 우선순위 |
|---|---|---|
| **Phase 2 (B)** | URL 결과 저장 (shortId + DB) | High |
| | 사용자 계정 (magic link or OAuth) | Medium |
| | 경로 비교 (히스토리, 여러 해 나란히) | Medium |
| | CF Proxy + Tunnel or 도메인 평탄화 (보안 강화) | **High (실사용자 평가 전 필수)** |
| | 지도 시각 개선 (카토DB, 커스텀 마커, 클러스터링) | Medium |
| **Phase 3 (C)** | 슬라이더 실시간 재계산 (debounce + 캐싱) | Low |
| | 내륙 도시 선호도 입력 (drag & rank) | Low |
| | **Orienteering Problem 모드** (부분집합 경로) | **High — 종설 계획서 핵심 가치** |
| | 선호도 가중치 추가 (확장성 논의 주차 9-10 반영) | Medium |
| | 여행 중 상황 변경 재계산 (실시간 API 통합) | Low |
| **관찰성** | OpenTelemetry Traces → Tempo | Medium |
| | Grafana 대시보드 확장 (per-hub 분석, 사용자 행동) | Low |
| **솔버** | OR-Tools 대체 솔버 실험 (Gurobi 대체) | Low — 사용자 결정으로 MVP 제외 |

## 12. Appendix

### A. 15개 허브 공항

`engine/collectors/airports.py` 참조.

| 국가 | 도시 | IATA | 위도 | 경도 |
|---|---|---|---|---|
| 프랑스 | 파리 | CDG | 49.0097 | 2.5479 |
| 이탈리아 | 로마 | FCO | 41.8003 | 12.2389 |
| 스위스 | 취리히 | ZRH | 47.4647 | 8.5492 |
| 영국 | 런던 | LHR | 51.4700 | -0.4543 |
| 오스트리아 | 비엔나 | VIE | 48.1103 | 16.5697 |
| 독일 | 베를린 | BER | 52.3667 | 13.5033 |
| 네덜란드 | 암스테르담 | AMS | 52.3105 | 4.7683 |
| 벨기에 | 브뤼셀 | BRU | 50.9014 | 4.4844 |
| 덴마크 | 코펜하겐 | CPH | 55.6181 | 12.6561 |
| 폴란드 | 바르샤바 | WAW | 52.1657 | 20.9671 |
| 스페인 | 바르셀로나 | BCN | 41.2974 | 2.0833 |
| 포르투갈 | 리스본 | LIS | 38.7742 | -9.1342 |
| 크로아티아 | 자그레브 | ZAG | 45.7429 | 16.0688 |
| 헝가리 | 부다페스트 | BUD | 47.4394 | 19.2556 |
| 체코 | 프라하 | PRG | 50.1008 | 14.2600 |

### B. 참조

- **Notion 종설 5조**: https://www.notion.so/90ed32f6b7c282e9827401e4c5a88387
- **Figma (SME Tour Web Design)**: https://www.figma.com/design/m7zUgf7urseUqpik3y1Gem/SME-Tour-Web-Design (현재 비어 있음)
- **Gurobi WLS docs**: https://docs.gurobi.com/projects/optimizer/en/current/concepts/environments/configuration
- **주간보고서 DB**: Notion database id `321d32f6-b7c2-80d2-91f7-f7d189d63747`
- **w6 수리모형 모델링 (1)**: Notion page id `328d32f6-b7c2-80d9-aff5-f4434087b968`
- **w7 수리모형 모델링 (2)**: Notion page id `328d32f6-b7c2-80bc-aa5a-e270fde382f1`

---

> **이 문서는 superpowers:brainstorming 단계의 산출물입니다.**
> 다음 단계는 **superpowers:writing-plans** 을 통해 이 설계를 실행 가능한 task 리스트로 전환하는 것입니다.
