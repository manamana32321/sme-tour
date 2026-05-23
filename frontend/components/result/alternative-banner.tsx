"use client";

import { AlertTriangle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EUROPEAN_HUB_LIST, EUROPEAN_IATA_CODES, HUBS } from "@/lib/hubs";
import { CITY_BY_NODE } from "@/lib/cities";
import { formatKRW } from "@/lib/format";
import type { Alternative } from "@/lib/schemas";

interface AlternativeBannerProps {
  alternative: Alternative;
  requestBudget: number;
  requestDeadline: number;
  /** 원 요청의 방문 필수 국가 (mode=full이면 null = 전체 유럽 허브). */
  requestRequiredCountries: string[] | null;
  /** 원 요청의 방문 필수 도시 (없으면 null). */
  requestRequiredCities: string[] | null;
  /** 원 요청의 도시별 체류일 (없으면 빈 객체). */
  requestStayDays: Record<string, number>;
  onApplyAlternative: () => void;
}

export function AlternativeBanner({
  alternative,
  requestBudget,
  requestDeadline,
  requestRequiredCountries,
  requestRequiredCities,
  requestStayDays,
  onApplyAlternative,
}: AlternativeBannerProps) {
  const diffs = collectDiffs(alternative, {
    requestBudget,
    requestDeadline,
    requestRequiredCountries,
    requestRequiredCities,
    requestStayDays,
  });

  return (
    <Card className="border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950">
      <CardContent className="p-5 space-y-3">
        <div className="flex items-start gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden />
          <div className="space-y-1">
            <p className="font-semibold text-sm">
              원 조건으로는 경로가 없어 자동으로 조정한 대안 결과입니다
            </p>
            <p className="text-sm text-muted-foreground">{alternative.type}</p>
          </div>
        </div>

        {diffs.length > 0 && (
          <ul className="space-y-1.5 pl-7 text-sm">
            {diffs.map((d) => (
              <li key={d.label} className="flex items-baseline gap-2 flex-wrap">
                <span className="font-medium shrink-0">{d.label}</span>
                <span className="text-muted-foreground line-through tabular-nums">
                  {d.before}
                </span>
                <ArrowRight className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden />
                <span className="tabular-nums">{d.after}</span>
              </li>
            ))}
          </ul>
        )}

        <div className="flex justify-end pt-1">
          <Button size="sm" variant="outline" onClick={onApplyAlternative}>
            이 조건으로 내 입력 업데이트
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/** 한 줄짜리 diff 항목 — 입력 조건 변경을 사람이 읽는 형태로. */
interface Diff {
  label: string;
  before: string;
  after: string;
}

interface RequestSnapshot {
  requestBudget: number;
  requestDeadline: number;
  requestRequiredCountries: string[] | null;
  requestRequiredCities: string[] | null;
  requestStayDays: Record<string, number>;
}

function collectDiffs(alt: Alternative, req: RequestSnapshot): Diff[] {
  const out: Diff[] = [];

  if (alt.applied_budget_won !== req.requestBudget) {
    out.push({
      label: "예산",
      before: formatKRW(req.requestBudget),
      after: formatKRW(alt.applied_budget_won),
    });
  }

  if (alt.applied_deadline_days !== req.requestDeadline) {
    out.push({
      label: "기간",
      before: `${req.requestDeadline}일`,
      after: `${alt.applied_deadline_days}일`,
    });
  }

  // mode=full(원 요청 null) → 전체 유럽 허브. ICN(출발/도착 전용)은 카운트 제외.
  const beforeCountries = req.requestRequiredCountries ?? EUROPEAN_IATA_CODES;
  const appliedCountries =
    alt.applied_required_countries ?? EUROPEAN_IATA_CODES;
  if (!sameSet(beforeCountries, appliedCountries)) {
    out.push({
      label: "방문 국가",
      before: formatCountryList(beforeCountries),
      after: formatCountryList(appliedCountries),
    });
  }

  const beforeCities = req.requestRequiredCities ?? [];
  const appliedCities = alt.applied_required_cities ?? [];
  if (!sameSet(beforeCities, appliedCities)) {
    out.push({
      label: "방문 도시",
      before: formatCityList(beforeCities),
      after: formatCityList(appliedCities),
    });
  }

  const appliedStay = alt.applied_stay_days ?? {};
  if (!sameStayDays(req.requestStayDays, appliedStay)) {
    out.push({
      label: "체류일",
      before: formatStayDays(req.requestStayDays),
      after: formatStayDays(appliedStay),
    });
  }

  return out;
}

function sameSet(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false;
  const setA = new Set(a);
  return b.every((x) => setA.has(x));
}

function sameStayDays(
  a: Record<string, number>,
  b: Record<string, number>,
): boolean {
  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  if (keysA.length !== keysB.length) return false;
  return keysA.every((k) => a[k] === b[k]);
}

function formatCountryList(iatas: string[]): string {
  if (iatas.length === 0) return "없음";
  if (iatas.length === EUROPEAN_HUB_LIST.length) return `전체 ${EUROPEAN_HUB_LIST.length}개국`;
  const names = iatas
    .map((iata) => HUBS[iata]?.country_kr ?? iata)
    .slice(0, 4);
  const suffix = iatas.length > 4 ? ` 외 ${iatas.length - 4}곳` : "";
  return names.join(", ") + suffix;
}

function formatCityList(nodes: string[]): string {
  if (nodes.length === 0) return "없음";
  const names = nodes
    .map((node) => CITY_BY_NODE[node]?.city_kr ?? node)
    .slice(0, 4);
  const suffix = nodes.length > 4 ? ` 외 ${nodes.length - 4}곳` : "";
  return names.join(", ") + suffix;
}

function formatStayDays(map: Record<string, number>): string {
  const entries = Object.entries(map).filter(([, d]) => d > 0);
  if (entries.length === 0) return "없음";
  const parts = entries
    .slice(0, 3)
    .map(([k, d]) => {
      const label = HUBS[k]?.city_kr ?? CITY_BY_NODE[k]?.city_kr ?? k;
      return `${label} ${d}일`;
    });
  const suffix = entries.length > 3 ? ` 외 ${entries.length - 3}곳` : "";
  return parts.join(", ") + suffix;
}
