---
version: 0.3
name: SME Tour
description: |
  SME Tour는 시스템경영공학 종합설계 5조의 유럽 여행 경로 다목적 최적화 데모.
  사용자가 예산·기간·가중치·국가를 입력하면 Clustered TSP 솔버가 최적 경로를 계산해
  Leaflet 지도와 단계별 리스트로 시각화한다. 디자인은 "정확한 계산 도구"의 차가운
  단정함을 지향하되 한국 사용자에게 익숙한 카카오맵의 지도 시각 관용과 토스의
  폼·타이포그래피 위계를 차용한다. 메인 voltage는 deep teal — 토스/카카오의
  대표 파랑과 분리되어 모방 인상을 피하면서 "최적화"의 학술적 인상을 강화한다.

colors:
  # Brand voltage — 자체 정의 (deep teal, 종설 톤)
  voltage: "#0e7c86"
  voltage-soft: "#e0f2f4"
  voltage-strong: "#0a5d65"
  voltage-on: "#ffffff"

  # Surface — 토스 grey scale 차용
  canvas: "#ffffff"
  surface-soft: "#f9fafb"
  surface-card: "#ffffff"
  surface-sub: "#f2f4f6"

  # Hairlines
  hairline: "#e5e8eb"
  hairline-soft: "#f2f4f6"

  # Text — 토스 grey scale 차용
  ink: "#191f28"
  body: "#4e5968"
  muted: "#8b95a1"
  placeholder: "#b0b8c1"

  # Semantic — 토스 차용
  success: "#15c47e"
  warning: "#fb8800"
  danger: "#f04452"

  # Map — 카카오맵 시각 관용 차용 (light/dark 동일)
  map-marker-start: "#3cb44a"   # 출발 (카카오 녹색 핀)
  map-marker-visited: "#1f8cff" # 방문 허브 (카카오 path blue)
  map-marker-idle: "#b0b8c1"    # 미방문
  map-route-air: "#924bdd"      # 항공 (카카오 항공 보라)
  map-route-ground: "#fd9727"   # 지상 (카카오 시내버스 오렌지) — 점선
  map-route-active: "{colors.voltage}"  # 활성 강조 = voltage 동일 (별도 색 금지)

  # Dark mode (자세한 매핑은 §13)
  dark:
    voltage: "#14a8b3"          # lightness 시프트, contrast 보존
    voltage-soft: "#0a3438"
    voltage-strong: "#3dc4cf"   # hover — light는 어둡게/dark는 밝게 반전
    canvas: "#191f28"
    surface-soft: "#252b35"
    surface-card: "#212833"
    surface-sub: "#2c3340"
    hairline: "#333d4b"
    ink: "#f9fafb"
    body: "#b0b8c1"
    muted: "#9aa3ad"            # v0.3 — light(#8b95a1)보다 밝게, 다크 surface·voltage-soft 위 가독성 보장

typography:
  font-family: "'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif"
  font-mono: "'Geist Mono', ui-monospace, monospace"
  scale:
    caption: 12        # 보조 라벨, 카드 메타
    body-sm: 13        # 단계 리스트 본문 (카카오 표준 매칭)
    body: 14           # 일반 본문
    body-strong: 15
    title-md: 16       # 카드 헤더, 인풋 라벨
    title-lg: 20       # 섹션 타이틀
    heading: 24        # 페이지 H1
    display: 28        # 큰 강조 (요약 카드 값 등 미사용 — Phase 2)
  weight:
    regular: 400
    medium: 500
    semibold: 600
    bold: 700
  letter-spacing:
    kr-tight: "-0.03em"   # 큰 헤더, 페이지 H1
    kr-normal: "-0.01em"  # 본문 한글
    kr-wide: "0"          # 영문/숫자 단독 토큰

spacing:
  grid: 4               # 4px base
  scale: [4, 8, 12, 16, 20, 24, 32, 40, 48, 64]
  sidebar-width: 320    # 폼 인풋 사이드바
  page-max-width: 1600
  card-gap: 16
  card-padding: 16
  step-icon-column: 56  # 단계 카드 좌측 아이콘 컬럼 (카카오 62px 변형)

radius:
  sm: 8
  md: 12        # 카드, 인풋 (토스 권장값)
  lg: 16
  pill: 999

motion:
  duration:
    instant: 0      # 토글 즉시
    fast: 120       # hover 색 변화, focus
    base: 200       # 카드 transition, accordion
    slow: 320       # 모달
  easing:
    out: "cubic-bezier(0.16, 1, 0.3, 1)"     # 진입 (가속 → 정지)
    in: "cubic-bezier(0.7, 0, 0.84, 0)"      # 퇴장
    inout: "cubic-bezier(0.65, 0, 0.35, 1)"
    linear: linear  # progress / indeterminate

