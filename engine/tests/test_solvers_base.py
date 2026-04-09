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
from src.solvers.base import SolverInitializationError


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
    def test_get_solver_triggers_gurobi_import(self) -> None:
        """gurobipy가 설치되지 않은 환경에서는 ImportError, 설치된 환경에서는 정상.

        이 테스트는 gurobipy 설치 여부에 관계없이 factory가 lazy import를
        실제로 수행하는지만 검증한다.
        """
        try:
            solver = get_solver()
            # 설치되어 있고 WLS env가 있으면 정상 생성
            assert isinstance(solver, BaseSolver)
            assert solver.name == "gurobi"
        except ImportError:
            # gurobipy 미설치 — 정상 동작
            pytest.skip("gurobipy not installed in this environment")
        except (KeyError, SolverInitializationError):
            # WLS env vars 누락 — factory 자체는 정상, 초기화 단계에서 실패
            pytest.skip("WLS credentials not set")
