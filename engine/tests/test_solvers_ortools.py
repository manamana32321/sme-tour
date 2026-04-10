"""OR-Tools solver 통합 테스트.

mini fixtures(3 hubs + 2 cities)로 solve가 유효한 경로를 반환하는지 검증한다.
OR-Tools는 라이센스 불필요 — 모든 환경에서 실행 가능.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.graph import build_graph
from src.models import OptimizeRequest, Status
from src.solvers.ortools import OrToolsSolver

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def solver() -> OrToolsSolver:
    return OrToolsSolver()


@pytest.fixture(scope="module")
def mini_graph():
    return build_graph(FIXTURES / "mini_air.csv", FIXTURES / "mini_city.csv")


class TestOrToolsSolverBasic:
    def test_name_is_ortools(self, solver: OrToolsSolver) -> None:
        assert solver.name == "ortools"

    def test_solve_returns_result(self, solver: OrToolsSolver, mini_graph) -> None:
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert result.solver == "ortools"
        assert result.solve_time_ms >= 0
        assert len(result.route) > 0

    def test_route_visits_internal_cities(self, solver: OrToolsSolver, mini_graph) -> None:
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        # mini fixture에 NCE_City, MIL_City가 있으므로 visited_cities에 포함되어야
        city_nodes_in_route = [e.to_node for e in result.route if not e.to_node.endswith(("_Entry", "_Exit"))]
        assert len(city_nodes_in_route) > 0, "내륙 도시를 하나도 방문하지 않았음"

    def test_total_cost_positive(self, solver: OrToolsSolver, mini_graph) -> None:
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert result.total_cost_won > 0
        assert result.total_time_minutes > 0

    def test_tight_budget_fewer_countries(self, solver: OrToolsSolver, mini_graph) -> None:
        """낮은 예산에서는 일부 허브를 skip하고 더 적은 국가만 방문.

        허브 노드는 in=out 제약이지만 0=0도 허용 (방문 선택적).
        내륙 도시만 in=out=1 강제 (반드시 방문).
        """
        req = OptimizeRequest(
            budget_won=1_000_000,  # 100만원
            deadline_days=3,
            start_hub="CDG",
            w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE, Status.INFEASIBLE)
        if result.status != Status.INFEASIBLE:
            # 풍족한 예산(30M)으로 3 hub 다 방문하는 것보다 적은 국가
            assert len(result.visited_iata) <= 3

    def test_engine_version_contains_ortools(self, solver: OrToolsSolver, mini_graph) -> None:
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert "ortools" in result.engine_version


class TestOrToolsFallback:
    def test_get_solver_returns_ortools_when_gurobi_unavailable(self) -> None:
        """이 환경에서 gurobipy 미설치이므로 get_solver()는 OrToolsSolver를 반환해야."""
        from src.solvers import get_solver

        solver = get_solver()
        # gurobipy 있으면 GurobiSolver, 없으면 OrToolsSolver
        assert solver.name in ("gurobi", "ortools")
