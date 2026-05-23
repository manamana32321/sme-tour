/** Zod 스키마 — 백엔드 Pydantic models와 1:1 미러. */

import { z } from "zod";
import { IATA_CODES } from "./hubs";

export const StatusEnum = z.enum(["optimal", "feasible", "infeasible", "timeout"]);
export type Status = z.infer<typeof StatusEnum>;

export const OptimizeRequestSchema = z.object({
  budget_won: z.number().int().min(1_000_000).max(30_000_000),
  deadline_days: z.number().int().min(3).max(30),
  start_hub: z.string().length(3).refine((v) => IATA_CODES.includes(v), {
    message: "유효한 공항 코드가 아닙니다",
  }),
  w_cost: z.number().min(0).max(1).default(0.5),
  required_countries: z.array(z.string()).nullable().default(null),
  required_cities: z.array(z.string()).nullable().default(null),
  stay_days: z.record(z.string(), z.number().int().min(0).max(30)).nullable().default(null),
});
export type OptimizeRequest = z.infer<typeof OptimizeRequestSchema>;

export const RouteEdgeSchema = z.object({
  from_node: z.string(),
  to_node: z.string(),
  mode: z.string(),
  category: z.enum(["air", "ground", "hub_stay"]),
  cost_won: z.number(),
  time_minutes: z.number(),
});
export type RouteEdge = z.infer<typeof RouteEdgeSchema>;

/** 원 조건이 infeasible일 때 솔버가 자동 완화해서 풀어낸 대안의 입력 조건.
 *  경로/비용/시간은 OptimizeResult의 기존 필드(route, total_*)에 그대로 들어가고,
 *  여기는 **어떤 조건이 적용되었는지** 만 노출. applied_* 는 OptimizeRequest의
 *  동일 이름 필드와 1:1 — 요청값과 다르면 그 항목이 완화된 것. */
export const AlternativeSchema = z.object({
  type: z.string(),
  applied_budget_won: z.number().int(),
  applied_deadline_days: z.number().int(),
  applied_required_countries: z.array(z.string()).nullable(),
  applied_required_cities: z.array(z.string()).nullable(),
  applied_stay_days: z.record(z.string(), z.number().int()).nullable(),
});
export type Alternative = z.infer<typeof AlternativeSchema>;

export const OptimizeResultSchema = z.object({
  status: StatusEnum,
  route: z.array(RouteEdgeSchema),
  total_cost_won: z.number(),
  total_time_minutes: z.number(),
  objective_value: z.number(),
  solve_time_ms: z.number(),
  solver: z.enum(["gurobi", "ortools"]),
  visited_iata: z.array(z.string()),
  visited_cities: z.array(z.string()),
  engine_version: z.string(),
  alternative: AlternativeSchema.nullable().default(null),
  /** 대안 탐색에 쓴 wall-clock ms. null=원 해가 풀려서 대안 탐색 미진입. */
  total_search_ms: z.number().int().nullable().default(null),
});
export type OptimizeResult = z.infer<typeof OptimizeResultSchema>;
