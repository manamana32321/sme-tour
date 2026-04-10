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
});
export type OptimizeResult = z.infer<typeof OptimizeResultSchema>;
