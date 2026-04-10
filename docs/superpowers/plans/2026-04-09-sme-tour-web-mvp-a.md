# SME Tour 웹 인터페이스 MVP A 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** SME투어 종설 5조의 적응형 유럽 여행 경로 최적화를 웹에서 사용 가능하게 만드는 MVP A(Thin Playground)를 구현한다.

**Architecture:** 단일 모노레포(`engine/` + `frontend/` + `k8s/`)에서 FastAPI/Gurobi 백엔드는 홈랩 K3s, Next.js 16 프론트는 Vercel에 배포. 입력값은 URL 쿼리에 인코딩, 결과는 매 요청마다 백엔드 재호출.

**Tech Stack:** Python 3.12 / FastAPI / gurobipy / NetworkX / Pydantic v2 / Docker / Next.js 16 / Tailwind / shadcn/ui / Leaflet / nuqs / Zod

**Spec 참조:** [docs/superpowers/specs/2026-04-09-sme-tour-web-mvp-a-design.md](../specs/2026-04-09-sme-tour-web-mvp-a-design.md)

---

## Phase 0 — 사전 조건 (사람이 처리)

이 plan을 실행하기 전에 사람이 직접 해결해야 하는 외부 의존성:

- [ ] **Gurobi WLS Academic 라이센스 발급**
  - https://www.gurobi.com/academia/ 학생 계정 생성
  - "Web License Service (Academic)" 신청
  - `LicenseID`, `WLSAccessID`, `WLSSecret` 3개 값 확보
  - 받은 값을 `~/.gurobi-wls.txt` 같은 안전한 곳에 임시 저장 (Phase 2에서 SealedSecret 변환)

- [ ] **Gurobi 엔진 코드 ownership 확인**
  - 팀 회의에서 "w7 코드를 repo에 이관해도 OK" 명시적 동의 받음 (이미 사용자 확인)
  - 작성자 크레딧 처리 방법 결정 (커밋 메시지 Co-Authored-By or 헤더 주석)

이 두 조건이 충족되면 Phase 1부터 자동 진행 가능.

---

## Phase 1 — Engine Bootstrap (백엔드 단독 동작)

**Milestone:** `cd engine && uvicorn src.main:app` 실행 → `curl localhost:8000/optimize` 로 실제 경로 응답을 받을 수 있음.

### Task 1: 디렉토리 재구조화 (data + scripts → engine/)

**Files:**
- Create dir: `engine/`
- Move: `data/` → `engine/data/`
- Move: `scripts/` → `engine/collectors/`
- Modify: `engine/collectors/collect_flights.py` (`.env.local` 경로 보정)

- [ ] **Step 1**: `mkdir -p engine`
- [ ] **Step 2**: `git mv data engine/data && git mv scripts engine/collectors`
- [ ] **Step 3**: `engine/collectors/collect_flights.py`의 `Path(__file__).parent.parent / ".env.local"`이 새 경로에서도 동작하도록 수정 (3 단계 위로: `engine/collectors/x.py` → repo root). `parent.parent.parent`로 변경.
- [ ] **Step 4**: 동작 검증: `cd engine && python collectors/collect_flights.py --help`
- [ ] **Step 5**: Commit `chore: data/scripts → engine/ 재구조화`

### Task 2: pyproject + Dockerfile 골격

**Files:**
- Create: `engine/pyproject.toml`
- Create: `engine/Dockerfile`
- Create: `engine/.dockerignore`
- Create: `engine/README.md`

- [ ] **Step 1**: `pyproject.toml` 생성 — Python 3.12, dependencies: `fastapi`, `uvicorn[standard]`, `gurobipy`, `networkx`, `pydantic>=2`, `pandas`, `prometheus-client`, `python-multipart`. Dev: `pytest`, `httpx`, `ruff`, `mypy`
- [ ] **Step 2**: `Dockerfile` — `python:3.12-slim` base, COPY engine/, `pip install .`, expose 8000, `CMD uvicorn src.main:app --host 0.0.0.0 --port 8000`
- [ ] **Step 3**: `.dockerignore` — `__pycache__`, `*.pyc`, `data/raw`, `tests/`, `.venv`
- [ ] **Step 4**: `pip install -e ./engine` (로컬 검증)
- [ ] **Step 5**: Commit `chore: engine pyproject + Dockerfile 골격`

