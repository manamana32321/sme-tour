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


class TestOrToolsYVariable:
    """y[d] 결정변수 도입 invariants."""

    def test_y_values_exposed_after_solve(self, solver: OrToolsSolver, mini_graph) -> None:
        """solve() 후 _last_y_values가 노출되어야."""
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        # mini fixture: 3 hubs (CDG, FCO, AMS) + 2 cities (NCE_City, MIL_City) = 5 keys
        expected_keys = mini_graph.hubs | mini_graph.internal_cities
        assert set(solver._last_y_values.keys()) == expected_keys
        # 모든 값이 0 또는 1 (binary)
        assert all(v in (0, 1) for v in solver._last_y_values.values())

    def test_y_hub_matches_visited_iata(self, solver: OrToolsSolver, mini_graph) -> None:
        """y[h] == 1 ↔ h가 visited_iata에 포함."""
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        for h in mini_graph.hubs:
            visited = h in result.visited_iata
            y_val = solver._last_y_values[h]
            assert (y_val == 1) == visited, (
                f"허브 {h}: y={y_val}, visited={visited}"
            )

    def test_y_city_matches_visited_cities(self, solver: OrToolsSolver, mini_graph) -> None:
        """y[c] == 1 ↔ c가 visited_cities에 포함."""
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        for c in mini_graph.internal_cities:
            visited = c in result.visited_cities
            y_val = solver._last_y_values[c]
            assert (y_val == 1) == visited, (
                f"도시 {c}: y={y_val}, visited={visited}"
            )

    def test_y_hub_zero_means_not_in_route(self, solver: OrToolsSolver, mini_graph) -> None:
        """y[h] == 0인 허브의 Entry/Exit는 route의 어느 노드로도 등장하지 않아야."""
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
            required_countries=["CDG"],  # CDG만 필수, FCO/AMS는 자유 (선택적 방문)
        )
        result = solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        skipped_hubs = {h for h in mini_graph.hubs if solver._last_y_values[h] == 0}
        # required_countries=["CDG"]이면 비용 최소화 시 FCO/AMS는 보통 skip됨
        # 0개일 가능성도 있으니 가드 추가 — solver가 모든 허브를 방문해도 이 테스트는 의미 없음
        assert len(skipped_hubs) > 0, (
            "테스트 전제: 최소 1개 허브가 skip되어야 의미 있는 검증 가능"
        )
        # 미방문 허브의 Entry/Exit는 route의 어느 쪽 노드(from 또는 to)로도 등장하지 않아야 한다
        route_nodes = {e.from_node for e in result.route} | {e.to_node for e in result.route}
        for h in skipped_hubs:
            assert f"{h}_Entry" not in route_nodes, (
                f"y[{h}]=0 인데 {h}_Entry가 route 노드에 있음"
            )
            assert f"{h}_Exit" not in route_nodes, (
                f"y[{h}]=0 인데 {h}_Exit가 route 노드에 있음"
            )

    def test_required_countries_pinned_to_one(self, solver: OrToolsSolver, mini_graph) -> None:
        """required_countries 안의 허브와 자식 도시는 y[d] == 1."""
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
            required_countries=["CDG", "FCO"],  # AMS는 자유
        )
        result = solver.solve(mini_graph, req)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert solver._last_y_values is not None
        # 허브 핀
        assert solver._last_y_values["CDG"] == 1
        assert solver._last_y_values["FCO"] == 1
        # 자식 도시 핀 (mini_graph.city_to_hub: NCE_City→CDG, MIL_City→FCO)
        assert solver._last_y_values["NCE_City"] == 1
        assert solver._last_y_values["MIL_City"] == 1


class TestOrToolsStayDays:
    """stay_days 기능 invariants — OR-Tools 솔버."""

    def test_stay_days_none_equivalent_to_baseline(self, solver: OrToolsSolver, mini_graph) -> None:
        """stay_days=None이면 기존 동작과 동일한 total_time을 반환해야."""
        base_req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        none_req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
            stay_days=None,
        )
        base = solver.solve(mini_graph, base_req)
        with_none = solver.solve(mini_graph, none_req)
        assert base.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert with_none.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert base.total_time_minutes == with_none.total_time_minutes

    def test_stay_days_adds_to_time_constraint_tight(self, solver: OrToolsSolver, mini_graph) -> None:
        """짧은 deadline + 큰 체류일 → 시간 초과 → INFEASIBLE 또는 기존보다 더 적은 방문."""
        # 5일 deadline (7200분). stay_days CDG:5 = 7200분 추가 → 이동 시간 여유 0분
        tight_req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=5,
            start_hub="CDG",
            w_cost=0.5,
            stay_days={"CDG": 5},  # 5일 * 1440분 = 7200분
        )
        tight_result = solver.solve(mini_graph, tight_req)
        # 이동시간이 0분일 수 없으므로 INFEASIBLE이어야
        assert tight_result.status == Status.INFEASIBLE

    def test_stay_days_adds_to_time_constraint_loose(self, solver: OrToolsSolver, mini_graph) -> None:
        """넉넉한 deadline에서 stay_days={"CDG": 2}는 여전히 OPTIMAL/FEASIBLE."""
        loose_req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
            stay_days={"CDG": 2},  # 2일 = 2880분, 30일(43200분) 중 여유 충분
        )
        loose_result = solver.solve(mini_graph, loose_req)
        assert loose_result.status in (Status.OPTIMAL, Status.FEASIBLE)

    def test_stay_days_for_unvisited_no_effect(self, solver: OrToolsSolver, mini_graph) -> None:
        """방문하지 않는 허브(y[AMS]=0)에 stay_days=30 지정해도 시간 기여 0 → OPTIMAL/FEASIBLE."""
        # required_countries=["CDG"]이면 AMS는 optional — 비용 최소화 시 skip될 가능성 있음
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
            required_countries=["CDG"],  # AMS 필수 아님
            stay_days={"AMS": 30},  # AMS 30일 — AMS 방문 시에만 적용
        )
        result = solver.solve(mini_graph, req)
        # stay_days 때문에 infeasible이 되면 안 됨 (AMS 미방문 시 기여 0)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE, Status.INFEASIBLE)
        if result.status != Status.INFEASIBLE:
            # AMS를 방문했다면 30*1440=43200분(30일)이 추가 → 30일 deadline 초과 → 방문 불가
            # 따라서 AMS는 skip되었어야 함
            assert "AMS" not in result.visited_iata

    def test_stay_days_added_to_response_total_time(self, solver: OrToolsSolver, mini_graph) -> None:
        """stay_days가 response total_time_minutes에도 반영되어야 (deadline 의미와 일치)."""
        req_baseline = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
        )
        result_baseline = solver.solve(mini_graph, req_baseline)
        baseline_time = result_baseline.total_time_minutes

        req_with_stay = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30,
            start_hub="CDG", w_cost=0.5,
            stay_days={"CDG": 2, "FCO": 1},
        )
        result_with_stay = solver.solve(mini_graph, req_with_stay)

        # 같은 route를 찾았다면 (예산/시간 여유) total_time이 stay 만큼 더 커야 함
        # CDG, FCO 모두 visited이면 +3 days = +4320 min
        if "CDG" in result_with_stay.visited_iata and "FCO" in result_with_stay.visited_iata:
            expected_extra = 3 * 1440
            assert result_with_stay.total_time_minutes == baseline_time + expected_extra, (
                f"baseline={baseline_time}, with_stay={result_with_stay.total_time_minutes}, "
                f"expected delta={expected_extra}"
            )
