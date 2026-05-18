"""원 조건 infeasible 시 자동 완화 대안 탐색 (``find_alternative``) 테스트.

전략 1·2는 OR-Tools 솔버 + mini fixture로 결정론적 통합 테스트, 전략 3·4 와
헬퍼 함수는 모의 ``solve_once`` 로 유닛 테스트.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.graph import Graph, build_graph
from src.models import Alternative, OptimizeRequest, OptimizeResult, Status
from src.solvers._alternative import (
    _build_alternative,
    _reduce_selection,
    _user_selected,
    find_alternative,
)
from src.solvers.ortools import OrToolsSolver

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def solver() -> OrToolsSolver:
    return OrToolsSolver()


@pytest.fixture(scope="module")
def mini_graph():
    return build_graph(FIXTURES / "mini_air.csv", FIXTURES / "mini_city.csv")


class TestSolveWithAlternative:
    """공개 ``solve()`` 진입점의 자동 완화 wrapper 동작."""

    def test_no_alternative_when_feasible(
        self, solver: OrToolsSolver, mini_graph: Graph
    ) -> None:
        """원 조건으로 풀리면 ``alternative`` 는 None."""
        req = OptimizeRequest(
            budget_won=30_000_000, deadline_days=30, start_hub="CDG", w_cost=0.5
        )
        result = solver.solve(mini_graph, req)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert result.alternative is None

    def test_budget_increase_alternative_fires(
        self, solver: OrToolsSolver, mini_graph: Graph
    ) -> None:
        """타이트한 예산 + 전체 허브 강제 → 예산 증가 전략으로 풀린다."""
        # mini fixture 전체 허브 방문 최소 ~1.12M (test_solvers_ortools.py 주석 참조).
        # 1.0M으로 원 조건은 infeasible, 1.5배=1.5M 또는 2.0배=2.0M에서 풀려야 함.
        req = OptimizeRequest(
            budget_won=1_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
            required_countries=None,  # 전체 허브 강제
        )
        result = solver.solve(mini_graph, req)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert result.alternative is not None
        assert result.alternative.type == "예산 증가"
        assert result.alternative.applied_budget_won > req.budget_won
        # 적용된 다른 필드는 원본과 동일해야
        assert result.alternative.applied_deadline_days == req.deadline_days
        assert result.alternative.applied_required_countries is None


class TestFindAlternativeWithMock:
    """``solve_once`` 모의로 전략 3·4 및 종료 조건 결정론적 검증."""

    def _make_req(self, **overrides) -> OptimizeRequest:
        base = dict(
            budget_won=10_000_000, deadline_days=14, start_hub="CDG", w_cost=0.5
        )
        base.update(overrides)
        return OptimizeRequest(**base)

    def _make_feasible_result(self) -> OptimizeResult:
        return OptimizeResult(
            status=Status.OPTIMAL,
            route=[],
            total_cost_won=0,
            total_time_minutes=0,
            objective_value=0.0,
            solve_time_ms=0,
            solver="ortools",
            visited_iata=[],
            visited_cities=[],
            engine_version="test",
        )

    def _make_infeasible_result(self) -> OptimizeResult:
        return OptimizeResult(
            status=Status.INFEASIBLE,
            route=[],
            total_cost_won=0,
            total_time_minutes=0,
            objective_value=0.0,
            solve_time_ms=0,
            solver="ortools",
            visited_iata=[],
            visited_cities=[],
            engine_version="test",
        )

    def _stub_graph(self) -> Graph:
        """find_alternative는 graph 객체를 그대로 통과만 시키므로 dummy로 충분."""
        return build_graph(FIXTURES / "mini_air.csv", FIXTURES / "mini_city.csv")

    def test_returns_none_when_all_strategies_fail(self) -> None:
        """모의 솔버가 항상 infeasible을 반환하면 ``find_alternative`` 도 None."""
        req = self._make_req(required_countries=["CDG", "FCO"])

        def solve_once(_g: Graph, _r: OptimizeRequest) -> OptimizeResult:
            return self._make_infeasible_result()

        assert find_alternative(self._stub_graph(), req, solve_once) is None

    def test_city_removal_strategy_picks_smallest_removal(self) -> None:
        """전략 3은 ``remove_count=1`` 부터 시작 — 작은 제외부터 점진 탐색."""
        # required_countries=[CDG,FCO,AMS]. 전략 1/2은 무조건 infeasible로 막고,
        # 전략 3에서 "CDG 1개만 제외" 시점에 feasible 반환.
        req = self._make_req(required_countries=["CDG", "FCO", "AMS"])

        def solve_once(_g: Graph, r: OptimizeRequest) -> OptimizeResult:
            # 원 조건과 동일한 예산·기간(전략 1·2)은 항상 infeasible로 강제
            if (
                r.budget_won != req.budget_won
                or r.deadline_days != req.deadline_days
            ):
                # 전략 1·2가 시도되어도 무조건 infeasible
                return self._make_infeasible_result()
            # 전략 3 (도시 제외) — required_countries가 줄어들면 feasible
            if r.required_countries is not None and len(r.required_countries) < 3:
                return self._make_feasible_result()
            return self._make_infeasible_result()

        finding = find_alternative(self._stub_graph(), req, solve_once)
        assert finding is not None
        alt, _ = finding
        assert alt.type.startswith("선택 도시 일부 제외")
        # 가장 적은 제외 = 1개 제외부터 시도하므로 applied는 2개 남아 있어야
        assert alt.applied_required_countries is not None
        assert len(alt.applied_required_countries) == 2


class TestHelpers:
    """``_user_selected`` / ``_reduce_selection`` 단위 검증."""

    def test_user_selected_combines_countries_and_cities(self) -> None:
        req = OptimizeRequest(
            budget_won=10_000_000,
            deadline_days=14,
            start_hub="CDG",
            w_cost=0.5,
            required_countries=["CDG", "FCO"],
            required_cities=["NCE_City"],
        )
        assert _user_selected(req) == ["CDG", "FCO", "NCE_City"]

    def test_user_selected_empty_when_both_none(self) -> None:
        req = OptimizeRequest(
            budget_won=10_000_000, deadline_days=14, start_hub="CDG", w_cost=0.5
        )
        assert _user_selected(req) == []

    def test_reduce_selection_removes_from_all_fields(self) -> None:
        req = OptimizeRequest(
            budget_won=10_000_000,
            deadline_days=14,
            start_hub="CDG",
            w_cost=0.5,
            required_countries=["CDG", "FCO", "AMS"],
            required_cities=["NCE_City", "MIL_City"],
            stay_days={"CDG": 2, "NCE_City": 1, "MIL_City": 1},
        )
        reduced = _reduce_selection(req, {"CDG", "MIL_City"})
        assert reduced.required_countries == ["FCO", "AMS"]
        assert reduced.required_cities == ["NCE_City"]
        assert reduced.stay_days == {"NCE_City": 1}
        # 원본은 불변
        assert "CDG" in (req.required_countries or [])

    def test_reduce_selection_preserves_none(self) -> None:
        """None 필드(full mode 등)는 그대로 None 유지 — 의미 보존."""
        req = OptimizeRequest(
            budget_won=10_000_000,
            deadline_days=14,
            start_hub="CDG",
            w_cost=0.5,
            required_countries=None,
            required_cities=None,
            stay_days=None,
        )
        reduced = _reduce_selection(req, {"anything"})
        assert reduced.required_countries is None
        assert reduced.required_cities is None
        assert reduced.stay_days is None

    def test_build_alternative_mirrors_applied_request(self) -> None:
        applied = OptimizeRequest(
            budget_won=11_000_000,
            deadline_days=14,
            start_hub="CDG",
            w_cost=0.5,
            required_countries=["CDG"],
        )
        alt: Alternative = _build_alternative(applied, "예산 증가")
        assert alt.type == "예산 증가"
        assert alt.applied_budget_won == 11_000_000
        assert alt.applied_deadline_days == 14
        assert alt.applied_required_countries == ["CDG"]
        assert alt.applied_required_cities is None
        assert alt.applied_stay_days is None