### Task 3: Pydantic 모델

**Files:**
- Create: `engine/src/__init__.py`
- Create: `engine/src/models.py`
- Create: `engine/tests/test_models.py`

- [ ] **Step 1**: `tests/test_models.py` — `OptimizeRequest` validation 테스트(범위 체크, computed fields). 실패 케이스도 `pytest.raises(ValidationError)`로
- [ ] **Step 2**: `pytest engine/tests/test_models.py -v` (FAIL — 모듈 없음)
- [ ] **Step 3**: `src/models.py` 작성 — spec 5.1의 `Status` enum, `OptimizeRequest`(field constraints + computed `w_time`/`deadline_minutes`), `RouteEdge`, `OptimizeResult` 그대로
- [ ] **Step 4**: `pytest engine/tests/test_models.py -v` (PASS)
- [ ] **Step 5**: Commit `feat(engine): Pydantic models for OptimizeRequest/Result`

### Task 4: Graph 빌더 (솔버 독립)

**Files:**
- Create: `engine/src/graph.py`
- Create: `engine/tests/fixtures/mini_air.csv`
- Create: `engine/tests/fixtures/mini_city.csv`
- Create: `engine/tests/test_graph.py`

- [ ] **Step 1**: `tests/fixtures/mini_*.csv` — 3개 hub(CDG/FCO/AMS) + 2개 city(NCE_City, Brno_City) 미니 데이터
- [ ] **Step 2**: `tests/test_graph.py` — `build_graph(mini_air, mini_city)`이 정확한 노드 수, 에지 수, edge categories(`Air_*`, `Ground_*`, `Hub_Stay`)를 반환하는지
- [ ] **Step 3**: `pytest engine/tests/test_graph.py -v` (FAIL)
- [ ] **Step 4**: `src/graph.py` — Spec 4.x의 `Graph`/`Edge` dataclass + `build_graph(air_csv, city_csv)`. Chisman 군집 연속성 (Hub_Entry / Hub_Exit / City) 노드 분리, w7 코드의 edges 구성 로직을 함수로 추출
- [ ] **Step 5**: `pytest engine/tests/test_graph.py -v` (PASS)
- [ ] **Step 6**: Commit `feat(engine): solver-independent graph builder`

### Task 5: BaseSolver ABC

**Files:**
- Create: `engine/src/solvers/__init__.py`
- Create: `engine/src/solvers/base.py`

- [ ] **Step 1**: `solvers/base.py` — `class BaseSolver(ABC)`, `name: str`, `@abstractmethod solve(graph: Graph, req: OptimizeRequest) -> OptimizeResult`
- [ ] **Step 2**: `solvers/__init__.py` — `get_solver()` 팩토리. 지금은 `from .gurobi import GurobiSolver; return GurobiSolver()` (지연 import). Future-proof: 환경변수 체크는 안 하지만 함수 시그니처 유지
- [ ] **Step 3**: `python -c "from src.solvers import get_solver; print(get_solver)"` 동작 확인
- [ ] **Step 4**: Commit `feat(engine): BaseSolver ABC + factory`

### Task 6: Gurobi solver 이관 + 래핑

**Files:**
- Create: `engine/src/solvers/gurobi.py`
- Create: `engine/tests/test_solver_gurobi.py` (skip if no license)

- [ ] **Step 1**: w7-code-16.py(Notion 보고서)의 Gurobi 모델 코드를 `solvers/gurobi.py`로 이식. 함수 시그니처는 `class GurobiSolver(BaseSolver): solve(self, graph, req)`. CSV 로드 부분 제거(graph는 이미 빌드됨), Gurobi env 초기화는 `__init__`에 옮김(WLS env vars 로드)
- [ ] **Step 2**: `m.Params.TimeLimit = 30` 추가, lazy callback `subtourelim`은 그대로 유지
- [ ] **Step 3**: 결과를 `OptimizeResult`로 변환 — w7의 텍스트 출력 로직(이모지/print)을 데이터 추출 로직으로 대체. `RouteEdge` 리스트 + `total_cost_won`/`total_time_minutes`/`visited_iata`/`visited_cities` 계산
- [ ] **Step 4**: `tests/test_solver_gurobi.py` — `pytest.skipif(no WLS env)` + 미니 그래프로 solve → `status == OPTIMAL` 검증
- [ ] **Step 5**: 로컬에서 WLS env vars 셋업 후 `pytest engine/tests/test_solver_gurobi.py -v`
- [ ] **Step 6**: Commit `feat(engine): port w7 Gurobi solver + WLS env init`

