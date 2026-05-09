---
version: 0.1
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

  # Map — 카카오맵 시각 관용 차용
  map-marker-start: "#3cb44a"   # 출발 (카카오 녹색 핀)
  map-marker-visited: "#1f8cff" # 방문 허브 (카카오 path blue)
  map-marker-idle: "#b0b8c1"    # 미방문
  map-route-air: "#924bdd"      # 항공 (카카오 항공 보라)
  map-route-ground: "#fd9727"   # 지상 (카카오 시내버스 오렌지) — 점선
  map-route-active: "{colors.voltage}"  # 활성 강조 = voltage 동일 (별도 색 금지)

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

다음 영역은 현재 미정의 — 필요 시 별도 PR로 추가:

- **다크 모드** — [globals.css:86-118](app/globals.css#L86)에 shadcn 기본 다크 토큰만 존재. voltage 다크 변형(`#14a8b3`?) 미정. 현재는 light-mode only로 운영.
- **모션** — transition / animation 토큰 미정의. shadcn `tw-animate-css` 기본 사용 중.
- **Form validation 톤** — danger 컬러는 정의했지만 인풋 에러 상태 마이크로카피·아이콘·이동 패턴 미정.
- **Loading skeleton 패턴** — shadcn `Skeleton` 기본 사용 중. brand 톤 입힘 미적용.
- **OG / favicon / 로고** — 종설 발표용 정식 로고 미정. 현재 `🇪🇺 SME Tour` 텍스트로 대체 ([page.tsx:44](app/page.tsx#L44)).
- **접근성** — 컬러 대비 검증, focus visible 정책, screen reader 라벨 미감사.
- **Print 스타일** — 종설 발표 자료에 결과 출력 시 인쇄 CSS 미정의.

---

**참고**: [google-labs-code/design.md](https://github.com/google-labs-code/design.md) (포맷 표준), [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (사례 컬렉션), [orioncactus/pretendard](https://github.com/orioncactus/pretendard) (폰트), [map.kakao.com](https://map.kakao.com/) / [toss.im](https://toss.im/) (한국 reference, 토큰 추출 출처).
