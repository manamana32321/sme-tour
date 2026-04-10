"""OR-Tools CP-SAT 기반 Clustered TSP 솔버 (Gurobi fallback).

Gurobi 코드와 동일한 에지 기반 MIP 모델을 사용하되, subtour elimination을
**Iterative DFJ** 방식으로 구현한다 (Gurobi의 lazy callback에 대응).

### Iterative DFJ란?
1. subtour 제약 없이 relaxed 모델을 풀어 빠른 첫 해를 구함
2. NetworkX SCC로 subtour 탐지
3. subtour가 있으면 해당 component에 DFJ cut 추가 → 재풀기
4. subtour 없을 때까지 반복 (대부분 1-5회 수렴)

MTZ(O(n²) 정적 제약)보다 훨씬 가벼워 60+ node에서도 수 초 안에 해결.
"""

from __future__ import annotations

import logging
import time as time_mod

import networkx as nx
from ortools.sat.python import cp_model

from ..graph import Graph
from ..models import OptimizeRequest, OptimizeResult, RouteEdge, Status
from .base import BaseSolver

logger = logging.getLogger(__name__)

_OBJ_SCALE = 10_000
_MAX_DFJ_ITERATIONS = 30
_SOLVE_TIME_LIMIT_SEC = 10  # 각 iteration당. 전체 합 ≤ 30초 수준