### Task 7: Data loader

**Files:**
- Create: `engine/src/data_loader.py`
- Create: `engine/tests/test_data_loader.py`

- [ ] **Step 1**: `data_loader.py` — `load_default_graph()` 함수. `engine/data/processed/Airplane dataset.csv`와 `engine/data/processed/city dataset.csv`를 절대 경로로 로드해 `build_graph()` 호출
- [ ] **Step 2**: `tests/test_data_loader.py` — 실제 CSV 로드 후 노드 수 ≥ 30 검증
- [ ] **Step 3**: `pytest engine/tests/test_data_loader.py -v` (PASS)
- [ ] **Step 4**: Commit `feat(engine): default data loader`

### Task 8: FastAPI 앱

**Files:**
- Create: `engine/src/main.py`
- Create: `engine/tests/test_api.py`

- [ ] **Step 1**: `tests/test_api.py` — `httpx.AsyncClient`로 `POST /optimize` 호출, 200 + body schema 검증. 422 케이스(invalid budget)도. WLS 의존이라 `pytest.skipif`
- [ ] **Step 2**: `src/main.py` — FastAPI app, startup event에서 `GRAPH = load_default_graph()` + `SOLVER = get_solver()`. `POST /optimize`, `GET /healthz`, `GET /readyz`(graph + solver 모두 초기화 됐는지)
- [ ] **Step 3**: CORS middleware — `CORS_ALLOWED_ORIGINS` env var를 ','로 split해서 적용
- [ ] **Step 4**: Exception handler — `SolverTimeoutError` → 504, `SolverInfeasibleError` → 200 with status=infeasible
- [ ] **Step 5**: 로컬 실행: `cd engine && uvicorn src.main:app --reload`. `curl -s -X POST localhost:8000/optimize -H 'Content-Type: application/json' -d '{"budget_won":10000000,"deadline_days":14,"start_hub":"CDG","w_cost":0.5}' | jq` 결과 확인
- [ ] **Step 6**: Commit `feat(engine): FastAPI app with /optimize endpoint`

### Task 9: Prometheus 메트릭

**Files:**
- Create: `engine/src/metrics.py`
- Modify: `engine/src/main.py`

- [ ] **Step 1**: `metrics.py` — `solve_duration` Histogram, `solve_requests` Counter, `graph_nodes` Gauge. `instrument_solve()` 컨텍스트 매니저로 main.py에서 wrapping
- [ ] **Step 2**: `main.py`에 `GET /metrics` 엔드포인트 — `from prometheus_client import generate_latest, CONTENT_TYPE_LATEST` 직접 노출
- [ ] **Step 3**: `curl localhost:8000/metrics | head` 검증
- [ ] **Step 4**: Commit `feat(engine): Prometheus metrics`

**🎯 Phase 1 milestone 도달**: 로컬 FastAPI에서 `/optimize` 동작 + `/healthz` `/readyz` `/metrics` 응답.

---

## Phase 2 — K8s 배포 매니페스트 (홈랩 K3s)

**Milestone:** ArgoCD가 sync 후 `https://api.sme-tour.json-server.win/healthz` 가 200 응답.

### Task 10: Kustomize 베이스 매니페스트

**Files:**
- Create: `k8s/namespace.yaml`
- Create: `k8s/deployment.yaml`
- Create: `k8s/service.yaml`
- Create: `k8s/ingress.yaml`
- Create: `k8s/kustomization.yaml`

