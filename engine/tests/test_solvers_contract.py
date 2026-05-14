"""솔버 간 계약 테스트 (Gurobi ↔ OR-Tools).

두 솔버는 동일한 수리 모델을 서로 다른 백엔드 API로 구현한다. 제약 빌드
코드가 각 파일에 복붙돼 있어 drift 위험이 있으므로, 동일 입력에 대해
**동치성**을 CI가 강제한다.

검증 불변식:
1. 같은 시나리오에서 둘 다 해를 찾는다 (feasibility 일치).
2. 두 솔버 모두 하드 제약을 지킨다 — 예산, deadline, required 핀.
3. canonical 목적값이 허용오차 내 일치한다.

OR-Tools(CP-SAT)는 정수 전용이라 목적/예산 계수를 ``_OBJ_SCALE`` 로
스케일 후 ``int()`` 절삭한다. 이 절삭 오차 때문에 두 솔버가 미세하게 다른
최적해를 낼 수 있어 목적값 비교는 상대 허용오차를 둔다.

WLS 환경변수 미설정 시 전체 skip.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.graph import build_graph
from src.models import OptimizeRequest, OptimizeResult, Status
from src.solvers.ortools import OrToolsSolver

try:
    from src.solvers.gurobi import GurobiSolver

    HAS_GUROBI = True
except ImportError:
    HAS_GUROBI = False

HAS_WLS = all(
    os.environ.get(k)
    for k in ("GUROBI_LICENSE_ID", "GUROBI_WLS_ACCESS_ID", "GUROBI_WLS_SECRET")
)

pytestmark = pytest.mark.skipif(
    not (HAS_GUROBI and HAS_WLS),
    reason="gurobipy 또는 WLS 환경변수 미설정 — 계약 테스트는 두 솔버 모두 필요",
)

FIXTURES = Path(__file__).parent / "fixtures"

# CP-SAT 정수 절삭 오차를 감안한 목적값 상대 허용오차.
_OBJECTIVE_REL_TOL = 0.05

# (id, request) — 두 솔버에 동일하게 투입할 시나리오 매트릭스.
_SCENARIOS: list[tuple[str, OptimizeRequest]] = [
    (
        "baseline",
        OptimizeRequest(
            budget_won=30_000_000, deadline_days=30, start_hub="CDG", w_cost=0.5
        ),
    ),
    (
        "cost_weighted",
        OptimizeRequest(
            budget_won=30_000_000, deadline_days=30, start_hub="CDG", w_cost=0.9
        ),
    ),
    (
        "time_weighted",
        OptimizeRequest(
            budget_won=30_000_000, deadline_days=30, start_hub="CDG", w_cost=0.1
        ),
    ),
    (
        "required_countries",
        OptimizeRequest(
            budget_won=30_000_000, deadline_days=30, start_hub="CDG", w_cost=0.5,
            required_countries=["CDG", "FCO"],
        ),
    ),
    (
        "required_cities",
        OptimizeRequest(
            budget_won=30_000_000, deadline_days=30, start_hub="CDG", w_cost=0.5,
            required_countries=["CDG"], required_cities=["MIL_City"],
        ),
    ),
    (
        "stay_days",
        OptimizeRequest(
            budget_won=30_000_000, deadline_days=30, start_hub="CDG", w_cost=0.5,
            stay_days={"CDG": 2, "FCO": 1},
        ),
    ),
]

_HAS_SOLUTION = (Status.OPTIMAL, Status.FEASIBLE)


@pytest.fixture(scope="module")
def mini_graph():
    return build_graph(FIXTURES / "mini_air.csv", FIXTURES / "mini_city.csv")


@pytest.fixture(scope="module")
def gurobi_solver():
    return GurobiSolver()


@pytest.fixture(scope="module")
def ortools_solver():
    return OrToolsSolver()


def _canonical_objective(
    result: OptimizeResult, req: OptimizeRequest, scale_factor: float
) -> float:
    """결과 route로부터 솔버 비의존 목적값을 재계산한다.

    gurobi.py / ortools.py가 공유하는 목적함수 정의:
        Σ(cost)/budget_scaled · w_cost + Σ(edge_time)/deadline · w_time

    이동시간만 사용한다 (체류시간은 목적함수에 포함되지 않음).
    """
    sum_cost_scaled = result.total_cost_won / scale_factor
    sum_edge_time = sum(e.time_minutes for e in result.route)
    budget_scaled = req.budget_won / scale_factor
    return (
        sum_cost_scaled / budget_scaled * req.w_cost
        + sum_edge_time / req.deadline_minutes * req.w_time
    )


@pytest.fixture(scope="module", params=_SCENARIOS, ids=lambda s: s[0])
def solved_pair(request, gurobi_solver, ortools_solver, mini_graph):
    """각 시나리오를 두 솔버로 풀어 (req, gurobi_result, ortools_result) 반환."""
    _, req = request.param
    return req, gurobi_solver.solve(mini_graph, req), ortools_solver.solve(mini_graph, req)


class TestSolverContract:
    """동일 입력 → 두 솔버가 동치 결과를 내는지 검증."""

    def test_feasibility_agrees(self, solved_pair) -> None:
        """둘 다 해를 찾거나, 둘 다 못 찾거나 — feasibility 판정이 일치해야."""
        _, gurobi_result, ortools_result = solved_pair
        gurobi_solved = gurobi_result.status in _HAS_SOLUTION
        ortools_solved = ortools_result.status in _HAS_SOLUTION
        assert gurobi_solved == ortools_solved, (
            f"feasibility 불일치: gurobi={gurobi_result.status}, "
            f"ortools={ortools_result.status}"
        )

    def test_both_respect_budget(self, solved_pair) -> None:
        """두 솔버 모두 예산 제약을 지켜야."""
        req, gurobi_result, ortools_result = solved_pair
        for name, result in (("gurobi", gurobi_result), ("ortools", ortools_result)):
            if result.status in _HAS_SOLUTION:
                assert result.total_cost_won <= req.budget_won, (
                    f"{name} 예산 초과: {result.total_cost_won} > {req.budget_won}"
                )

    def test_both_respect_deadline(self, solved_pair) -> None:
        """두 솔버 모두 deadline(이동+체류) 제약을 지켜야."""
        req, gurobi_result, ortools_result = solved_pair
        for name, result in (("gurobi", gurobi_result), ("ortools", ortools_result)):
            if result.status in _HAS_SOLUTION:
                assert result.total_time_minutes <= req.deadline_minutes, (
                    f"{name} deadline 초과: "
                    f"{result.total_time_minutes} > {req.deadline_minutes}"
                )

    def test_both_honor_required_pins(self, solved_pair) -> None:
        """required_countries 허브 + required_cities 도시가 두 솔버 결과에 모두 포함."""
        req, gurobi_result, ortools_result = solved_pair
        for name, result in (("gurobi", gurobi_result), ("ortools", ortools_result)):
            if result.status not in _HAS_SOLUTION:
                continue
            for hub in req.required_countries or []:
                assert hub in result.visited_iata, (
                    f"{name}: required_country {hub}가 visited_iata에 없음"
                )
            for city in req.required_cities or []:
                assert city in result.visited_cities, (
                    f"{name}: required_city {city}가 visited_cities에 없음"
                )

    def test_canonical_objective_within_tolerance(self, solved_pair, mini_graph) -> None:
        """route에서 재계산한 목적값이 두 솔버 간 허용오차 내 일치해야.

        같은 모델의 최적해이므로 목적값이 같아야 하나, CP-SAT의 정수 절삭
        오차로 OR-Tools가 미세하게 다른 해를 낼 수 있어 상대 허용오차를 둔다.
        """
        req, gurobi_result, ortools_result = solved_pair
        if gurobi_result.status not in _HAS_SOLUTION:
            pytest.skip("해가 없는 시나리오 — 목적값 비교 불가")

        gurobi_obj = _canonical_objective(gurobi_result, req, mini_graph.scale_factor)
        ortools_obj = _canonical_objective(ortools_result, req, mini_graph.scale_factor)
        assert ortools_obj == pytest.approx(gurobi_obj, rel=_OBJECTIVE_REL_TOL), (
            f"목적값 괴리: gurobi={gurobi_obj:.4f}, ortools={ortools_obj:.4f} "
            f"(상대 허용오차 {_OBJECTIVE_REL_TOL})"
        )
