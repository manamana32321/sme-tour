"""솔버 추상 인터페이스.

모든 구체 솔버(Gurobi, 향후 OR-Tools 등)는 이 ABC를 구현해야 하며,
동일한 `Graph` + `OptimizeRequest` 입력에 대해 `OptimizeResult`를
반환해야 한다 (해 자체는 동일 objective의 다른 optimal일 수 있음).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..graph import Graph
from ..models import OptimizeRequest, OptimizeResult


class BaseSolver(ABC):
    """모든 수리 최적화 솔버의 공통 인터페이스."""

    name: str
    """솔버 식별자. OptimizeResult.solver 필드에 그대로 사용된다."""

    @abstractmethod
    def solve(self, graph: Graph, req: OptimizeRequest) -> OptimizeResult:
        """주어진 그래프와 제약 하에서 최적 경로를 찾는다.

        Args:
            graph: `build_graph()` 로 빌드된 가상 노드 그래프.
            req: 사용자 입력 (예산, 기간, 출발지, 가중치).

        Returns:
            경로 + 총합 + 솔버 메타를 포함한 `OptimizeResult`.
            Infeasible/Timeout도 예외가 아닌 status 필드로 표현한다.

        Raises:
            SolverInitializationError: 솔버 초기화 (라이센스 등) 실패.
        """
        ...


class SolverInitializationError(RuntimeError):
    """솔버 초기화 실패 (라이센스, 환경변수 누락 등)."""
