"""솔버 추상 인터페이스.

모든 구체 솔버(Gurobi, 향후 OR-Tools 등)는 이 ABC를 구현해야 하며,
동일한 `Graph` + `OptimizeRequest` 입력에 대해 `OptimizeResult`를
반환해야 한다 (해 자체는 동일 objective의 다른 optimal일 수 있음).

공통 ``solve()`` 진입점은 **템플릿 메서드** 패턴으로 구현 — 원 조건으로 한 번
풀고(``_solve_internal``), infeasible이면 :func:`find_alternative` 로 4단계
자동 완화 후보를 탐색한다. 후보가 풀리면 그 결과에 ``alternative`` 필드를
채워 반환. 모두 실패하면 원래의 infeasible 결과를 그대로 반환.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..graph import Graph
from ..models import OptimizeRequest, OptimizeResult, Status
from ._alternative import find_alternative


class BaseSolver(ABC):
    """모든 수리 최적화 솔버의 공통 인터페이스."""

    name: str
    """솔버 식별자. OptimizeResult.solver 필드에 그대로 사용된다."""

    def solve(self, graph: Graph, req: OptimizeRequest) -> OptimizeResult:
        """원 조건으로 푼 뒤 infeasible이면 자동 완화 대안을 탐색해 반환한다.

        Args:
            graph: `build_graph()` 로 빌드된 가상 노드 그래프.
            req: 사용자 입력 (예산, 기간, 출발지, 가중치, 선택지).

        Returns:
            경로 + 총합 + 솔버 메타를 포함한 `OptimizeResult`. ``alternative``
            필드가 채워졌으면 원 조건이 아닌 완화된 조건의 풀이 결과를 의미.
            모든 완화 실패 시 ``status=infeasible``, ``alternative=None``.

        Raises:
            SolverInitializationError: 솔버 초기화 (라이센스 등) 실패.
        """
        result = self._solve_internal(graph, req)
        if result.status != Status.INFEASIBLE:
            return result
        finding = find_alternative(graph, req, self._solve_internal)
        if finding is None:
            return result
        alt, alt_result = finding
        return alt_result.model_copy(update={"alternative": alt})

    @abstractmethod
    def _solve_internal(self, graph: Graph, req: OptimizeRequest) -> OptimizeResult:
        """원 조건으로 한 번만 푸는 솔버 호출. 대안 탐색을 거치지 않는다.

        :func:`find_alternative` 가 이 메서드를 콜백으로 받아 여러 변형 입력에
        대해 호출하므로, 이 메서드 자체에서 재귀적으로 ``solve`` 를 부르면
        절대 안 된다.
        """
        ...


class SolverInitializationError(RuntimeError):
    """솔버 초기화 실패 (라이센스, 환경변수 누락 등)."""
