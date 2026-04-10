"""OR-Tools CP-SAT 기반 Clustered TSP 솔버 (Gurobi fallback).

Gurobi WLS 인증이 불가능한 환경(CI, 무료 배포 등)에서 사용하는 대안 솔버.
CP-SAT는 정수 프로그래밍 솔버이므로 Gurobi MIP 코드와 **동일한 에지 기반
모델 구조**를 그대로 사용한다.

### Gurobi 코드와의 차이
- DFJ lazy constraint callback → **MTZ subtour elimination** (정적 제약)
- float 목적함수 → **정수 스케일링** (CP-SAT는 integer only)
- Gurobi Env/WLS 불필요

### 성능
- 60노드 규모에서 MTZ는 O(n²) 추가 변수/제약. CP-SAT가 수 초 안에 해결 예상.
- GLS(Guided Local Search) 등의 메타 휴리스틱이 아닌, 정확한 MIP solver.
"""

from __future__ import annotations

import time as time_mod

from ortools.sat.python import cp_model

from ..graph import Graph
from ..models import OptimizeRequest, OptimizeResult, RouteEdge, Status
from .base import BaseSolver

# CP-SAT는 정수만 다루므로 float 비용을 정수로 스케일링
_OBJ_SCALE = 10_000


class OrToolsSolver(BaseSolver):
    """OR-Tools CP-SAT 기반 에지 MIP + MTZ subtour elimination."""

    name = "ortools"

    def __init__(self) -> None:
        """OR-Tools는 라이센스가 불필요."""

    def solve(self, graph: Graph, req: OptimizeRequest) -> OptimizeResult:
        start = time_mod.perf_counter()

        # ── Graph.edges → edge dict (Gurobi 코드와 동일 구조) ──
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
        n_nodes = len(nodes)

        # ── CP-SAT 모델 ─────────────────────────────────────
        model = cp_model.CpModel()

        # 결정 변수: x_e ∈ {0,1}
        x = [model.new_bool_var(f"x_{i}") for i in range(n_edges)]

        # ── 예산 제약 (정수 스케일링) ────────────────────────
        model.add(
            sum(int(edge_cost[i] * _OBJ_SCALE) * x[i] for i in range(n_edges))
            <= int(budget_scaled * _OBJ_SCALE)
        )

        # ── 시간 제약 ───────────────────────────────────────
        model.add(
            sum(edge_time[i] * x[i] for i in range(n_edges))
            <= deadline
        )

        # ── 흐름 보존 제약 ──────────────────────────────────
        for n in nodes:
            out_indices = [i for i, ek in enumerate(edge_keys) if ek[0] == n]
            in_indices = [i for i, ek in enumerate(edge_keys) if ek[1] == n]

            if "_Entry" in n or "_Exit" in n:
                # 허브 노드: in-flow = out-flow
                model.add(sum(x[i] for i in out_indices) == sum(x[i] for i in in_indices))
            else:
                # 내륙 도시: 정확히 1회 방문
                model.add(sum(x[i] for i in out_indices) == 1)
                model.add(sum(x[i] for i in in_indices) == 1)

        # ── 출발지 제약 ─────────────────────────────────────
        start_node = f"{req.start_hub}_Entry"
        start_out = [i for i, ek in enumerate(edge_keys) if ek[0] == start_node]
        model.add(sum(x[i] for i in start_out) == 1)

        # ── MTZ Subtour Elimination ──────────────────────────
        # u[n] = 방문 순서 (0 ~ n_nodes-1). start_node = 0 고정.
        node_to_idx = {n: i for i, n in enumerate(nodes)}
        u = [model.new_int_var(0, n_nodes - 1, f"u_{n}") for n in nodes]

        start_idx = node_to_idx.get(start_node, 0)
        model.add(u[start_idx] == 0)

        for ei in range(n_edges):
            eu, ev, _ = edge_keys[ei]
            ui = node_to_idx.get(eu)
            vi = node_to_idx.get(ev)
            if ui is None or vi is None:
                continue
            if vi == start_idx:
                continue  # 돌아가는 에지(→start)는 MTZ 적용 안 함 (u[start]=0 고정이라 모순 발생)
            # u[eu] - u[ev] + n_nodes * x_e <= n_nodes - 1
            model.add(u[ui] - u[vi] + n_nodes * x[ei] <= n_nodes - 1)

        # ── 목적 함수 (정수 스케일링) ────────────────────────
        obj_terms = []
        for i in range(n_edges):
            cost_term = int(edge_cost[i] / budget_scaled * req.w_cost * _OBJ_SCALE) if budget_scaled > 0 else 0
            time_term = int(edge_time[i] / deadline * req.w_time * _OBJ_SCALE) if deadline > 0 else 0
            obj_terms.append((cost_term + time_term) * x[i])
        model.minimize(sum(obj_terms))

        # ── Solve ────────────────────────────────────────────
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30

        cp_status = solver.solve(model)
        solve_ms = int((time_mod.perf_counter() - start) * 1000)

        # ── 상태 판별 ───────────────────────────────────────
        if cp_status == cp_model.OPTIMAL:
            status = Status.OPTIMAL
        elif cp_status == cp_model.FEASIBLE:
            status = Status.FEASIBLE
        elif cp_status == cp_model.INFEASIBLE:
            return self._empty_result(Status.INFEASIBLE, solve_ms)
        else:
            return self._empty_result(Status.TIMEOUT, solve_ms)

        # ── 경로 재구성 (start_node부터 체인 순회) ──────────
        # x[ei] == 1 인 에지를 순서대로 추출
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

            route.append(
                RouteEdge(
                    from_node=eu,
                    to_node=ev,
                    mode=mode,
                    category=category,
                    cost_won=cost_won,
                    time_minutes=time_m,
                )
            )
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
            status=status,
            route=[],
            total_cost_won=0,
            total_time_minutes=0,
            objective_value=0.0,
            solve_time_ms=solve_ms,
            solver="ortools",
            visited_iata=[],
            visited_cities=[],
            engine_version=self._version(),
        )

    @staticmethod
    def _version() -> str:
        from src import __version__

        return f"sme-tour-engine {__version__} (ortools)"
