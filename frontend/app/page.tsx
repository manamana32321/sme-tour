"use client";

import { Suspense, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useQueryStates, parseAsInteger, parseAsFloat, parseAsString, useQueryState } from "nuqs";
import { OptimizeForm, type FocusField } from "@/components/form/optimize-form";
import { SummaryCards } from "@/components/result/summary-cards";
import { RouteList } from "@/components/result/route-list";
import { InfeasibleBanner } from "@/components/shared/infeasible-banner";
import { ErrorState } from "@/components/shared/error-state";
import { CopyUrlButton } from "@/components/shared/copy-url-button";
import { ThemeToggle } from "@/components/shared/theme-toggle";
import { Skeleton } from "@/components/ui/skeleton";
import { useOptimize } from "@/hooks/use-optimize";

const RouteMap = dynamic(
  () => import("@/components/result/route-map").then((m) => m.RouteMap),
  { ssr: false, loading: () => <Skeleton className="h-[500px] w-full rounded-lg" /> }
);

const FOCUS_PULSE_MS = 2500;

function parseStayDaysString(s: string): Record<string, number> {
  if (!s) return {};
  const result: Record<string, number> = {};
  for (const part of s.split(",")) {
    const [k, v] = part.split(":");
    const days = parseInt(v, 10);
    if (k && !isNaN(days)) result[k] = days;
  }
  return result;
}

function serializeStayDays(v: Record<string, number>): string {
  return Object.entries(v)
    .filter(([, d]) => d > 0)
    .map(([k, d]) => `${k}:${d}`)
    .join(",");
}

function PageInner() {
  const [params, setParams] = useQueryStates({
    budget_won: parseAsInteger.withDefault(10_000_000),
    deadline_days: parseAsInteger.withDefault(14),
    start_hub: parseAsString.withDefault("CDG"),
    w_cost: parseAsFloat.withDefault(0.5),
  });

  const [stayDaysStr, setStayDaysStr] = useQueryState("stay_days", parseAsString.withDefault(""));
  const stayDays = parseStayDaysString(stayDaysStr);
  const setStayDays = (next: Record<string, number>) => setStayDaysStr(serializeStayDays(next));

  const [requiredCountries, setRequiredCountries] = useState<string[] | null>(null);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [focusField, setFocusField] = useState<FocusField>(null);

  useEffect(() => {
    if (focusField === null) return;
    const t = setTimeout(() => setFocusField(null), FOCUS_PULSE_MS);
    return () => clearTimeout(t);
  }, [focusField]);

  const stayDaysPayload = Object.keys(stayDays).length > 0 ? stayDays : null;

  const { result, loading, error } = useOptimize({
    budget_won: params.budget_won,
    deadline_days: params.deadline_days,
    start_hub: params.start_hub,
    w_cost: params.w_cost,
    required_countries: requiredCountries,
    stay_days: stayDaysPayload,
  });

  return (
    <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 max-w-[1600px] mx-auto w-full">
      <aside className="w-full lg:w-80 shrink-0">
        <div className="mb-4">
          <h1 className="text-2xl font-bold tracking-tight mb-1">🇪🇺 SME Tour</h1>
          <p className="text-sm text-muted-foreground">유럽 최적 여행 경로</p>
        </div>
        <OptimizeForm
          budget_won={params.budget_won}
          deadline_days={params.deadline_days}
          start_hub={params.start_hub}
          w_cost={params.w_cost}
          required_countries={requiredCountries}
          stay_days={stayDays}
          focusField={focusField}
          onBudgetChange={(v) => setParams({ budget_won: v })}
          onDeadlineChange={(v) => setParams({ deadline_days: v })}
          onHubChange={(v) => setParams({ start_hub: v })}
          onWeightChange={(v) => setParams({ w_cost: v })}
          onCountriesChange={setRequiredCountries}
          onStayDaysChange={setStayDays}
        />
      </aside>

      <main className="flex-1 min-w-0 space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {loading
              ? "계산 중..."
              : result
                ? `${result.route.length} steps · ${result.visited_iata.length}개국 · ${result.solver} · ${result.solve_time_ms}ms`
                : "슬라이더를 조작하세요"}
          </p>
          <div className="flex items-center gap-1">
            <CopyUrlButton />
            <ThemeToggle />
          </div>
        </div>

        {error && <ErrorState message={error} onRetry={() => window.location.reload()} />}
        {result?.status === "infeasible" && (
          <InfeasibleBanner
            requiredCountries={requiredCountries}
            currentBudget={params.budget_won}
            currentDays={params.deadline_days}
            onFocusBudget={() => setFocusField("budget")}
            onFocusDeadline={() => setFocusField("deadline")}
            onFocusCountries={() => setFocusField("countries")}
          />
        )}

        {loading && !result && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
            </div>
            <Skeleton className="h-[500px]" />
          </div>
        )}

        {result && result.status !== "infeasible" && (
          <div className={loading ? "opacity-40 pointer-events-none transition-opacity" : "transition-opacity"}>
            <SummaryCards result={result} />
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mt-4">
              <RouteMap
                edges={result.route}
                visitedIata={result.visited_iata}
                activeIndex={activeIndex}
                requiredCountries={requiredCountries}
                startHub={params.start_hub}
                onEdgeClick={(i) => { setOpenIndex(i); setActiveIndex(i); }}
                onEdgeHover={(i) => { if (openIndex === null) setActiveIndex(i); }}
              />
              <RouteList
                edges={result.route}
                totalCost={result.total_cost_won}
                activeIndex={activeIndex}
                openIndex={openIndex}
                onActiveChange={setActiveIndex}
                onOpenChange={setOpenIndex}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<Skeleton className="flex-1" />}>
      <PageInner />
    </Suspense>
  );
}
