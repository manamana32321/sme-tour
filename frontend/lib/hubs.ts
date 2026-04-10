/** 15개국 허브 공항 상수. 변동 없으므로 프론트 하드코딩. */

export interface Hub {
  iata: string;
  country_kr: string;
  city_kr: string;
  flag: string;
  lat: number;
  lon: number;
}

export const HUBS: Record<string, Hub> = {
  CDG: { iata: "CDG", country_kr: "프랑스", city_kr: "파리", flag: "🇫🇷", lat: 49.0097, lon: 2.5479 },
  FCO: { iata: "FCO", country_kr: "이탈리아", city_kr: "로마", flag: "🇮🇹", lat: 41.8003, lon: 12.2389 },
  ZRH: { iata: "ZRH", country_kr: "스위스", city_kr: "취리히", flag: "🇨🇭", lat: 47.4647, lon: 8.5492 },
  LHR: { iata: "LHR", country_kr: "영국", city_kr: "런던", flag: "🇬🇧", lat: 51.47, lon: -0.4543 },
  VIE: { iata: "VIE", country_kr: "오스트리아", city_kr: "비엔나", flag: "🇦🇹", lat: 48.1103, lon: 16.5697 },
  BER: { iata: "BER", country_kr: "독일", city_kr: "베를린", flag: "🇩🇪", lat: 52.3667, lon: 13.5033 },
  AMS: { iata: "AMS", country_kr: "네덜란드", city_kr: "암스테르담", flag: "🇳🇱", lat: 52.3105, lon: 4.7683 },
  BRU: { iata: "BRU", country_kr: "벨기에", city_kr: "브뤼셀", flag: "🇧🇪", lat: 50.9014, lon: 4.4844 },
  CPH: { iata: "CPH", country_kr: "덴마크", city_kr: "코펜하겐", flag: "🇩🇰", lat: 55.6181, lon: 12.6561 },
  WAW: { iata: "WAW", country_kr: "폴란드", city_kr: "바르샤바", flag: "🇵🇱", lat: 52.1657, lon: 20.9671 },
  BCN: { iata: "BCN", country_kr: "스페인", city_kr: "바르셀로나", flag: "🇪🇸", lat: 41.2974, lon: 2.0833 },
  LIS: { iata: "LIS", country_kr: "포르투갈", city_kr: "리스본", flag: "🇵🇹", lat: 38.7742, lon: -9.1342 },
  ZAG: { iata: "ZAG", country_kr: "크로아티아", city_kr: "자그레브", flag: "🇭🇷", lat: 45.7429, lon: 16.0688 },
  BUD: { iata: "BUD", country_kr: "헝가리", city_kr: "부다페스트", flag: "🇭🇺", lat: 47.4394, lon: 19.2556 },
  PRG: { iata: "PRG", country_kr: "체코", city_kr: "프라하", flag: "🇨🇿", lat: 50.1008, lon: 14.26 },
} as const;

export const HUB_LIST = Object.values(HUBS);
export const IATA_CODES = Object.keys(HUBS);