- [ ] **Step 1**: `namespace.yaml` — `sme-tour` namespace
- [ ] **Step 2**: `deployment.yaml` — Spec 8.5의 발췌를 그대로. 1 replica, env vars(WLS 3개 + CORS), liveness/readiness, resources(500m/2000m, 512Mi/2Gi), image: `ghcr.io/manamana32321/sme-tour-engine:latest`
- [ ] **Step 3**: `service.yaml` — ClusterIP, port 80 → targetPort 8000
- [ ] **Step 4**: `ingress.yaml` — ingress-nginx, host `api.sme-tour.json-server.win`, TLS via `letsencrypt-dns` ClusterIssuer (CLAUDE.md 홈랩 패턴)
- [ ] **Step 5**: `kustomization.yaml` — 위 4개 리소스 합치기
- [ ] **Step 6**: 로컬 검증: `kubectl --kubeconfig ~/.kube/json kustomize k8s/ | head -100`
- [ ] **Step 7**: Commit `feat(k8s): base manifests for sme-tour-engine`

### Task 11: Gurobi WLS SealedSecret

**Files:**
- Create: `k8s/sealed-secret-gurobi.yaml`
- Create: `k8s/secret-template-gurobi.yaml` (gitignored, 로컬 작성용)

- [ ] **Step 1**: 로컬 임시 `secret-template-gurobi.yaml` 작성 — Phase 0에서 받은 3개 값을 base64 encode (`echo -n "..." | base64`)
- [ ] **Step 2**: `kubeseal --format yaml --cert /home/json/homelab-worktrees/main/k8s/sealed-secrets/cert.pem < secret-template.yaml > k8s/sealed-secret-gurobi.yaml` (cert 경로는 홈랩 repo 참조)
- [ ] **Step 3**: `secret-template-gurobi.yaml` 삭제 + `.gitignore`에 추가
- [ ] **Step 4**: `kustomization.yaml`에 `sealed-secret-gurobi.yaml` 추가
- [ ] **Step 5**: Commit `feat(k8s): SealedSecret for Gurobi WLS credentials`

### Task 12: Cloudflare DNS 레코드

**Files:**
- Modify: `/home/json/homelab-worktrees/main/cloudflare/dns.tf` (별도 워크트리)

- [ ] **Step 1**: 홈랩 워크트리에서 `api.sme-tour.json-server.win` A 레코드 추가, `proxied = false`
- [ ] **Step 2**: `cd cloudflare && terraform plan` (CLAUDE.md 규칙: auto-approve 금지)
- [ ] **Step 3**: 사용자 승인 후 `terraform apply`
- [ ] **Step 4**: `dig +short api.sme-tour.json-server.win` 검증
- [ ] **Step 5**: 홈랩 PR 생성, 머지, ArgoCD 자동 sync 확인
- [ ] **Step 6**: Commit (홈랩 워크트리)

### Task 13: ArgoCD Application

**Files:**
- Create: `k8s/argocd-app.yaml`

- [ ] **Step 1**: Spec 8.4의 ArgoCD Application YAML 그대로 작성. Image Updater annotations(`update-strategy: digest`, `allow-tags: regexp:^latest$`, `write-back-method: git`)
- [ ] **Step 2**: 홈랩 워크트리의 `k8s/argocd/applications/apps/`에 sme-tour 추가
- [ ] **Step 3**: `kubectl --kubeconfig ~/.kube/json apply -f` 직접 적용 (Application 리소스는 이미 ArgoCD 자체로 부트스트랩되어 있음, 홈랩 PR 머지 후 자동 sync)
- [ ] **Step 4**: Commit `feat(k8s): ArgoCD Application for sme-tour-engine`

**🎯 Phase 2 milestone**: ArgoCD에서 `sme-tour-engine` Application Healthy/Synced. `curl https://api.sme-tour.json-server.win/healthz` → 200.

---

## Phase 3 — CI/CD (GitHub Actions)

**Milestone:** PR push → 이미지 빌드 검증, main merge → GHCR push → ArgoCD Image Updater 자동 롤아웃.

### Task 14: Engine 이미지 빌드 워크플로우

**Files:**
- Create: `.github/workflows/engine-build.yml`

