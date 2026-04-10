import { Suspense } from "react";
import { ResultView } from "@/components/result/result-view";
import { optimize } from "@/lib/api";
import { OptimizeRequestSchema } from "@/lib/schemas";
import { ErrorState } from "@/components/shared/error-state";
import { Skeleton } from "@/components/ui/skeleton";

interface ResultPageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function ResultPage({ searchParams }: ResultPageProps) {
  const sp = await searchParams;

  const parsed = OptimizeRequestSchema.safeParse({
    budget_won: Number(sp.budget_won),
    deadline_days: Number(sp.deadline_days),
    start_hub: String(sp.start_hub ?? "CDG"),
    w_cost: Number(sp.w_cost ?? 0.5),
  });

  if (!parsed.success) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <ErrorState
          title="잘못된 입력"
          message={`입력값을 확인해주세요: ${parsed.error.issues.map((i) => i.message).join(", ")}`}
        />
      </div>
    );
  }

  let result;
  try {
    result = await optimize(parsed.data);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "알 수 없는 오류";
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <ErrorState title="서버 오류" message={msg} />
      </div>
    );
  }

  return (
    <Suspense fallback={<ResultSkeleton />}>
      <ResultView result={result} />
    </Suspense>
  );
}

function ResultSkeleton() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-4">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Skeleton className="h-[500px]" />
        <Skeleton className="h-[500px]" />
      </div>
    </div>
  );
}
