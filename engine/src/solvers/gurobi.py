"""Gurobi 기반 Clustered TSP 솔버.

w7 주간보고서의 수리 모형 코드를 ``BaseSolver`` 인터페이스로 이식한 것이다.
원본 코드 작성자: 종설 5조 모델링 담당 팀원.

### 변경 사항 (w7 → GurobiSolver)
- CSV 로드/그래프 빌드 분리 → ``graph.py`` 가 담당, 여기선 ``Graph`` 수신만
- 하드코딩 파라미터(BUDGET/DEADLINE/가중치/출발지) → ``OptimizeRequest`` 에서 수신
- print 기반 출력 → ``OptimizeResult`` 데이터 반환
- Gurobi Env를 WLS 환경변수로 초기화 (``__init__``)
- ``TimeLimit = 30`` 하드 캡 추가 (FastAPI hang 방지)
- ``OutputFlag = 0`` (콘솔 출력 억제)

### 수학적 모형 (불변)
- 결정 변수: ``x_{ijm}`` ∈ {0,1} (에지 (i,j) 를 수단 m 으로 이동 여부)
- 목적 함수: ``min W_cost·(Σcost·x / Budget) + W_time·(Σtime·x / Deadline)``
- 흐름 보존: hub 노드는 in=out, 내륙 도시는 정확히 1회 방문
- DFJ Subtour Elimination: lazy constraint callback (Branch and Cut)
"""

from __future__ import annotations

import os
import time as time_mod
from typing import TYPE_CHECKING

import networkx as nx

from ..graph import Graph
from ..models import OptimizeRequest, OptimizeResult, RouteEdge, Status
from .base import BaseSolver, SolverInitializationError

if TYPE_CHECKING:
    pass

# Gurobi는 top-level import — gurobipy 미설치 시 이 파일을 import하면 ImportError.
# solvers/__init__.py의 lazy import가 이를 보호한다.
import gurobipy as gp
from gurobipy import GRB


