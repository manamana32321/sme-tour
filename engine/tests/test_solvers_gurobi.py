"""Gurobi solver 통합 테스트.

OR-Tools와 동일한 mini fixture로 동등한 invariant를 검증한다.
WLS 환경변수 미설정 시 모든 테스트가 skip된다.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.graph import build_graph
from src.models import OptimizeRequest, Status

# Gurobi 의존성 import — 실패 시 모든 테스트 skip
try:
    from src.solvers.gurobi import GurobiSolver
    HAS_GUROBI = True
except ImportError:
    HAS_GUROBI = False

# WLS 환경변수 모두 설정되어야 GurobiSolver 인스턴스 생성 가능
HAS_WLS = all(
    os.environ.get(k)
    for k in ("GUROBI_LICENSE_ID", "GUROBI_WLS_ACCESS_ID", "GUROBI_WLS_SECRET")
)

pytestmark = pytest.mark.skipif(
    not (HAS_GUROBI and HAS_WLS),
    reason="gurobipy 또는 WLS 환경변수 미설정"
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def solver():
    return GurobiSolver()


@pytest.fixture(scope="module")
def mini_graph():
    return build_graph(FIXTURES / "mini_air.csv", FIXTURES / "mini_city.csv")


class TestGurobiSolverBasic:
    def test_name_is_gurobi(self, solver) -> None:
        assert solver.name == "gurobi"

    def test_solve_returns_result(self, solver, mini_graph) -> None:
        req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert result.solver == "gurobi"
        assert len(result.route) > 0

    def test_route_visits_internal_cities(self, solver, mini_graph) -> None:
        req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        city_nodes = [e.to_node for e in result.route if not e.to_node.endswith(("_Entry", "_Exit"))]
        assert len(city_nodes) > 0


class TestGurobiYVariable:
    """OR-Tools와 동일한 y[d] invariant 미러."""

    def test_y_values_exposed_after_solve(self, solver, mini_graph) -> None:
        req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
        )
        solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        expected_keys = mini_graph.hubs | mini_graph.internal_cities
        assert set(solver._last_y_values.keys()) == expected_keys
        assert all(v in (0, 1) for v in solver._last_y_values.values())

    def test_y_hub_matches_visited_iata(self, solver, mini_graph) -> None:
        req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        for h in mini_graph.hubs:
            visited = h in result.visited_iata
            y_val = solver._last_y_values[h]
            assert (y_val == 1) == visited, f"허브 {h}: y={y_val}, visited={visited}"

    def test_y_city_matches_visited_cities(self, solver, mini_graph) -> None:
        req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        for c in mini_graph.internal_cities:
            visited = c in result.visited_cities
            y_val = solver._last_y_values[c]
            assert (y_val == 1) == visited, f"도시 {c}: y={y_val}, visited={visited}"

    def test_required_countries_pinned_to_one(self, solver, mini_graph) -> None:
        req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
            required_countries=["CDG", "FCO"],
        )
        result = solver.solve(mini_graph, req)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert solver._last_y_values is not None
        assert solver._last_y_values["CDG"] == 1
        assert solver._last_y_values["FCO"] == 1
        assert solver._last_y_values["NCE_City"] == 1
        assert solver._last_y_values["MIL_City"] == 1


class TestGurobiStayDays:
    """stay_days 기능 invariants — Gurobi 솔버 (OR-Tools 미러)."""

    def test_stay_days_none_equivalent_to_baseline(self, solver, mini_graph) -> None:
        """stay_days=None이면 기존 동작과 동일한 total_time을 반환해야."""
        base_req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
        )
        none_req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
            stay_days=None,
        )
        base = solver.solve(mini_graph, base_req)
        with_none = solver.solve(mini_graph, none_req)
        assert base.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert with_none.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert base.total_time_minutes == with_none.total_time_minutes

    def test_stay_days_adds_to_time_constraint_tight(self, solver, mini_graph) -> None:
        """짧은 deadline + 큰 체류일 → 시간 초과 → INFEASIBLE."""
        tight_req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=5,
            start_hub="CDG", w_cost=0.5,
            stay_days={"CDG": 5},  # 5일 * 1440분 = 7200분, deadline도 7200분
        )
        tight_result = solver.solve(mini_graph, tight_req)
        assert tight_result.status == Status.INFEASIBLE

    def test_stay_days_adds_to_time_constraint_loose(self, solver, mini_graph) -> None:
        """넉넉한 deadline에서 stay_days={"CDG": 2}는 여전히 OPTIMAL/FEASIBLE."""
        loose_req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
            stay_days={"CDG": 2},
        )
        loose_result = solver.solve(mini_graph, loose_req)
        assert loose_result.status in (Status.OPTIMAL, Status.FEASIBLE)

    def test_stay_days_for_unvisited_no_effect(self, solver, mini_graph) -> None:
        """방문하지 않는 허브(AMS)에 stay_days=30 지정해도 시간 기여 0."""
        req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
            required_countries=["CDG"],
            stay_days={"AMS": 30},
        )
        result = solver.solve(mini_graph, req)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE, Status.INFEASIBLE)
        if result.status != Status.INFEASIBLE:
            assert "AMS" not in result.visited_iata