breakpoints:
  sm: 640
  md: 768
  lg: 1024
  xl: 1280
  "2xl": 1536

components:
  - sidebar-form          # 좌측 320px 인풋 폼
  - budget-slider
  - deadline-slider
  - weight-slider
  - hub-select
  - country-select
  - summary-card          # 요약 4-grid
  - route-map             # Leaflet + Carto Voyager 타일
  - route-marker
  - route-polyline
  - route-step-card       # 단계 리스트 카드 (카카오 좌측 아이콘 컬럼 패턴)
  - infeasible-banner
  - error-state
  - copy-url-button
---

# SME Tour Design System

> 이 문서는 SME Tour 프론트엔드의 SSOT(Single Source of Truth)입니다. 디자인 변경은
> **반드시 이 문서 먼저** 수정하고 [`app/globals.css`](app/globals.css) / 컴포넌트
> 코드는 그 컴파일 산출물로 따라옵니다. 역방향 편집은 PR 리뷰에서 거부됩니다.
> 표준 포맷: [google-labs-code/design.md](https://github.com/google-labs-code/design.md).

## 1. Overview

SME Tour는 **데이터 시각화 도구의 단정한 신뢰감**을 지향합니다. 사용자가 슬라이더를 조작할 때마다 솔버가 새 경로를 계산해 지도와 리스트가 동시에 갱신되는 "라이브 인터랙션"이 핵심 경험이며, UI는 그 계산 결과를 가리지 않고 명료하게 전달하는 데 목적이 있습니다.

### Key Characteristics

- **차가운 voltage** — deep teal `{colors.voltage}` 한 색으로 CTA·링크·활성 강조를 모두 처리. 보조 voltage 신설 금지.
- **이모지 → lucide 아이콘** — UI chrome은 lucide-react로 통일. 이모지는 데이터 메타데이터(국기 등)에만 허용.
- **숫자 우선** — 비용·시간·개수 등 모든 수치는 `tabular-nums`로 정렬. 한국어 본문은 `tracking-[-0.01em]` 자동 적용.
- **지도가 hero** — 페이지 면적의 절반 이상을 지도가 차지. 마커·경로 색은 카카오맵 관용을 따라 한국 사용자 학습 비용 0.
- **양방향 하이라이트** — 지도 ↔ 단계 리스트가 hover/click으로 양방향 동기화. 활성 색은 voltage 한 색.
- **인풋은 사이드바, 결과는 메인** — 모바일에선 위→아래로 자연 적층(stack).
- **이모지 국기는 의미적 메타데이터** — 국가 표기에서만 유지(`🇫🇷 프랑스`). 장식 이모지(`💰⏱️🌍⚙️`)는 사용 금지.
- **Pretendard 단일 폰트** — 한글·영문·숫자 모두 한 폰트. 외부 CDN 의존 없이 로컬 호스팅.

## 2. Colors

### 2.1 Brand Voltage

| 토큰 | hex | 용도 |
|---|---|---|
| `{colors.voltage}` | `#0e7c86` | Primary CTA, focus ring, 활성 강조, 강조 숫자(소요 시간) |
| `{colors.voltage-soft}` | `#e0f2f4` | 활성 카드 배경, badge 배경 |
| `{colors.voltage-strong}` | `#0a5d65` | hover/active state |
| `{colors.voltage-on}` | `#ffffff` | voltage 위 텍스트 |

**왜 deep teal인가**: 토스 파랑(`#3182f6`) / 카카오 파랑(`#1f8cff`) / 카카오 자동차 네이비(`#3356b4`) 어떤 한국 메이저 서비스와도 직접 충돌하지 않아 "표절" 인상을 피합니다. 동시에 cyan-blue 계열의 차가운 톤이 "정확한 계산"을 시각적으로 신호합니다.

### 2.2 Surface

| 토큰 | hex | 용도 |
|---|---|---|
| `{colors.canvas}` | `#ffffff` | 페이지 배경 |
| `{colors.surface-soft}` | `#f9fafb` | 사이드바, hover 영역 |
| `{colors.surface-card}` | `#ffffff` | 카드 (border + shadow로 구분) |
| `{colors.surface-sub}` | `#f2f4f6` | 인풋 비활성 배경, 코드 블록 |

### 2.3 Text

| 토큰 | hex | 용도 |
|---|---|---|
| `{colors.ink}` | `#191f28` | 강조 본문, 카드 값, H1 |
| `{colors.body}` | `#4e5968` | 일반 본문 |
| `{colors.muted}` | `#8b95a1` | 보조 라벨, 메타데이터 |
| `{colors.placeholder}` | `#b0b8c1` | 인풋 placeholder, 비활성 |

### 2.4 Hairlines

| 토큰 | hex | 용도 |
|---|---|---|
| `{colors.hairline}` | `#e5e8eb` | 카드 border, 구분선 (1px) |
| `{colors.hairline-soft}` | `#f2f4f6` | 내부 구분선 (점선·약한 분할) |

### 2.5 Semantic

| 토큰 | hex | 용도 |
|---|---|---|
| `{colors.success}` | `#15c47e` | 성공, 완료 |
| `{colors.warning}` | `#fb8800` | 주의, 부분 결과 |
| `{colors.danger}` | `#f04452` | 에러, infeasible 배너 |

### 2.6 Map

지도 마커·경로색은 카카오맵 관용 컬러를 따릅니다. 한국 사용자가 무의식적으로 학습한 색-의미 매핑(녹색=출발, 보라=항공)을 활용해 학습 비용을 0으로 만듭니다.

| 토큰 | hex | 용도 |
|---|---|---|
| `{colors.map-marker-start}` | `#3cb44a` | 출발 허브 (큰 원 + ring) |
| `{colors.map-marker-visited}` | `#1f8cff` | 방문한 허브 |
| `{colors.map-marker-idle}` | `#b0b8c1` | 미방문 허브 (40% opacity) |
| `{colors.map-route-air}` | `#924bdd` | 항공 polyline (실선) |
| `{colors.map-route-ground}` | `#fd9727` | 지상 polyline (점선 `dashArray: "6 4"`) |
| `{colors.map-route-active}` | `{colors.voltage}` | 활성(클릭/hover) 경로 — voltage와 동일 |

## 3. Typography

### 3.1 Font Family

[Pretendard Variable](https://github.com/orioncactus/pretendard) 단일 폰트. 한글·영문·숫자 모두 한 패밀리에서 처리되어 weight 위계가 깨지지 않습니다. `next/font/local`로 [`public/fonts/PretendardVariable.woff2`](public/fonts/) 로컬 호스팅.

```ts
// app/fonts.ts
import localFont from 'next/font/local'
export const pretendard = localFont({
  src: '../public/fonts/PretendardVariable.woff2',
  display: 'swap',
  weight: '45 920',  // 필수 — WebKit 렌더링 버그 회피
  variable: '--font-pretendard',
  fallback: ['-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
})
```

### 3.2 Hierarchy

| 토큰 | size(px) | weight | 용도 |
|---|---|---|---|
| `{typography.caption}` | 12 | regular | 메타 라벨, 카드 보조 |
| `{typography.body-sm}` | 13 | regular | 단계 리스트 본문 |
| `{typography.body}` | 14 | regular | 일반 본문 |
| `{typography.body-strong}` | 15 | medium | 강조 본문 |
| `{typography.title-md}` | 16 | semibold | 카드 헤더, 인풋 라벨 |
| `{typography.title-lg}` | 20 | semibold | 섹션 타이틀 |
| `{typography.heading}` | 24 | bold | 페이지 H1 |

### 3.3 Korean Letter-Spacing

한글은 영문 대비 자간이 좁아야 자연스럽습니다. base 스타일에서 자동 적용:

```css
@layer base {
  body { letter-spacing: -0.01em; }
  h1, h2, h3 { letter-spacing: -0.03em; }
}
```

영문/숫자 단독 토큰(IATA 코드 `CDG`, 비용 `1,234,567원`)에는 `tracking-[0]`로 명시적 reset.

### 3.4 Numerics

비용·시간·개수 등 자릿수 정렬이 필요한 모든 숫자는 `tabular-nums` (이미 [route-edge-card.tsx:58,69](components/result/route-edge-card.tsx#L58)에서 일부 적용 중 — 전 컴포넌트로 확장).

## 4. Layout

### 4.1 Grid

- 베이스: 4px grid
- 페이지 최대 너비: `max-w-[1600px]` (현재 [page.tsx:41](app/page.tsx#L41)와 동일)
- 사이드바: `w-80` (320px), `lg:` breakpoint 이상에서만 가로 배치, 미만은 위→아래 stack

### 4.2 Surface Pacing

페이지를 surface 교차로 페이싱:

```
canvas (페이지) → surface-soft (sidebar) → canvas (메인) → surface-card (4 summary cards) → canvas (map+list 영역)
```

연속 카드 그리드 사이에 `surface-soft` 영역을 끼워 시각적 호흡을 만듭니다.

### 4.3 Whitespace

- 카드 패딩: `p-4` (16px) 기본, 단계 카드는 `py-2.5 px-3`
- 카드 간 gap: `gap-3` (12px) 또는 `gap-4` (16px)
- 섹션 간: `space-y-4`

## 5. Elevation

**단일 tier 정책** — shadcn 기본의 다단계 shadow를 사용하지 않습니다.

| 토큰 | 값 | 용도 |
|---|---|---|
| `flat` | none | 기본 카드 (`border` + `surface-card`로 구분) |
| `card` | `0 1px 2px 0 rgb(0 0 0 / 0.04)` | 떠 있어야 하는 카드(요약 카드만) |

hover에서 shadow 증가 금지 — 대신 `border-color` 또는 `surface-soft` 배경 변화로 표현.

## 6. Shapes (Radius)

| 토큰 | 값 |
|---|---|
| `{radius.sm}` | 8px (배지, 작은 인풋) |
| `{radius.md}` | 12px (카드, 인풋, 버튼 — **주력**) |
| `{radius.lg}` | 16px (모달, 큰 카드) |
| `{radius.pill}` | 999px (필터 칩) |

## 7. Components

### 7.1 Sidebar Form

좌측 [`components/form/optimize-form.tsx`](components/form/optimize-form.tsx). 5개 인풋이 한 화면에 동시 표시됩니다(토스의 "한 질문 한 화면" 패턴 비채택 — 슬라이더 라이브 피드백이 핵심이라 동시 노출 필수).

- 라벨: `text-title-md font-medium text-ink`
- 슬라이더 트랙: `bg-hairline`, fill: `bg-voltage`
- 셀렉트: shadcn `Select` 기본, `radius-md`

### 7.2 Summary Cards (4-grid)

[`components/result/summary-cards.tsx`](components/result/summary-cards.tsx). 모바일 2열, 데스크톱 4열.

- 아이콘: lucide (`Wallet` / `Clock` / `Globe` / `Cpu`) — **이모지 폐기**
- 값: `text-title-md font-semibold text-ink tabular-nums`
- 라벨: `text-caption text-muted`

### 7.3 Route Map

[`components/result/route-map.tsx`](components/result/route-map.tsx). Leaflet + Carto Voyager 타일.

- **베이스 타일**: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png` (변경 금지 — 다른 타일 갈아끼우려면 DESIGN.md 먼저 수정)
- **마커**: `CircleMarker`, 출발 9px / 방문 7px / 미방문 4px / 활성 10px
- **Polyline weight**: 일반 2px, 활성 5px (카카오 6~8px보다 얇게 — SME Tour 지도는 줌아웃 상태가 기본)
- **Polyline opacity**: 0.7
- **Ground 점선**: `dashArray: "6 4"` (활성 시 실선)
- **Tooltip**: 국기 이모지 + IATA + 한국어 도시명 (`🇫🇷 CDG · 파리`)

### 7.4 Route Step Card

[`components/result/route-edge-card.tsx`](components/result/route-edge-card.tsx). 카카오맵 단계 리스트 패턴 차용.

- **좌측 56px 컬럼**: 인덱스(`text-caption tabular-nums`) + 교통수단 아이콘
- **본문**: `text-body font-medium` 출발→도착, `text-caption text-muted` 교통수단 라벨
- **우측 정렬**: `text-body-sm tabular-nums` 비용, `text-caption tabular-nums` 시간
- **활성 카드**: `bg-voltage-soft` (현재 `bg-purple-50` 폐기)
- **확장 시**: `border-t border-dashed` + 2-col detail grid

## 8. Do's and Don'ts

### Do

1. **voltage 한 색 + map 의미색 6색만 사용**. 그 외 컬러는 `hairline`/`muted` 등 무채색에서 처리.
2. **이모지 대신 lucide 아이콘** — 단 국기는 의미적 메타데이터로 유지.
3. **모든 hex는 토큰 참조** — `{colors.voltage}` 형식. 코드에 hex inline 금지.
4. **숫자에 `tabular-nums`** — 비용/시간/개수 모두.
5. **활성 강조는 항상 `{colors.voltage}` 한 색** — purple/yellow/red 등 별도 색 금지.

### Don't

1. **shadcn 기본 다단계 shadow 사용 금지** — 단일 tier만.
2. **장식 이모지 사용 금지**(💰⏱️🌍⚙️ 등) — 종설 평가 톤 손상.
3. **map polyline에 voltage 사용 금지** — voltage는 활성 강조 전용. 일반 경로는 `map-route-air`/`map-route-ground`.
4. **여행/관광 앱 톤 차용 금지**(채도 높은 핑크·오렌지 voltage, 그라디언트 hero 등) — SME Tour는 "최적화 도구"이지 OTA가 아님.
5. **rounded radius 16px 초과 금지** — 카드를 둥글릴수록 "장난감" 인상이 강해짐.

## 9. Responsive Behavior

| Breakpoint | 동작 |
|---|---|
| `<lg` (<1024px) | 사이드바 → 페이지 최상단 stack, summary 2열, map+list 1열 적층 |
| `lg` (≥1024px) | 사이드바 좌측 고정, summary 4열 |
| `xl` (≥1280px) | map+list 2열 (현재 [page.tsx:88](app/page.tsx#L88)) |

지도 모바일 처리: 높이 `h-[400px]` (현재 500px → 모바일 축소), 터치 줌 활성화.

## 10. Agent Prompt Guide

Cursor / Claude Code에 던지는 자연어 입력 — DESIGN.md를 컨텍스트에 포함시킨 상태에서 그대로 사용.

### Quick Color Reference

```
voltage: #0e7c86 (deep teal — CTA, 활성)
ink/body/muted: #191f28 / #4e5968 / #8b95a1
canvas/surface-soft: #ffffff / #f9fafb
hairline: #e5e8eb
map: #3cb44a (출발) / #924bdd (항공) / #fd9727 (지상, 점선)
```

### Example Component Prompts

1. **요약 카드 추가** — "summary card 패턴으로 '평균 비행 시간' 카드 추가. lucide `Plane` 아이콘, voltage 컬러 사용 금지(중성톤), tabular-nums."
2. **인풋 폼 확장** — "사이드바에 '선호 항공사' multi-select 추가. shadcn Select 기반, hairline border, radius-md, 라벨은 title-md."
3. **새 마커 종류** — "지도에 '경유 추천 도시' 마커 추가. CircleMarker 5px, color는 voltage-soft(#e0f2f4) fill + voltage-strong border."
4. **에러 상태** — "infeasible-banner와 같은 톤으로 'API 타임아웃' 배너 컴포넌트. danger color, lucide `AlertTriangle`, body-strong 메시지."
5. **빈 상태** — "결과 없을 때 표시할 EmptyState. surface-soft 배경, muted 본문, lucide `MapPinOff` 아이콘 24px, voltage CTA 버튼 '슬라이더 조작하기'."

## 11. Iteration Guide

DESIGN.md 자체의 운영 룰. 6개월 뒤 본인이 까먹지 않게 박아둡니다.

1. **토큰 참조만, hex inline 금지** — 코드에 `#3b82f6` 같은 raw hex 발견 시 PR 거부.
2. **DESIGN.md → globals.css 일방향** — globals.css는 컴파일 산출물. CSS 변수 추가는 반드시 DESIGN.md frontmatter 갱신부터.
3. **새 컴포넌트는 `components` 배열에 등록** — 등록 안 된 컴포넌트는 임시 코드 취급.
4. **Variants는 별개 entry로** — `card-summary` / `card-step`처럼 분리. props로만 분기하는 variant는 토큰 컴포넌트로 인정 안 함.
5. **활성/hover 상태는 새 토큰 만들지 말 것** — voltage / voltage-strong / voltage-soft 3단계로 모두 처리.
6. **반응형 breakpoint 추가 금지** — Tailwind 기본 sm/md/lg/xl만 사용. 새 breakpoint는 DESIGN.md 합의 후.
7. **이미지/아이콘 import 일원화** — lucide-react만 사용. SVG inline·기타 아이콘 라이브러리 금지.

## 12. Known Gaps

대부분의 gap은 v0.2에서 정의됨(§13–18). 남은 미정의 영역:

- **OG / favicon / 정식 로고** — 현재 `🇪🇺 SME Tour` 텍스트로 대체 ([page.tsx:44](app/page.tsx#L44)). 워드마크 + 노드-엣지 메타포 SVG는 별도 디자인 세션 필요. 인쇄·OG 이미지에서도 동일 문제.

미구현 (Phase 2 — 실제 필요 시점에 도입):

- **§15 Form Validation** — 현재 슬라이더 위주라 invalid 상태 거의 없음. country-select 등 폼 인풋 도입 시점에 적용
- **§18 Print CSS** — 종설 발표 일주일 전 도입 권장

## 13. Dark Mode

Light voltage `#0e7c86`를 lightness 시프트로 `#14a8b3`으로 매핑. Surface는 grey-900 베이스로 반전. Map 컬러는 light/dark 동일 — 카카오맵 관용색이 양 모드에서 모두 동작합니다.

### 13.1 Token Mapping

| 토큰 | Light | Dark | 노트 |
|---|---|---|---|
| `voltage` | `#0e7c86` | `#14a8b3` | lightness 시프트, contrast 보존 |
| `voltage-soft` | `#e0f2f4` | `#0a3438` | 다크 surface 위 옅은 voltage |
| `voltage-strong` | `#0a5d65` | `#3dc4cf` | hover — light는 어둡게/dark는 밝게 **반전** |
| `voltage-on` | `#ffffff` | `#ffffff` | 동일 |
| `canvas` | `#ffffff` | `#191f28` | ink 색과 정확히 반전 |
| `surface-soft` | `#f9fafb` | `#252b35` | |
| `surface-card` | `#ffffff` | `#212833` | |
| `surface-sub` | `#f2f4f6` | `#2c3340` | |
| `hairline` | `#e5e8eb` | `#333d4b` | |
| `hairline-soft` | `#f2f4f6` | `#252b35` | |
| `ink` | `#191f28` | `#f9fafb` | |
| `body` | `#4e5968` | `#b0b8c1` | |
| `muted` | `#8b95a1` | `#9aa3ad` | **다크는 라이트보다 밝게** (§13.3 Iron Rule) |
| `placeholder` | `#b0b8c1` | `#4e5968` | dark에서 hairline보다 진하게 |
| `success` / `warning` / `danger` | 동일 | 동일 | 의미 컬러 반전 X |
| `map-*` (모든 토큰) | 동일 | 동일 | 카카오맵 관용 — 양 모드에서 가독 |

### 13.2 Activation

[next-themes](https://github.com/pacanukeha/next-themes) 이미 설치됨 (`package.json` 확인). `<html>`에 `class="dark"` 또는 `data-theme="dark"` 토글로 활성화. 기본은 `prefers-color-scheme` 자동 추적 + 사용자 토글로 override.

```tsx
// app/providers.tsx (이미 설정 영역)
<ThemeProvider attribute="class" defaultTheme="system" enableSystem>
```

### 13.3 Iron Rules

- **다크 모드의 모든 텍스트 토큰은 light 모드 대응 토큰보다 **밝거나 동등**해야 함** — `ink`/`body`/`muted`/`voltage` 모두 동일 원리. 다크에서 텍스트가 어두워지면 dark surface 대비 contrast 붕괴 (v0.2 → v0.3 수정 사례: muted `#6b7684` → `#9aa3ad`)
- **다크 모드 voltage는 light보다 **밝게**, hover/active(strong)는 더 밝게** — 일반적인 light-dark 직관과 반대 방향이지만 dark surface 대비 시인성 보장
- **shadow는 dark 모드에서 무효** — 단일 tier 정책은 light에만 적용, dark는 border + surface 단계로만 elevation 표현
- **이미지/맵 타일은 그대로** — Carto Voyager는 light 톤이지만 의미 색이 본질이라 dark에서도 light tile 유지. 다크 맵 타일로 갈아끼우지 말 것
- **새 토큰 추가 시 light/dark 모두 정의 + AA 컨트라스트 검증 필수** — frontmatter `colors.dark` 블록과 §17.1 표를 동시 갱신

## 14. Motion

전 transition/animation의 duration·easing을 frontmatter `motion` 블록에서 일원화. 키 원칙은 "위치 이동 금지, 색·투명도·크기만 허용".

### 14.1 Duration / Easing 매핑

| 용도 | 토큰 | 값 |
|---|---|---|
| hover bg, focus ring | `motion.fast` | 120ms ease-out |
| 카드 색 transition, accordion | `motion.base` | 200ms ease-out |
| 모달 in/out | `motion.slow` | 320ms ease-out |
| Indeterminate progress, skeleton pulse | `linear` | (CSS animation infinite) |

Tailwind 기본 `transition-colors`(150ms)는 `motion.fast` 근사로 그대로 허용. shadcn 기본 timing 유지.

### 14.2 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

`globals.css`의 `@layer base`에 추가. 전역 강제로 사용자 시스템 설정 100% 존중.

### 14.3 Iron Rules

- **위치 이동 (translate, slide, swipe) 금지** — 컬러/투명도/scale만 허용. 라이브 인터랙션이 핵심인 SME Tour에서 이동 애니메이션은 결과 갱신을 가림
- **Indeterminate 스피너는 linear easing** — 가속·감속 ease는 "곧 끝날 듯한 거짓 신호"
- **Accordion expand/collapse는 height auto 회피** — `data-state` 기반 grid-template-rows transition (Radix 기본)
- 활성 강조 색 변화는 항상 `motion.fast` — 슬라이더 조작 → 카드 활성 응답 즉시감

## 15. Form Validation

인풋 에러 상태 표현 패턴. SME Tour는 슬라이더 위주라 사용자 invalid 상태가 거의 없지만 `country-select`("최소 1개 선택") 등에서 사용.

### 15.1 Visual Pattern

| 상태 | 스타일 |
|---|---|
| 정상 | `border-hairline focus:border-voltage focus:ring-voltage/20` |
| 에러 | `border-danger focus:border-danger focus:ring-danger/20` |
| 비활성 | `border-hairline-soft text-placeholder cursor-not-allowed` |

에러 helper text:

```tsx
<p
  id={`${field}-error`}
  className="mt-1 flex items-center gap-1 text-caption text-danger"
>
  <AlertCircle className="h-3.5 w-3.5" aria-hidden />
  최소 1개 국가를 선택해주세요
</p>
```

### 15.2 ARIA Contract

- `aria-invalid="true"` (에러 상태 인풋)
- `aria-describedby="{field}-error"` (helper text 연결)
- form submit 시 첫 에러 필드 `el.focus({ preventScroll: false })`

### 15.3 Submit Button Behavior

전체 form invalid 시 **submit 버튼을 disable하지 말 것** — 클릭 시 어디가 잘못됐는지 안내가 더 친절. 대신 제출 후 첫 에러로 focus 이동.

```tsx
<Button onClick={handleSubmit}>
  최적 경로 찾기
</Button>
```

(SME Tour 현재 구조: 슬라이더 조작 → 자동 fetch. Submit 버튼 없음. 향후 Phase 2 폼 인풋 도입 시 위 패턴 적용)

## 16. Loading Skeleton

[shadcn Skeleton](components/ui/skeleton.tsx) 컴포넌트 사용. **Brand 톤(voltage) 적용 금지** — skeleton과 활성 강조가 시각적으로 분리되어야 "loading 중인지 강조 중인지" 혼동 방지.

### 16.1 Pattern

| 컨텐츠 | Skeleton 크기 |
|---|---|
| Summary card (4-grid) | `h-20` |
| Map | `h-[500px]` |
| Step card | `h-12` |
| Inline 텍스트 | `h-4` |

```tsx
{loading && !result && (
  <div className="space-y-4">
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
    </div>
    <Skeleton className="h-[500px]" />
  </div>
)}
```

이미 [page.tsx:79-82](app/page.tsx#L79)에 적용. 신규 컴포넌트도 동일 패턴.

### 16.2 Iron Rules

- **CLS 0** — Skeleton 크기는 실제 컨텐츠 height와 1:1 매칭. 컨텐츠 도착 시 layout shift 금지
- **Pulse animation은 `tw-animate-css`의 기본 `animate-pulse`** (linear 1.5s infinite) — 커스텀 timing 금지
- **BG는 `bg-surface-sub` (#f2f4f6)** — voltage-soft (옅은 청록)와 시각적 구분
- 1초 이상 대기 예상 시에만 skeleton 사용. 그 미만은 그냥 빈 영역 (skeleton "깜빡임" 회피)

## 17. Accessibility

WCAG 2.1 AA 타겟. 종설 평가에서 접근성 검토 포인트가 잡힐 수 있음.

### 17.1 Color Contrast (검증됨)

**Light mode:**

| 조합 | 비율 | 결과 |
|---|---|---|
| `ink #191f28` on canvas `#ffffff` | 17.4:1 | ✅ AAA |
| `body #4e5968` on canvas | 8.4:1 | ✅ AAA |
| `voltage #0e7c86` on canvas | 4.6:1 | ✅ AA |
| `voltage-on #ffffff` on voltage | 4.6:1 | ✅ AA |
| `muted #8b95a1` on canvas | 3.6:1 | ⚠️ AA large text only (≥18px 또는 ≥14px bold) |
| `danger #f04452` on canvas | 4.4:1 | ✅ AA |

**Dark mode (v0.3):**

| 조합 | 비율 | 결과 |
|---|---|---|
| `ink #f9fafb` on canvas `#191f28` | 16.7:1 | ✅ AAA |
| `body #b0b8c1` on canvas | 11.1:1 | ✅ AAA |
| `voltage #14a8b3` on canvas | 5.4:1 | ✅ AA |
| `muted #9aa3ad` on canvas | 7.4:1 | ✅ AAA |
| `muted #9aa3ad` on voltage-soft `#0a3438` | 5.1:1 | ✅ AA |
| `body #b0b8c1` on voltage-soft | 6.7:1 | ✅ AA |
| `ink #f9fafb` on voltage-soft | 12.4:1 | ✅ AAA |

⚠️ **muted는 caption(12px) 본문 사용 금지** — 라이트 모드에서 AA 미통과. 라벨/메타데이터(아이콘 옆 한 단어 등)에만. 본문은 body 이상.

ℹ️ **다크 모드 muted는 voltage-soft 위에서도 AA 통과** — 액티브 카드(`bg-voltage-soft`) 안의 detail 텍스트가 가독 (v0.2에서 발견된 회귀를 v0.3에서 수정).

### 17.2 Focus Visible

- 모든 인터랙티브 요소 — `focus-visible:outline-2 focus-visible:outline-voltage focus-visible:outline-offset-2`
- shadcn Button/Input/Select 기본 `ring` 유지 (이미 voltage 톤)
- `:focus`는 outline 제거 X — `:focus-visible`로 마우스/키보드 분기
- `globals.css`에 이미 `outline-ring/50` base 적용 ([globals.css의 @layer base](app/globals.css))

### 17.3 Keyboard Navigation

- **Tab order = visual order** — 좌측 사이드바(인풋 5개) → 메인(copy URL → 결과 카드들)
- **슬라이더**: ArrowLeft/Right 단계 조정 (Radix Slider 기본)
- **단계 카드**: `<button type="button" aria-expanded aria-controls>` 시맨틱 ([route-edge-card.tsx](components/result/route-edge-card.tsx)). Enter/Space 토글, focus-visible voltage outline
- **ESC**: 모달/드롭다운 닫기 (shadcn 기본)
- **Skip link 미설치** — 단일 페이지 SPA라 우선순위 낮음

### 17.4 Screen Reader

- **lucide 아이콘**: `aria-hidden` 일괄 적용 (이미 `formatMode`/summary-cards/route-list 적용됨)
- **Icon-only button**: `aria-label` 필수 — [copy-url-button.tsx](components/shared/copy-url-button.tsx) 검증 대상
- **Map polyline/marker**: SVG `<title>` 제한적 — Leaflet은 Tooltip 컴포넌트로 대체 (현재 적용 중)
- **`lang="ko"`** ([layout.tsx:29](app/layout.tsx#L29)) — 한국어 declaration 정확
- **로딩 상태**: `aria-live="polite"` + `role="status"` — Skeleton 영역에 누락 (Phase 2)

### 17.5 Touch Targets

모바일 인터랙티브 요소 최소 44×44px (iOS HIG / Material 48dp). 슬라이더 thumb, 버튼, 단계 카드 트리거 모두 충족. 단계 카드 chevron(`ChevronUp`/`ChevronDown`)은 버튼 전체 클릭 영역으로 해결.

### 17.6 Iron Rules

- **컬러로만 정보 전달 금지** — voltage = 활성, danger = 에러는 항상 텍스트/아이콘과 함께
- **자동 재생/캐러셀 금지** — SME Tour는 사용자 주도 인터랙션만
- **자동 focus 이동은 form submit 후 첫 에러 한정** — 기타 시점에 focus 가로채기 금지

## 18. Print

종설 발표 자료에 결과 인쇄/PDF 저장 시 사용. **현재 미구현** — 발표 일주일 전 도입 권장.

### 18.1 Print CSS

```css
@media print {
  @page {
    size: A4 portrait;
    margin: 1in;
  }

  /* Hide interactive chrome */
  aside,
  .copy-url-button,
  button[aria-expanded] svg,
  .leaflet-control-container { display: none !important; }

  /* Force expand all step cards */
  [data-state="closed"] [data-collapsible-content] {
    display: block !important;
  }

  /* Single column layout */
  .grid { display: block !important; }

  /* Map: keep but force height */
  .leaflet-container {
    height: 4in !important;
    page-break-inside: avoid;
  }

  /* Show URLs after links */
  a[href]::after {
    content: " (" attr(href) ")";
    font-size: 80%;
    color: var(--muted);
  }

  /* Step cards: avoid mid-card page break */
  [data-route-step-card] { page-break-inside: avoid; }

  /* Ink-on-paper colors */
  body { background: white !important; color: black !important; }
}
```

### 18.2 Iron Rules

- **컬러 의존 금지** — 흑백 출력 가정. voltage 강조는 `font-bold` + `underline`로 보강
- **지도 마커는 색만으로 의미 X** — print에서 출발 마커 옆 "출발" 텍스트 라벨 자동 부착 (Phase 2)
- **단계 카드는 모두 펼친 상태로 출력** — accordion 닫힘 상태 무시
- **인쇄 미리보기에서 검증 필수** — Chrome DevTools "Emulate print media" 또는 실제 PDF 출력

---

**참고**: [google-labs-code/design.md](https://github.com/google-labs-code/design.md) (포맷 표준), [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (사례 컬렉션), [orioncactus/pretendard](https://github.com/orioncactus/pretendard) (폰트), [map.kakao.com](https://map.kakao.com/) / [toss.im](https://toss.im/) (한국 reference, 토큰 추출 출처), [WCAG 2.1 AA](https://www.w3.org/TR/WCAG21/) (접근성).