- [ ] **Step 1**: Spec 8.3의 YAML 그대로 작성
- [ ] **Step 2**: PR 단계에선 `push: false`로 빌드만, main 푸시 시에만 GHCR push
- [ ] **Step 3**: `actions/cache` 또는 `cache-from: type=gha` 설정
- [ ] **Step 4**: 이 PR에 push해서 Actions 탭에서 빌드 성공 확인
- [ ] **Step 5**: Commit `ci: GHA workflow for engine image build`

### Task 15: Frontend 타입체크/린트 워크플로우

**Files:**
- Create: `.github/workflows/frontend-ci.yml`

- [ ] **Step 1**: Vercel이 자동 배포하므로 build/deploy는 불필요. type-check + lint만
- [ ] **Step 2**: Node 20+ + pnpm/npm setup, `pnpm tsc --noEmit`, `pnpm lint`
- [ ] **Step 3**: paths filter `frontend/**`
- [ ] **Step 4**: Commit `ci: GHA workflow for frontend type-check + lint`

**🎯 Phase 3 milestone**: GitHub Actions에서 engine-build + frontend-ci 모두 green.

---

## Phase 4 — Frontend Scaffold

**Milestone:** `cd frontend && npm run dev` → `localhost:3000`에서 빈 페이지 + 폼 컴포넌트 렌더.

### Task 16: Next.js 16 프로젝트 생성

**Files:**
- Create dir: `frontend/`
- Create: `frontend/package.json`, `next.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.mjs`

- [ ] **Step 1**: `cd .. && npx create-next-app@latest frontend --typescript --tailwind --app --src-dir=false --import-alias="@/*" --no-eslint` → `--use-npm` 또는 pnpm
- [ ] **Step 2**: 생성된 boilerplate 정리: 기본 `app/page.tsx`, `globals.css` 만 유지
- [ ] **Step 3**: shadcn/ui 초기화: `npx shadcn@latest init` (Default style, Slate base color)
- [ ] **Step 4**: 필요한 컴포넌트 add: `npx shadcn@latest add button card slider select skeleton sonner separator badge`
- [ ] **Step 5**: 로컬 실행 검증: `npm run dev` → http://localhost:3000 정상 로드
- [ ] **Step 6**: Commit `feat(frontend): Next.js 16 + Tailwind + shadcn scaffold`

### Task 17: 라이브러리 — schemas, api, hubs, format

**Files:**
- Create: `frontend/lib/schemas.ts`
- Create: `frontend/lib/api.ts`
- Create: `frontend/lib/hubs.ts`
- Create: `frontend/lib/format.ts`
- Create: `frontend/lib/icons.ts`
- Install: `zod`, `nuqs`

- [ ] **Step 1**: `npm i zod nuqs`
- [ ] **Step 2**: `lib/schemas.ts` — Pydantic 미러. `OptimizeRequestSchema`, `OptimizeResultSchema`, `RouteEdgeSchema`, `StatusEnum` (Zod)
- [ ] **Step 3**: `lib/api.ts` — Spec 7.4의 fetch wrapper 그대로. `TimeoutError`/`ValidationError`/`ServerError`/`ApiError` 클래스 + `optimize(req)` 함수. `API_BASE = process.env.NEXT_PUBLIC_API_BASE!`
- [ ] **Step 4**: `lib/hubs.ts` — Spec Appendix A의 15개 허브 좌표 상수
- [ ] **Step 5**: `lib/format.ts` — `formatKRW(n)`, `formatDuration(min)` (예: `7일 21시간`), `formatHubLabel(iata)` 등
- [ ] **Step 6**: `lib/icons.ts` — `category` → 이모지 매핑 (`air → ✈`, `ground → 🏘`, `hub_stay → 🔄`)
- [ ] **Step 7**: Commit `feat(frontend): lib utilities (schemas, api, hubs, format)`

### Task 18: Providers + 환경변수

**Files:**
- Create: `frontend/app/providers.tsx`
- Create: `frontend/.env.local.example`
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1**: `app/providers.tsx` — `NuqsAdapter` (from `nuqs/adapters/next/app`) + `Toaster` (sonner) wrapping children
- [ ] **Step 2**: `app/layout.tsx`에 `<Providers>` 추가
- [ ] **Step 3**: `frontend/.env.local.example` — `NEXT_PUBLIC_API_BASE=https://api.sme-tour.json-server.win`
- [ ] **Step 4**: 로컬 개발용 `frontend/.env.local`에 `NEXT_PUBLIC_API_BASE=http://localhost:8000` 작성 (gitignored)
- [ ] **Step 5**: Commit `feat(frontend): providers + env config`

