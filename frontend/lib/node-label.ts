/** 가상 노드명 → 사람이 읽을 수 있는 라벨 변환. */

import { HUBS } from "./hubs";

/**
 * `CDG_Entry` → `🇫🇷 파리 (CDG)`
 * `NCE_City` → `니스 (NCE)`
 * `Cesky Krumlov_City` → `Cesky Krumlov`
 */
export function formatNode(node: string): string {
  // {IATA}_Entry / {IATA}_Exit
  const hubMatch = node.match(/^([A-Z]{3})_(Entry|Exit)$/);
  if (hubMatch) {
    const hub = HUBS[hubMatch[1]];
    if (hub) return `${hub.flag} ${hub.city_kr} (${hub.iata})`;
    return hubMatch[1];
  }

  // {Name}_City
  if (node.endsWith("_City")) {
    return node.replace(/_City$/, "");
  }

  return node;
}

/**
 * `Air_KLM` → `✈️ KLM`
 * `Ground_TGV INOUI(Train)` → `🚂 TGV INOUI`
 * `Hub_Stay` → `🔄 공항 경유`
 */
export function formatMode(mode: string): { icon: string; label: string } {
  if (mode === "Hub_Stay") {
    return { icon: "🔄", label: "공항 경유" };
  }
  if (mode.startsWith("Air_")) {
    return { icon: "✈️", label: mode.replace(/^Air_/, "") };
  }
  if (mode.startsWith("Ground_")) {
    // "Ground_TGV INOUI(Train)" → "TGV INOUI"
    const raw = mode.replace(/^Ground_/, "");
    // Remove parenthetical transport type suffix like "(Train)", "(Bus)"
    const clean = raw.replace(/\s*\([^)]*\)\s*$/, "");
    return { icon: "🚂", label: clean || raw };
  }
  return { icon: "❓", label: mode };
}

/** 노드에서 국가 정보 추출 (허브만 가능, 내륙 도시는 null) */
export function nodeCountry(node: string): { flag: string; country_kr: string } | null {
  const hubMatch = node.match(/^([A-Z]{3})_(Entry|Exit)$/);
  if (hubMatch) {
    const hub = HUBS[hubMatch[1]];
    if (hub) return { flag: hub.flag, country_kr: hub.country_kr };
  }
  return null;
}
