"""솔버 패키지.

Gurobi(상용, 고성능)를 우선 시도하고, 설치되지 않았거나 WLS 인증이
실패하면 OR-Tools(오픈소스, fallback)로 자동 전환한다.

Import는 함수 내부에서 지연 수행되어, gurobipy 또는 ortools가 설치되지
않은 환경(예: CI lint-only job)에서도 이 패키지를 import할 수 있다.
"""

from __future__ import annotations

import logging

from .base import BaseSolver, SolverInitializationError

logger = logging.getLogger(__name__)


def get_solver() -> BaseSolver:
    """환경에 맞는 solver 인스턴스를 생성해 반환.

    **우선순위**: Gurobi → OR-Tools.

    1. ``gurobipy`` import 시도 → 성공이면 WLS 인증 시도 → 성공이면 GurobiSolver
    2. ``gurobipy`` 미설치 또는 WLS 인증 실패 → OrToolsSolver fallback

    Returns:
        초기화된 솔버 인스턴스.

    Raises:
        RuntimeError: Gurobi도 OR-Tools도 사용 불가능한 경우.
    """
    # 1) Gurobi 시도
    try:
        from .gurobi import GurobiSolver

        solver = GurobiSolver()
        logger.info("Solver: Gurobi (WLS 인증 성공)")
        return solver
    except ImportError:
        logger.info("gurobipy 미설치 — OR-Tools fallback 시도")
    except SolverInitializationError as e:
        logger.warning("Gurobi WLS 인증 실패 (%s) — OR-Tools fallback 시도", e)

    # 2) OR-Tools fallback
    try:
        from .ortools import OrToolsSolver

        solver = OrToolsSolver()
        logger.info("Solver: OR-Tools (fallback)")
        return solver
    except ImportError:
        raise RuntimeError(
            "Gurobi와 OR-Tools 모두 사용 불가능합니다. "
            "pip install gurobipy 또는 pip install ortools 중 하나를 설치해주세요."
        ) from None


__all__ = ["BaseSolver", "get_solver"]