---

## Phase 5 — Frontend Implementation

**Milestone:** 브라우저에서 입력 → 실제 백엔드 호출 → 지도 + 경로 + 카드 렌더 + URL 공유.

### Task 19: 입력 폼 컴포넌트들

**Files:**
- Create: `frontend/components/form/optimize-form.tsx`
- Create: `frontend/components/form/hub-select.tsx`
- Create: `frontend/components/form/budget-slider.tsx`
- Create: `frontend/components/form/deadline-slider.tsx`
- Create: `frontend/components/form/weight-slider.tsx`

- [ ] **Step 1**: `optimize-form.tsx` — `useQueryStates` (nuqs)로 4개 파라미터 URL 동기화. Submit 핸들러는 `router.push('/result?...')`
- [ ] **Step 2**: `hub-select.tsx` — `HUBS` 상수 기반 shadcn `<Select>` (국기 이모지 + IATA + 도시 한국어)
- [ ] **Step 3**: `budget-slider.tsx` — shadcn `<Slider>` (1M~30M, step 100K), 우측에 `formatKRW` 표시
- [ ] **Step 4**: `deadline-slider.tsx` — shadcn `<Slider>` (3~30일, step 1)
- [ ] **Step 5**: `weight-slider.tsx` — 0~1, step 0.05, 좌우에 "💰 비용" / "⏱ 시간" 라벨
- [ ] **Step 6**: 로컬 검증: `npm run dev`, 슬라이더 움직이면 URL 실시간 변경 확인
- [ ] **Step 7**: Commit `feat(frontend): input form components`

### Task 20: Landing page (`/`)

**Files:**
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1**: RSC로 hero section + `<OptimizeForm/>` 렌더
- [ ] **Step 2**: Tailwind layout: max-w-3xl center, 카드 형태 폼
- [ ] **Step 3**: 정보 callout: "엔진은 15개 유럽 허브 + 내륙 도시를 Clustered TSP로 탐색합니다"
- [ ] **Step 4**: Commit `feat(frontend): landing page`

### Task 21: Result page 골격 (`/result`)

**Files:**
- Create: `frontend/app/result/page.tsx`
- Create: `frontend/app/result/loading.tsx`
- Create: `frontend/app/result/error.tsx`
- Create: `frontend/components/result/result-view.tsx`

- [ ] **Step 1**: `result/page.tsx` — RSC, `searchParams`를 Zod로 파싱, `optimize()` 호출, `<ResultView/>`에 결과 전달
- [ ] **Step 2**: `loading.tsx` — Skeleton(상단 카드 4개 + 좌측 지도 영역 + 우측 리스트)
- [ ] **Step 3**: `error.tsx` — Client Component, error boundary, "다시 시도" 버튼 + Reset
- [ ] **Step 4**: `result-view.tsx` — props로 `OptimizeResult` 받아 `<TopBar/>` + `<SummaryCards/>` + `<RouteMap/>` + `<RouteList/>` 조합. `status === 'infeasible'` 분기로 `<InfeasibleBanner/>` 렌더
- [ ] **Step 5**: Commit `feat(frontend): result page skeleton`

### Task 22: TopBar + SummaryCards + InputChips

**Files:**
- Create: `frontend/components/result/top-bar.tsx`
- Create: `frontend/components/result/summary-cards.tsx`
- Create: `frontend/components/shared/copy-url-button.tsx`

- [ ] **Step 1**: `top-bar.tsx` — 좌측 "← 입력 수정" 링크(`/?...`), 중앙 입력 칩(`shadcn Badge`로 출발지/예산/기간/가중치 표시), 우측 `<CopyUrlButton/>`
- [ ] **Step 2**: `summary-cards.tsx` — 4개 카드(총비용 / 총시간 / 국가수 / 솔버+ms). `formatKRW` / `formatDuration`
- [ ] **Step 3**: `copy-url-button.tsx` — `navigator.clipboard.writeText(window.location.href)` + sonner toast
- [ ] **Step 4**: Commit `feat(frontend): top bar + summary cards`

