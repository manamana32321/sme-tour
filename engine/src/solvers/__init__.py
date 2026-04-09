"""솔버 패키지.

MVP A에서는 `GurobiSolver` 단 하나만 존재하지만, 전략 패턴(Base class +
factory)을 유지하여 미래의 OR-Tools/SCIP/HiGHS 추가 시 zero-friction
확장을 가능하게 한다.

Solver import는 함수 내부에서 수행되어 gurobipy가 설치되지 않은 환경
(예: CI lint-only job, 테스트 단계)에서도 이 패키지를 import할 수 있다.
"""

from __future__ import annotations

from .base import BaseSolver


def get_solver() -> BaseSolver:
    """환경에 맞는 solver 인스턴스를 생성해 반환.

    현재는 무조건 GurobiSolver. 향후 `SME_TOUR_SOLVER` 환경변수로
    분기하려면 여기서 추가하면 된다.

    Returns:
        초기화된 솔버 인스턴스 (WLS credentials 적용 완료).

    Raises:
        ImportError: gurobipy가 설치되지 않은 경우.
        KeyError: 필수 WLS 환경변수 누락.
    """
    from .gurobi import GurobiSolver

    return GurobiSolver()


__all__ = ["BaseSolver", "get_solver"]
