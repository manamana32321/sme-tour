"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { SummaryCards } from "./summary-cards";
import { RouteList } from "./route-list";
import { InfeasibleBanner } from "@/components/shared/infeasible-banner";
import { ErrorState } from "@/components/shared/error-state";
import { CopyUrlButton } from "@/components/shared/copy-url-button";
import { formatKRW } from "@/lib/format";
import { HUBS } from "@/lib/hubs";
import type { OptimizeResult } from "@/lib/schemas";
import { Skeleton } from "@/components/ui/skeleton";

const RouteMap = dynamic(() => import("./route-map").then((m) => m.RouteMap), {
  ssr: false,
  loading: () => <Skeleton className="h-[500px] w-full rounded-lg" />,
});

interface ResultViewProps {
  result: OptimizeResult;
}

export function ResultView({ result }: ResultViewProps) {
  const sp = useSearchParams();
  const hub = HUBS[sp.get("start_hub") ?? "CDG"];

  if (result.status === "infeasible") {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-4">
        <TopBar hub={hub} />
        <InfeasibleBanner />
      </div>
    );
  }

  if (result.status === "timeout") {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-4">
        <TopBar hub={hub} />
        <ErrorState
          title="시간 초과"
          message="경로 계산이 30초를 초과했어요. 조건을 완화해보세요."
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-4">
      <TopBar hub={hub} />
      <SummaryCards result={result} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RouteMap edges={result.route} visitedIata={result.visited_iata} />
        <RouteList edges={result.route} />
      </div>
    </div>
  );
}

function TopBar({ hub }: { hub: (typeof HUBS)[keyof typeof HUBS] | undefined }) {
  const sp = useSearchParams();
  const budget = Number(sp.get("budget_won") ?? 10_000_000);
  const days = sp.get("deadline_days") ?? "14";
  const wCost = Number(sp.get("w_cost") ?? 0.5);
  const weightLabel = wCost < 0.35 ? "시간 우선" : wCost > 0.65 ? "비용 우선" : "균형";

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Link href={`/?${sp.toString()}`} className="text-sm hover:underline">
        ← 입력 수정
      </Link>
      <Separator orientation="vertical" className="h-4" />
      <div className="flex gap-1.5 flex-wrap">
        <Badge variant="secondary">{hub?.flag} {hub?.iata ?? "?"}</Badge>
        <Badge variant="secondary">{formatKRW(budget)}</Badge>
        <Badge variant="secondary">{days}일</Badge>
        <Badge variant="secondary">{weightLabel}</Badge>
      </div>
      <div className="ml-auto">
        <CopyUrlButton />
      </div>
    </div>
  );
}