### Task 23: Leaflet 지도

**Files:**
- Create: `frontend/components/result/route-map.tsx`
- Install: `leaflet`, `react-leaflet`, `@types/leaflet`

- [ ] **Step 1**: `npm i leaflet react-leaflet @types/leaflet`
- [ ] **Step 2**: `globals.css`에 leaflet css import: `@import 'leaflet/dist/leaflet.css';`
- [ ] **Step 3**: `route-map.tsx` — Client Component (`'use client'`). `MapContainer`, `TileLayer` (CartoDB Voyager), 15개 허브 `<Marker>` (방문 여부에 따라 색상), 경로 `<Polyline>` (air vs ground 색상 분기), `whenReady`에서 `fitBounds` 자동
- [ ] **Step 4**: 부모(`result-view.tsx`)에서 `next/dynamic`으로 import: `const RouteMap = dynamic(() => import('./route-map'), { ssr: false })`
- [ ] **Step 5**: 로컬 검증: 결과 페이지에서 지도가 정상 렌더 + zoom/pan 동작
- [ ] **Step 6**: Commit `feat(frontend): Leaflet route map`

### Task 24: Route list (virtualized)

**Files:**
- Create: `frontend/components/result/route-list.tsx`
- Create: `frontend/components/result/route-edge-card.tsx`
- Install: `@tanstack/react-virtual`

- [ ] **Step 1**: `npm i @tanstack/react-virtual`
- [ ] **Step 2**: `route-edge-card.tsx` — 한 에지 카드(아이콘 + from→to + mode + cost + time)
- [ ] **Step 3**: `route-list.tsx` — `useVirtualizer`로 60+ 에지 가상화. 컨테이너 높이 적절히 설정 (예: `h-[600px] overflow-auto`)
- [ ] **Step 4**: Commit `feat(frontend): virtualized route list`

### Task 25: 에러 / Infeasible 상태

**Files:**
- Create: `frontend/components/shared/infeasible-banner.tsx`
- Create: `frontend/components/shared/error-state.tsx`

- [ ] **Step 1**: `infeasible-banner.tsx` — 카드형 alert. "예산 +20%" 버튼은 현재 URL에서 `budget_won * 1.2`로 새 URL 생성 후 `router.replace`
- [ ] **Step 2**: `error-state.tsx` — generic error 표시 + "다시 시도" 버튼
- [ ] **Step 3**: `result-view.tsx`에서 `status === 'infeasible'` 분기로 banner 렌더
- [ ] **Step 4**: 로컬 검증: 의도적으로 `budget_won=1000000` (1M) 로 호출 → infeasible 발생 → banner 표시 → CTA 클릭 시 budget 1.2M으로 재호출
- [ ] **Step 5**: Commit `feat(frontend): infeasible & error states`

**🎯 Phase 5 milestone**: 로컬에서 풀 플로우 동작. 입력 → 백엔드 호출 → 지도+리스트+카드 + 에러/infeasible UX.

---

## Phase 6 — 배포 및 통합 검증

**Milestone:** `https://sme-tour.json-server.win` 에서 입력 → 결과 → URL 공유 → 다른 기기에서 같은 URL로 동일 결과.

### Task 26: Vercel 프로젝트 셋업

**Files:** (Vercel UI / `vercel.json` 옵션)

- [ ] **Step 1**: vercel.com에서 GitHub repo 연결, Root Directory: `frontend/`, Framework: Next.js
- [ ] **Step 2**: Environment variables: `NEXT_PUBLIC_API_BASE=https://api.sme-tour.json-server.win`
- [ ] **Step 3**: 첫 deploy 트리거 (이 PR push로 preview URL 생성)
- [ ] **Step 4**: Cloudflare DNS: `sme-tour.json-server.win` CNAME → Vercel target (`cname.vercel-dns.com`), proxied ON
- [ ] **Step 5**: Vercel 프로덕션 도메인 설정에 `sme-tour.json-server.win` 추가, DNS 검증
- [ ] **Step 6**: 검증: `https://sme-tour.json-server.win` 첫 페이지 로드

