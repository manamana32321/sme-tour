/** 30 내륙 도시 정보 + parent hub 매핑. */

export interface InternalCity {
  node: string; // 노드명 (예: 'NCE_City') — API 식별자
  city_kr: string; // 한글 도시명
  parent_hub: string; // 부모 허브 IATA
}

export const INTERNAL_CITIES: InternalCity[] = [
  { node: "Aarhus_City", city_kr: "오르후스", parent_hub: "CPH" },
  { node: "Brno_City", city_kr: "브르노", parent_hub: "PRG" },
  { node: "Bruges_City", city_kr: "브뤼헤", parent_hub: "BRU" },
  { node: "CGN_City", city_kr: "쾰른", parent_hub: "BER" },
  { node: "Cesky Krumlov_City", city_kr: "체스키크룸로프", parent_hub: "PRG" },
  { node: "Debrecen_City", city_kr: "데브레첸", parent_hub: "BUD" },
  { node: "Dubrovnik_City", city_kr: "두브로브니크", parent_hub: "ZAG" },
  { node: "EDI_City", city_kr: "에든버러", parent_hub: "LHR" },
  { node: "FLR_City", city_kr: "피렌체", parent_hub: "FCO" },
  { node: "Faro_City", city_kr: "파루", parent_hub: "LIS" },
  { node: "Gdansk_City", city_kr: "그단스크", parent_hub: "WAW" },
  { node: "Gent_City", city_kr: "헨트", parent_hub: "BRU" },
  { node: "Hague_City", city_kr: "헤이그", parent_hub: "AMS" },
  { node: "INN_City", city_kr: "인스브루크", parent_hub: "VIE" },
  { node: "Interlaken_City", city_kr: "인터라켄", parent_hub: "ZRH" },
  { node: "Krakow_City", city_kr: "크라쿠프", parent_hub: "WAW" },
  { node: "LYS_City", city_kr: "리옹", parent_hub: "CDG" },
  { node: "Lucerne_City", city_kr: "루체른", parent_hub: "ZRH" },
  { node: "MAN_City", city_kr: "맨체스터", parent_hub: "LHR" },
  { node: "MUC_City", city_kr: "뮌헨", parent_hub: "BER" },
  { node: "Madrid_City", city_kr: "마드리드", parent_hub: "BCN" },
  { node: "NCE_City", city_kr: "니스", parent_hub: "CDG" },
  { node: "Odense_City", city_kr: "오덴세", parent_hub: "CPH" },
  { node: "Porto_City", city_kr: "포르투", parent_hub: "LIS" },
  { node: "Rotterdam_City", city_kr: "로테르담", parent_hub: "AMS" },
  { node: "SZG_City", city_kr: "잘츠부르크", parent_hub: "VIE" },
  { node: "Seville_City", city_kr: "세비야", parent_hub: "BCN" },
  { node: "Split_City", city_kr: "스플리트", parent_hub: "ZAG" },
  { node: "Szeged_City", city_kr: "세게드", parent_hub: "BUD" },
  { node: "VCE_City", city_kr: "베네치아", parent_hub: "FCO" },
];

export const CITY_BY_NODE: Record<string, InternalCity> = Object.fromEntries(
  INTERNAL_CITIES.map((c) => [c.node, c])
);

export function citiesByHub(hub: string): InternalCity[] {
  return INTERNAL_CITIES.filter((c) => c.parent_hub === hub);
}
