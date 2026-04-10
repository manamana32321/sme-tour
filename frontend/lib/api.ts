/** 엔진 API fetch 래퍼. Zod 검증 + 타임아웃 + 에러 분류. */

import { type OptimizeRequest, type OptimizeResult, OptimizeResultSchema } from "./schemas";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const TIMEOUT_MS = 35_000;

// ── 에러 클래스 ──────────────────────────────────────────
export class TimeoutError extends Error {
  constructor() { super("경로 계산이 시간을 초과했어요. (30초)"); }
}
export class ValidationError extends Error {
  detail: unknown;
  constructor(detail: unknown) { super("입력 검증 실패"); this.detail = detail; }
}
export class ServerError extends Error {
  status: number;
  constructor(status: number) { super(`서버 오류 (${status})`); this.status = status; }
}

// ── fetch 함수 ───────────────────────────────────────────
export async function optimize(req: OptimizeRequest): Promise<OptimizeResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE}/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal: controller.signal,
    });

    if (res.status === 504) throw new TimeoutError();
    if (res.status === 422) throw new ValidationError(await res.json());
    if (res.status >= 500) throw new ServerError(res.status);
    if (!res.ok) throw new ServerError(res.status);

    const json = await res.json();
    return OptimizeResultSchema.parse(json);
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw new TimeoutError();
    throw e;
  } finally {
    clearTimeout(timer);
  }
}