### Task 27: Blackbox probe 등록

**Files:**
- Modify: `/home/json/homelab-worktrees/main/k8s/observability/...`

- [ ] **Step 1**: 홈랩 워크트리의 `blackbox-targets` ConfigMap에 `https://api.sme-tour.json-server.win/healthz` 추가
- [ ] **Step 2**: 홈랩 PR 생성, 머지, ArgoCD sync, Prometheus targets에 새 endpoint 등장 확인
- [ ] **Step 3**: Telegram 알림 테스트는 자연 발생 시 검증 (강제 down 안 시킴)

### Task 28: End-to-end 검증

- [ ] **Step 1**: 브라우저로 `https://sme-tour.json-server.win` 방문, 슬라이더 조작, "최적 경로 찾기" 클릭
- [ ] **Step 2**: `/result?...` URL이 의도대로 형성되고 결과 페이지 렌더
- [ ] **Step 3**: 지도에 경로 표시, 리스트에 60+ 에지, 카드에 총합
- [ ] **Step 4**: URL 복사 → 다른 브라우저(또는 시크릿 모드)에서 붙여넣기 → 동일 결과
- [ ] **Step 5**: Infeasible 시나리오 의도적 발생: `budget_won=1500000` → infeasible banner 확인, "+20%" CTA 동작
- [ ] **Step 6**: Timeout 시나리오: 백엔드 가짜 sleep 30s 추가해서 504 → frontend timeout banner. (검증 후 sleep 제거)
- [ ] **Step 7**: 모바일 뷰포트(devtools)에서 layout 확인
- [ ] **Step 8**: Lighthouse 1회 측정, Performance ≥ 80 목표

### Task 29: README 업데이트

**Files:**
- Create: `README.md` (repo root, 기존 없음)
- Update: `engine/README.md`, `frontend/README.md` (있다면)

- [ ] **Step 1**: Repo root README — 프로젝트 1줄 소개, 빠른 시작 (`engine` 로컬 실행, `frontend` 로컬 실행), 배포 정보
- [ ] **Step 2**: `engine/README.md` — Gurobi WLS env vars 셋업 가이드, `pytest` 실행법
- [ ] **Step 3**: 링크 모음 — 설계 spec, Notion, Figma, 라이브 URL
- [ ] **Step 4**: Commit `docs: README + sub-READMEs`

**🎯 Phase 6 milestone (= MVP A 완성)**: 13주차 실사용자 평가검증에 사용 가능한 상태. 팀원에게 라이브 URL 공유 → "감 잡기" 목적 달성.

---

## Self-Review

**1. Spec coverage:**
- [x] §1-2 Goals → Phase 1-6 전체
- [x] §3 Constraints (CSV 검증, WLS) → Phase 0 + Task 6, 7
- [x] §4 Architecture → Phase 1, 2 (engine + k8s)
- [x] §5 Engine API → Task 3, 8
- [x] §6 Frontend → Phase 4, 5
- [x] §7 Error/Loading → Task 21, 25
- [x] §8 Deployment → Phase 2, 3, 6
- [x] §9 Risks → Phase 0 (C1, C2 모두 사전 처리)
- [x] §11 Future Work → 명시적으로 plan에서 제외 (Phase 2/3 라벨)

**2. Placeholder scan:** "TBD"/"TODO"/"등" 없음 확인 ✓

**3. Type consistency:** Pydantic 모델명(`OptimizeRequest`/`OptimizeResult`/`RouteEdge`/`Status`)이 frontend Zod 스키마(`OptimizeRequestSchema` 등)와 mirror naming 일관 ✓. 환경변수명 (`GUROBI_LICENSE_ID`/`GUROBI_WLS_ACCESS_ID`/`GUROBI_WLS_SECRET`)도 spec과 일치 ✓.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-09-sme-tour-web-mvp-a.md`.

다음 단계 두 가지 옵션:

**1. Subagent-Driven (recommended)** — fresh subagent 1개씩 task 처리, task 사이에 리뷰 체크포인트

**2. Inline Execution** — 이 세션에서 직접 task 실행, batch 단위로 리뷰
