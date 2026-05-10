"use client";

import { useEffect, useState, useRef } from "react";
import { optimize, TimeoutError } from "@/lib/api";
import type { OptimizeRequest, OptimizeResult } from "@/lib/schemas";

const DEBOUNCE_MS = 800;

interface UseOptimizeReturn {
  result: OptimizeResult | null;
  loading: boolean;
  error: string | null;
}

export function useOptimize(params: OptimizeRequest): UseOptimizeReturn {
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const timer = setTimeout(async () => {
      // Cancel previous request
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setError(null);

      try {
        const res = await optimize(params);
        if (!controller.signal.aborted) {
          setResult(res);
          setLoading(false);
        }
      } catch (e) {
        if (controller.signal.aborted) return;
        setLoading(false);
        if (e instanceof TimeoutError) {
          setError("경로 계산이 시간을 초과했어요. (30초)");
        } else if (e instanceof Error) {
          setError(e.message);
        } else {
          setError("알 수 없는 오류");
        }
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [params.budget_won, params.deadline_days, params.start_hub, params.w_cost, JSON.stringify(params.required_countries), JSON.stringify(params.required_cities), JSON.stringify(params.stay_days)]);

  return { result, loading, error };
}
