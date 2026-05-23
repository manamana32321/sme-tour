/** 가상 노드명 → 사람이 읽을 수 있는 라벨 변환. */

import { Plane, Train, RefreshCw, HelpCircle, type LucideIcon } from "lucide-react";
import { CITY_BY_NODE } from "./cities";
import { HUBS } from "./hubs";

/**
 * `CDG_Entry` → `🇫🇷 파리 (CDG)`
 * `NCE_City` → `🇫🇷 니스` (parent hub의 국기 + 한글명)
 * 매핑 없는 `Cesky Krumlov_City` → `Cesky Krumlov` (fallback)
 */
export function formatNode(node: string): string {
  // {IATA}_Entry / {IATA}_Exit
  const hubMatch = node.match(/^([A-Z]{3})_(Entry|Exit)$/);
  if (hubMatch) {
    const hub = HUBS[hubMatch[1]];
    if (hub) return `${hub.flag} ${hub.city_kr} (${hub.iata})`;
    return hubMatch[1];
  }

  // {Name}_City — CITY_BY_NODE 매핑 있으면 한글명 + parent 국기
  if (node.endsWith("_City")) {
    const city = CITY_BY_NODE[node];
    if (city) {
      const parent = HUBS[city.parent_hub];
      return parent ? `${parent.flag} ${city.city_kr}` : city.city_kr;
    }
    return node.replace(/_City$/, "");
  }

  return node;
}

/**
 * `Air_KLM` → `<Plane /> KLM`
 * `Ground_TGV INOUI(Train)` → `<Train /> TGV INOUI`
 * `Hub_Stay` → `<RefreshCw /> 공항 경유`
 */
export function formatMode(mode: string): { Icon: LucideIcon; label: string } {
  if (mode === "Hub_Stay") {
    return { Icon: RefreshCw, label: "공항 경유" };
  }
  if (mode.startsWith("Air_")) {
    return { Icon: Plane, label: mode.replace(/^Air_/, "") };
  }
  if (mode.startsWith("Ground_")) {
    const raw = mode.replace(/^Ground_/, "");
    const clean = raw.replace(/\s*\([^)]*\)\s*$/, "");
    return { Icon: Train, label: clean || raw };
  }
  return { Icon: HelpCircle, label: mode };
}

/** 노드에서 국가 정보 추출. 내륙 도시는 parent 허브의 국가로 매핑. */
export function nodeCountry(node: string): { flag: string; country_kr: string } | null {
  const hubMatch = node.match(/^([A-Z]{3})_(Entry|Exit)$/);
  if (hubMatch) {
    const hub = HUBS[hubMatch[1]];
    if (hub) return { flag: hub.flag, country_kr: hub.country_kr };
    return null;
  }
  if (node.endsWith("_City")) {
    const city = CITY_BY_NODE[node];
    if (city) {
      const parent = HUBS[city.parent_hub];
      if (parent) return { flag: parent.flag, country_kr: parent.country_kr };
    }
  }
  return null;
}
