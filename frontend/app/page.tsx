"use client";

import { Suspense, useState } from "react";
import dynamic from "next/dynamic";
import { useQueryStates, parseAsInteger, parseAsFloat, parseAsString, parseAsArrayOf } from "nuqs";
import { OptimizeForm } from "@/components/form/optimize-form";
import { SummaryCards } from "@/components/result/summary-cards";
import { RouteList } from "@/components/result/route-list";
import { InfeasibleBanner } from "@/components/shared/infeasible-banner";
import { ErrorState } from "@/components/shared/error-state";
import { CopyUrlButton } from "@/components/shared/copy-url-button";
import { Skeleton } from "@/components/ui/skeleton";
import { useOptimize } from "@/hooks/use-optimize";

const RouteMap = dynamic(
  () => import("@/components/result/route-map").then((m) => m.RouteMap),
  { ssr: false, loading: () => <Skeleton className="h-[500px] w-full rounded-lg" /> }
);

function PageInner() {
  const [params, setParams] = useQueryStates({
    budget_won: parseAsInteger.withDefault(10_000_000),
    deadline_days: parseAsInteger.withDefault(14),
    start_hub: parseAsString.withDefault("CDG"),
    w_cost: parseAsFloat.withDefault(0.5),
  });

  const [requiredCountries, setRequiredCountries] = useState<string[] | null>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const { result, loading, error } = useOptimize({
    budget_won: params.budget_won,
    deadline_days: params.deadline_days,
    start_hub: params.start_hub,
    w_cost: params.w_cost,
    required_countries: requiredCountries,
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
          onBudgetChange={(v) => setParams({ budget_won: v })}
          onDeadlineChange={(v) => setParams({ deadline_days: v })}
          onHubChange={(v) => setParams({ start_hub: v })}
          onWeightChange={(v) => setParams({ w_cost: v })}
          onCountriesChange={setRequiredCountries}
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
          <CopyUrlButton />
        </div>

        {error && <ErrorState message={error} onRetry={() => window.location.reload()} />}
        {result?.status === "infeasible" && <InfeasibleBanner />}

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
              <RouteMap edges={result.route} visitedIata={result.visited_iata} hoveredIndex={hoveredIndex} />
              <RouteList edges={result.route} totalCost={result.total_cost_won} onHover={setHoveredIndex} />
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
