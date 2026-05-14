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
from ..models import OptimizeRequest, OptimizeResult, Status
from ._shared import ActiveEdge, reconstruct_route, stay_time_minutes
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
        self._last_y_values: dict[str, int] | None = None

    def solve(self, graph: Graph, req: OptimizeRequest) -> OptimizeResult:
        start = time_mod.perf_counter()
        # 매 호출 시작 시 디버그 인터페이스 reset (이전 호출의 stale state 방지)
        self._last_y_values = None

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

        # 필수 방문 국가 결정
        required = set(req.required_countries) if req.required_countries is not None else graph.hubs

        # ── y[d] 도시 방문 결정변수 ──────────────────────────
        # 내륙 도시 단위 (도시 1개 = y 1개)
        y_city = {
            c: model.new_bool_var(f"y_city_{c}")
            for c in graph.internal_cities
        }

        # 허브 단위 (Entry/Exit 묶음 → y 1개)
        y_hub = {
            h: model.new_bool_var(f"y_hub_{h}")
            for h in graph.hubs
        }

        # 시간 제약 (이동시간 + 체류시간)
        # stay_days[d] * 1440 (분/일) * y[d] (방문 여부)를 합산
        stay_days = req.stay_days or {}
        all_y = {**y_city, **y_hub}
        stay_terms = [
            stay_days.get(d, 0) * 1440 * all_y[d]
            for d in (graph.internal_cities | graph.hubs)
        ]
        model.add(
            sum(edge_time[i] * x[i] for i in range(n_edges))
            + sum(stay_terms)
            <= deadline
        )

        # 허브 가상 노드 집합 (substring 매치보다 안전)
        hub_virtual_nodes = {f"{h}_Entry" for h in graph.hubs} | {f"{h}_Exit" for h in graph.hubs}

        # 허브 방문 = h_Entry로부터의 어떤 outflow든 1번 발생 (Hub_Stay 또는 Ground out)
        # TSP 흐름 보존으로 h_Entry outflow 합은 0 또는 1 (방문 여부와 일치)
        # 시작 허브는 start_out == 1로 인해 자동으로 y_hub == 1
        for h in graph.hubs:
            h_entry_out_idx = [
                i for i, ek in enumerate(edge_keys)
                if ek[0] == f"{h}_Entry"
            ]
            if not h_entry_out_idx:
                raise ValueError(
                    f"허브 {h}에 h_Entry outflow 에지가 없음 — 그래프 구조 이상"
                )
            model.add(sum(x[i] for i in h_entry_out_idx) == y_hub[h])

        # 흐름 보존
        for n in nodes:
            out_idx = [i for i, ek in enumerate(edge_keys) if ek[0] == n]
            in_idx = [i for i, ek in enumerate(edge_keys) if ek[1] == n]
            if n in hub_virtual_nodes:
                # 허브 가상 노드: 통과 흐름 보존 (in == out, 흐름 방향은 solver 자유)
                model.add(sum(x[i] for i in out_idx) == sum(x[i] for i in in_idx))
            else:
                # 내륙 도시: outflow == inflow == y[c]
                model.add(sum(x[i] for i in out_idx) == y_city[n])
                model.add(sum(x[i] for i in in_idx) == y_city[n])

        # ── 필수 방문 핀 ─────────────────────────────────────
        # required_countries 안의 허브 + 그 자식 내륙 도시 강제 방문
        # required_cities에 명시된 내륙 도시도 강제 방문 (OR)
        required_cities = set(req.required_cities) if req.required_cities else set()

        for h in required:
            if h in graph.hubs:  # 안전 가드 (잘못된 IATA 대비)
                model.add(y_hub[h] == 1)
        for c in graph.internal_cities:
            parent_hub = graph.city_to_hub.get(c)
            country_required = parent_hub and parent_hub in required
            city_required = c in required_cities
            if country_required or city_required:
                model.add(y_city[c] == 1)

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
        # active(x=1) 에지를 from_node 키 dict로 모아 공유 헬퍼에 위임.
        active_edges: dict[str, ActiveEdge] = {}
        for i in range(n_edges):
            if solver.value(x[i]) == 1:
                eu, ev, mode = edge_keys[i]
                active_edges[eu] = (eu, ev, mode, edge_cost[i], edge_time[i])

        route, visited_iata, visited_cities, total_cost, total_time = reconstruct_route(
            start_node, active_edges, graph
        )

        # ── y[d] 결정변수 노출 ───────────────────────────────
        self._last_y_values = {
            **{c: int(solver.value(y_city[c])) for c in graph.internal_cities},
            **{h: int(solver.value(y_hub[h])) for h in graph.hubs},
        }

        # 체류시간 추가 (deadline 제약과 의미 일치)
        total_time += stay_time_minutes(self._last_y_values, req.stay_days)

        return OptimizeResult(
            status=status,
            route=route,
            total_cost_won=total_cost,
            total_time_minutes=total_time,
            objective_value=float(solver.objective_value) / _OBJ_SCALE,
            solve_time_ms=solve_ms,
            solver="ortools",
            visited_iata=visited_iata,
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
