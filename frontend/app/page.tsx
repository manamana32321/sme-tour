import { Suspense } from "react";
import { OptimizeForm } from "@/components/form/optimize-form";
import { Skeleton } from "@/components/ui/skeleton";

export default function HomePage() {
  return (
    <main className="flex-1 flex flex-col items-center justify-center px-4 py-12">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          🇪🇺 SME Tour
        </h1>
        <p className="mt-2 text-muted-foreground">
          예산과 일정을 입력하면 15개국 유럽 최적 여행 경로를 찾아드립니다
        </p>
      </div>

      <Suspense fallback={<Skeleton className="w-full max-w-lg h-80" />}>
        <OptimizeForm />
      </Suspense>

      <p className="mt-6 text-xs text-muted-foreground max-w-md text-center">
        Clustered TSP 기반 다목적 최적화 엔진이 15개 허브 공항과 내륙 도시를 탐색합니다.
        시스템경영공학 종합설계 5조 프로젝트.
      </p>
    </main>
  );
}