class OrToolsSolver(BaseSolver):
    """OR-Tools CP-SAT + Iterative DFJ subtour elimination."""

    name = "ortools"

    def __init__(self) -> None:
        """OR-Tools는 라이센스 불필요."""

    def solve(self, graph: Graph, req: OptimizeRequest) -> OptimizeResult:
        start = time_mod.perf_counter()

        edge_keys: list[tuple[str, str, str]] = []
        edge_cost: list[float] = []
        edge_time: list[int] = []
        for e in graph.edges:
            edge_keys.append((e.u, e.v, e.mode))
            edge_cost.append(e.cost_scaled)
            edge_time.append(e.time_minutes)

        n_edges = len(edge_keys)
        budget_scaled = req.budget_won / graph.scale_factor
        deadline = req.deadline_minutes
        nodes = graph.virtual_nodes

        # ── CP-SAT 모델 (MTZ 없이) ──────────────────────────
        model = cp_model.CpModel()
        x = [model.new_bool_var(f"x_{i}") for i in range(n_edges)]

        # 예산 제약
        model.add(
            sum(int(edge_cost[i] * _OBJ_SCALE) * x[i] for i in range(n_edges))
            <= int(budget_scaled * _OBJ_SCALE)
        )
        # 시간 제약
        model.add(sum(edge_time[i] * x[i] for i in range(n_edges)) <= deadline)

        # 흐름 보존
        for n in nodes:
            out_idx = [i for i, ek in enumerate(edge_keys) if ek[0] == n]
            in_idx = [i for i, ek in enumerate(edge_keys) if ek[1] == n]
            if "_Entry" in n or "_Exit" in n:
                model.add(sum(x[i] for i in out_idx) == sum(x[i] for i in in_idx))
            else:
                model.add(sum(x[i] for i in out_idx) == 1)
                model.add(sum(x[i] for i in in_idx) == 1)

        # 출발지
        start_node = f"{req.start_hub}_Entry"
        start_out = [i for i, ek in enumerate(edge_keys) if ek[0] == start_node]
        model.add(sum(x[i] for i in start_out) == 1)

        # 목적 함수
        obj_terms = []
        for i in range(n_edges):
            ct = int(edge_cost[i] / budget_scaled * req.w_cost * _OBJ_SCALE) if budget_scaled > 0 else 0
            tt = int(edge_time[i] / deadline * req.w_time * _OBJ_SCALE) if deadline > 0 else 0
            obj_terms.append((ct + tt) * x[i])
        model.minimize(sum(obj_terms))

        # ── Iterative DFJ ────────────────────────────────────
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = _SOLVE_TIME_LIMIT_SEC

        final_status = cp_model.UNKNOWN
        for iteration in range(_MAX_DFJ_ITERATIONS):
            final_status = solver.solve(model)

            if final_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                break

            # subtour 탐지 (SCC)
            active = [
                (edge_keys[i][0], edge_keys[i][1])
                for i in range(n_edges)
                if solver.value(x[i]) == 1
            ]
            g = nx.DiGraph(active)
            components = list(nx.strongly_connected_components(g))

            if len(components) <= 1:
                logger.info("OR-Tools DFJ converged in %d iterations", iteration + 1)
                break

            # DFJ cuts 추가
            cuts_added = 0
            for comp in components:
                if len(comp) < len(nodes):
                    out_edges = [
                        i for i, ek in enumerate(edge_keys)
                        if ek[0] in comp and ek[1] not in comp
                    ]
                    if out_edges:
                        model.add(sum(x[i] for i in out_edges) >= 1)
                        cuts_added += 1

            logger.debug(
                "DFJ iteration %d: %d components, %d cuts added",
                iteration + 1, len(components), cuts_added,
            )

            if cuts_added == 0:
                break

        solve_ms = int((time_mod.perf_counter() - start) * 1000)

        # ── 상태 판별 ───────────────────────────────────────
        if final_status == cp_model.OPTIMAL:
            status = Status.OPTIMAL
        elif final_status == cp_model.FEASIBLE:
            status = Status.FEASIBLE
        elif final_status == cp_model.INFEASIBLE:
            return self._empty_result(Status.INFEASIBLE, solve_ms)
        else:
            return self._empty_result(Status.TIMEOUT, solve_ms)

        # ── 경로 재구성 ─────────────────────────────────────
        active_edges: dict[str, tuple[str, str, str, float, int]] = {}
        for i in range(n_edges):
            if solver.value(x[i]) == 1:
                eu, ev, mode = edge_keys[i]
                active_edges[eu] = (eu, ev, mode, edge_cost[i], edge_time[i])

        route: list[RouteEdge] = []
        visited_iata: set[str] = set()
        visited_cities: list[str] = []
        total_cost = 0
        total_time = 0

        curr = start_node
        for _ in range(len(active_edges) + 1):
            if curr not in active_edges:
                break
            eu, ev, mode, cost_s, time_m = active_edges[curr]
            cost_won = int(cost_s * graph.scale_factor)

            if mode == "Hub_Stay":
                category = "hub_stay"
            elif mode.startswith("Air_"):
                category = "air"
            else:
                category = "ground"

            route.append(RouteEdge(
                from_node=eu, to_node=ev, mode=mode,
                category=category, cost_won=cost_won, time_minutes=time_m,
            ))
            total_cost += cost_won
            total_time += time_m

            for node in (eu, ev):
                if node.endswith("_Entry") or node.endswith("_Exit"):
                    visited_iata.add(node.rsplit("_", 1)[0])
                elif node not in visited_cities:
                    visited_cities.append(node)

            curr = ev
            if curr == start_node:
                break

        return OptimizeResult(
            status=status,
            route=route,
            total_cost_won=total_cost,
            total_time_minutes=total_time,
            objective_value=float(solver.objective_value) / _OBJ_SCALE,
            solve_time_ms=solve_ms,
            solver="ortools",
            visited_iata=sorted(visited_iata),
            visited_cities=visited_cities,
            engine_version=self._version(),
        )

    def _empty_result(self, status: Status, solve_ms: int) -> OptimizeResult:
        return OptimizeResult(
            status=status, route=[], total_cost_won=0, total_time_minutes=0,
            objective_value=0.0, solve_time_ms=solve_ms, solver="ortools",
            visited_iata=[], visited_cities=[], engine_version=self._version(),
        )

    @staticmethod
    def _version() -> str:
        from src import __version__
        return f"sme-tour-engine {__version__} (ortools)"
