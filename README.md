# SME Tour

사용자의 제약 조건(예산, 기간)과 선호도를 고려한 **적응형 유럽 여행 경로 다목적 최적화** 웹 서비스.

시스템경영공학 종합설계 5조 프로젝트.

**[https://sme-tour.json-server.win](https://sme-tour.json-server.win)**

## 주요 기능

- 예산 / 기간 / 출발 공항 / 비용-시간 가중치 입력
- 16개 허브 출발 (유럽 15개국 + ICN 인천)
- 방문 모드 토글 — "전체 완주"(15개국 모두) / "선택 방문"(원하는 도시만)
- 도시 단위 강제 + 체류일 (`stay_days`) 설정
- Clustered TSP 기반 최적 경로 실시간 계산
- 원 조건이 풀리지 않으면 예산·기간·방문 도시 조정안 자동 제시
- 지도 시각화 (항공: 파란 실선, 지상: 주황 점선, 출발지: 초록 마커)
- 경로 상세 드롭다운 (누적 비용/시간, 국가 이동, 교통수단)
- 지도 ↔ 리스트 양방향 하이라이트
- 다크모드 (시스템 / 라이트 / 다크)

## 기술 스택

| 계층 | 기술 |
|---|---|
| **프론트엔드** | Next.js 16, Tailwind CSS, shadcn/ui (base-nova), Leaflet, nuqs, next-themes |
| **백엔드** | FastAPI, OR-Tools CP-SAT (Gurobi fallback) |
| **인프라** | Vercel (프론트), K3s + ArgoCD (엔진), Cloudflare DNS |
| **CI/CD** | GitHub Actions → GHCR → ArgoCD Image Updater |

## 아키텍처

```
사용자 브라우저
  → Vercel (Next.js SSR/CSR)
    → https://api.sme-tour.json-server.win (FastAPI)
      → OR-Tools CP-SAT Iterative DFJ solver
        → 최적 경로 JSON 응답
```

## 로컬 개발

### 엔진

```bash
cd engine
uv venv --python 3.12
uv pip install -e '.[dev]'
uv run pytest -v              # 109 tests (Gurobi 미설치 환경에서 45 skipped)
uv run uvicorn src.main:app --reload --port 8000
```

### 프론트엔드

```bash
cd frontend
pnpm install
pnpm dev --port 3000          # http://localhost:3000
```

`.env.local`에 `NEXT_PUBLIC_API_BASE=http://localhost:8000` 설정.

## 팀

SME투어 (시스템경영공학 종합설계 5조)

- 조혁진 (팀장), 전진석, 유지웅, 박경민, 손장수, 윤강희
