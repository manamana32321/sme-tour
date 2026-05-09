/**
 * SSOT: frontend/DESIGN.md frontmatter
 *
 * 이 파일은 DESIGN.md의 JS 컨텍스트 미러. CSS-only 컴포넌트는 Tailwind 유틸리티
 * (bg-voltage 등)를 쓰지만, Leaflet 등 JS-controlled SVG는 색 문자열이 필요하므로
 * 여기서 import한다.
 *
 * 변경 시: DESIGN.md frontmatter 먼저 수정 후 이 파일 동기화.
 */
export const DESIGN_TOKENS = {
  voltage: "#0e7c86",
  voltageSoft: "#e0f2f4",
  voltageStrong: "#0a5d65",
  map: {
    markerStart: "#3cb44a",
    markerVisited: "#1f8cff",
    markerIdle: "#b0b8c1",
    routeAir: "#924bdd",
    routeGround: "#fd9727",
    routeActive: "#0e7c86", // = voltage (활성 강조 = voltage 동일)
  },
} as const;
