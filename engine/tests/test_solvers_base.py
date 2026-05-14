"""BaseSolver ABC + factory 계약 테스트.

구체 솔버(GurobiSolver)는 Task 6에서 구현되므로 여기서는 추상 인터페이스와
팩토리가 의도한 형태로 존재하는지만 확인한다.
"""

from __future__ import annotations

import inspect

import pytest

from src.graph import Graph
from src.models import OptimizeRequest, OptimizeResult, Status
from src.solvers import BaseSolver, get_solver


class TestBaseSolverContract:
    def test_cannot_instantiate_abstract_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseSolver()  # type: ignore[abstract]

    def test_solve_is_abstract_method(self) -> None:
        assert getattr(BaseSolver.solve, "__isabstractmethod__", False) is True

    def test_solve_signature(self) -> None:
        """solve는 (graph, req) -> OptimizeResult 시그니처여야 한다."""
        sig = inspect.signature(BaseSolver.solve)
        params = list(sig.parameters.keys())
        assert params == ["self", "graph", "req"]

    def test_custom_subclass_can_be_instantiated(self) -> None:
        """서브클래스가 solve를 구현하면 정상 생성되어야 한다."""

        class DummySolver(BaseSolver):
            name = "dummy"

            def solve(self, graph: Graph, req: OptimizeRequest) -> OptimizeResult:
                return OptimizeResult(
                    status=Status.OPTIMAL,
                    route=[],
                    total_cost_won=0,
                    total_time_minutes=0,
                    objective_value=0.0,
                    solve_time_ms=0,
                    solver="gurobi",  # Literal constraint (MVP A)
                    visited_iata=[],
                    visited_cities=[],
                    engine_version="test",
                )

        solver = DummySolver()
        assert solver.name == "dummy"


class TestFactory:
    def test_get_solver_returns_valid_solver(self) -> None:
        """factory가 유효한 솔버를 반환한다.

        Gurobi 설치 + WLS 인증 성공 → GurobiSolver,
        미설치 or WLS 실패 → OrToolsSolver fallback.
        어느 쪽이든 BaseSolver 인스턴스여야 한다.
        """
        solver = get_solver()
        assert isinstance(solver, BaseSolver)
        assert solver.name in ("gurobi", "ortools")