class GurobiSolver(BaseSolver):
    """Gurobi MIP 솔버로 Clustered TSP를 풀어 최적 경로를 반환한다."""

    name = "gurobi"

    def __init__(self) -> None:
        """WLS 환경변수로 Gurobi Env를 초기화한다.

        필요한 환경변수:
        - ``GUROBI_LICENSE_ID``
        - ``GUROBI_WLS_ACCESS_ID``
        - ``GUROBI_WLS_SECRET``

        Raises:
            SolverInitializationError: 환경변수 누락 또는 WLS 인증 실패.
        """
        self._last_y_values: dict[str, int] | None = None
        try:
            self._env = gp.Env(empty=True)
            self._env.setParam("LicenseID", os.environ["GUROBI_LICENSE_ID"])
            self._env.setParam("WLSAccessID", os.environ["GUROBI_WLS_ACCESS_ID"])
            self._env.setParam("WLSSecret", os.environ["GUROBI_WLS_SECRET"])
            self._env.start()
        except KeyError as e:
            raise SolverInitializationError(
                f"Gurobi WLS 환경변수 누락: {e}. "
                "GUROBI_LICENSE_ID, GUROBI_WLS_ACCESS_ID, GUROBI_WLS_SECRET 세 개가 모두 필요합니다."
            ) from e
        except gp.GurobiError as e:
            raise SolverInitializationError(
                f"Gurobi WLS 인증 실패: {e}. 라이센스 값을 확인해주세요."
            ) from e

    def solve(self, graph: Graph, req: OptimizeRequest) -> OptimizeResult:
        """그래프와 사용자 제약으로 Clustered TSP 최적해를 찾는다."""
        start = time_mod.perf_counter()
        self._last_y_values = None

        # Graph.edges → Gurobi addVars 호환 dict
        edge_dict: dict[tuple[str, str, str], dict[str, float]] = {
            (e.u, e.v, e.mode): {"cost": e.cost_scaled, "time": float(e.time_minutes)}
            for e in graph.edges
        }

        budget_scaled = req.budget_won / graph.scale_factor
        deadline = req.deadline_minutes

        m = gp.Model("SME_Tour", env=self._env)
        try:
            return self._solve_model(m, edge_dict, graph, req, budget_scaled, deadline, start)
        finally:
            m.dispose()

    def _solve_model(
        self,
        m: gp.Model,
        edge_dict: dict[tuple[str, str, str], dict[str, float]],
        graph: Graph,
        req: OptimizeRequest,
        budget_scaled: float,
        deadline: int,
        start: float,
    ) -> OptimizeResult:
        # ── 솔버 파라미터 ────────────────────────────────────
        m.Params.LazyConstraints = 1
        m.Params.NumericFocus = 3
        m.Params.TimeLimit = 30
        m.Params.OutputFlag = 0  # 콘솔 출력 억제 (FastAPI 환경)

        # ── 결정 변수 ────────────────────────────────────────
        x = m.addVars(edge_dict.keys(), vtype=GRB.BINARY, name="x")

        # ── y[d] 도시 방문 결정변수 ──────────────────────────
        y_city = m.addVars(graph.internal_cities, vtype=GRB.BINARY, name="y_city")
        y_hub = m.addVars(graph.hubs, vtype=GRB.BINARY, name="y_hub")

        # 허브 가상 노드 집합 (substring 매치보다 안전)
        hub_virtual_nodes = {f"{h}_Entry" for h in graph.hubs} | {f"{h}_Exit" for h in graph.hubs}

        # 허브 방문 = h_Entry로부터의 어떤 outflow든 1번 발생 (Hub_Stay 또는 Ground out)
        # TSP 흐름 보존으로 h_Entry outflow 합은 0 또는 1 (방문 여부와 일치)
        # 시작 허브는 start_out == 1로 인해 자동으로 y_hub == 1
        for h in graph.hubs:
            entry_out_edges = [e for e in edge_dict if e[0] == f"{h}_Entry"]
            if not entry_out_edges:
                raise ValueError(
                    f"허브 {h}에 h_Entry outflow 에지가 없음 — 그래프 구조 이상"
                )
            m.addConstr(gp.quicksum(x[e] for e in entry_out_edges) == y_hub[h])

        # ── 예산 제약 ────────────────────────────────────────
        m.addConstr(gp.quicksum(edge_dict[e]["cost"] * x[e] for e in edge_dict) <= budget_scaled)

        # 시간 제약 (이동시간 + 체류시간)
        # stay_days[d] * 1440 (분/일) * y[d] (방문 여부)를 합산
        stay_days = req.stay_days or {}
        m.addConstr(
            gp.quicksum(edge_dict[e]["time"] * x[e] for e in edge_dict)
            + gp.quicksum(
                stay_days.get(d, 0) * 1440 * y_city[d] for d in graph.internal_cities
            )
            + gp.quicksum(
                stay_days.get(h, 0) * 1440 * y_hub[h] for h in graph.hubs
            )
            <= deadline
        )

        # ── 목적 함수 ───────────────────────────────────────
        m.setObjective(
            gp.quicksum(edge_dict[e]["cost"] * x[e] for e in edge_dict) / budget_scaled * req.w_cost
            + gp.quicksum(edge_dict[e]["time"] * x[e] for e in edge_dict) / deadline * req.w_time,
            GRB.MINIMIZE,
        )

        # ── 흐름 보존 제약 ──────────────────────────────────
        required = set(req.required_countries) if req.required_countries else graph.hubs

        for n in graph.virtual_nodes:
            if n in hub_virtual_nodes:
                # 허브 가상 노드: 통과 흐름 보존 (in == out, 흐름 방향은 solver 자유)
                m.addConstr(
                    gp.quicksum(x[e] for e in edge_dict if e[0] == n)
                    == gp.quicksum(x[e] for e in edge_dict if e[1] == n)
                )
            else:
                # 내륙 도시: outflow == inflow == y[c]
                m.addConstr(gp.quicksum(x[e] for e in edge_dict if e[0] == n) == y_city[n])
                m.addConstr(gp.quicksum(x[e] for e in edge_dict if e[1] == n) == y_city[n])

        # ── 필수 방문 핀 ─────────────────────────────────────
        # required_countries 안의 허브 자체와 그 자식 내륙 도시 모두 강제 방문
        for h in required:
            if h in graph.hubs:  # 안전 가드 (잘못된 IATA 대비)
                m.addConstr(y_hub[h] == 1)
        for c in graph.internal_cities:
            hub = graph.city_to_hub.get(c)
            if hub and hub in required:
                m.addConstr(y_city[c] == 1)

        # ── 출발지 제약 ─────────────────────────────────────
        start_node = f"{req.start_hub}_Entry"
        m.addConstr(gp.quicksum(x[e] for e in edge_dict if e[0] == start_node) == 1)

        # ── DFJ Subtour Elimination (lazy callback) ──────────
        all_nodes = graph.virtual_nodes

        def subtourelim(model: gp.Model, where: int) -> None:
            if where != GRB.Callback.MIPSOL:
                return
            vals = model.cbGetSolution(model._vars)
            directed = nx.DiGraph()
            directed.add_edges_from(
                [(e[0], e[1]) for e in model._vars if vals[e] > 0.5]
            )
            components = list(nx.strongly_connected_components(directed))
            if len(components) <= 1:
                return
            for comp in components:
                if len(comp) < len(all_nodes):
                    model.cbLazy(
                        gp.quicksum(
                            model._vars[e]
                            for e in model._vars
                            if e[0] in comp and e[1] not in comp
                        )
                        >= 1
                    )

        m._vars = x
        m.optimize(subtourelim)

        solve_ms = int((time_mod.perf_counter() - start) * 1000)

        # ── 상태 판별 ───────────────────────────────────────
        if m.status == GRB.OPTIMAL:
            status = Status.OPTIMAL
        elif m.status == GRB.TIME_LIMIT and m.SolCount > 0:
            status = Status.FEASIBLE
        elif m.status == GRB.TIME_LIMIT:
            return self._empty_result(Status.TIMEOUT, solve_ms)
        elif m.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
            return self._empty_result(Status.INFEASIBLE, solve_ms)
        elif m.SolCount > 0:
            status = Status.FEASIBLE
        else:
            return self._empty_result(Status.INFEASIBLE, solve_ms)

        # ── 경로 재구성 (start_node부터 체인 순회) ──────────
        route: list[RouteEdge] = []
        visited_iata: set[str] = set()
        visited_cities: list[str] = []
        total_cost = 0
        total_time = 0

        curr = start_node
        for _ in range(len(edge_dict)):
            found = False
            for key in edge_dict:
                i, j, mode = key
                if i == curr and x[key].X > 0.5:
                    data = edge_dict[key]
                    cost_won = int(data["cost"] * graph.scale_factor)
                    time_min = int(data["time"])

                    if mode == "Hub_Stay":
                        category = "hub_stay"
                    elif mode.startswith("Air_"):
                        category = "air"
                    else:
                        category = "ground"

                    route.append(
                        RouteEdge(
                            from_node=i,
                            to_node=j,
                            mode=mode,
                            category=category,
                            cost_won=cost_won,
                            time_minutes=time_min,
                        )
                    )

                    total_cost += cost_won
                    total_time += time_min

                    # IATA / city 추적
                    for node in (i, j):
                        if node.endswith("_Entry") or node.endswith("_Exit"):
                            visited_iata.add(node.rsplit("_", 1)[0])
                        elif node not in visited_cities:
                            visited_cities.append(node)

                    curr = j
                    found = True
                    break

            if not found or curr == start_node:
                break

        # ── y[d] 결정변수 노출 ───────────────────────────────
        self._last_y_values = {
            **{c: int(round(y_city[c].X)) for c in graph.internal_cities},
            **{h: int(round(y_hub[h].X)) for h in graph.hubs},
        }

        return OptimizeResult(
            status=status,
            route=route,
            total_cost_won=total_cost,
            total_time_minutes=total_time,
            objective_value=float(m.ObjVal),
            solve_time_ms=solve_ms,
            solver="gurobi",
            visited_iata=sorted(visited_iata),
            visited_cities=visited_cities,
            engine_version=self._version(),
        )

    def _empty_result(self, status: Status, solve_ms: int) -> OptimizeResult:
        """infeasible / timeout 시 빈 결과 생성."""
        return OptimizeResult(
            status=status,
            route=[],
            total_cost_won=0,
            total_time_minutes=0,
            objective_value=0.0,
            solve_time_ms=solve_ms,
            solver="gurobi",
            visited_iata=[],
            visited_cities=[],
            engine_version=self._version(),
        )

    @staticmethod
    def _version() -> str:
        from src import __version__

        return f"sme-tour-engine {__version__}"
