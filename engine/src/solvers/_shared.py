"""솔버 비의존 공통 헬퍼.

Gurobi/OR-Tools 솔버가 동일하게 사용하는 후처리 로직 — 경로 재구성과
체류시간 합산. 제약/목적함수 빌드는 솔버 API(``m.addConstr`` vs
``model.add``)에 종속적이라 각 솔버 파일에 남는다.

이 모듈을 SSOT로 두면 ``y_hub`` 정의·``stay_days``·``required_cities`` 같은
후처리 변경을 한 곳에서만 하면 된다.
"""

from __future__ import annotations

from ..graph import Graph
from ..models import RouteEdge

# from_node → (u, v, mode, cost_scaled, time_minutes)
# TSP 해이므로 노드당 outflow 에지는 최대 1개 → from_node 키로 유일.
ActiveEdge = tuple[str, str, str, float, int]


def edge_category(mode: str) -> str:
    """이동 수단 태그를 UI 아이콘/집계용 카테고리로 매핑한다."""
    if mode == "Hub_Stay":
        return "hub_stay"
    if mode.startswith("Air_"):
        return "air"
    return "ground"


def reconstruct_route(
    start_node: str,
    active_edges: dict[str, ActiveEdge],
    graph: Graph,
) -> tuple[list[RouteEdge], list[str], list[str], int, int]:
    """start_node부터 active edge 체인을 순회해 경로를 복원한다.

    Args:
        start_node: 출발 가상 노드 (``{IATA}_Entry``).
        active_edges: ``from_node → (u, v, mode, cost_scaled, time_minutes)``.
            해당 노드에서 출발하는 활성(x=1) 에지.
        graph: ``scale_factor`` 로 비용을 원래 KRW 단위로 환산.

    Returns:
        ``(route, visited_iata_sorted, visited_cities, total_cost_won,
        total_time_minutes)``. ``total_time_minutes`` 는 이동시간만 — 체류시간은
        호출 측에서 :func:`stay_time_minutes` 로 더한다.
    """
    route: list[RouteEdge] = []
    visited_iata: set[str] = set()
    visited_cities: list[str] = []
    total_cost = 0
    total_time = 0

    curr = start_node
    # +1: start_node로 돌아오는 마지막 에지까지 포함.
    for _ in range(len(active_edges) + 1):
        if curr not in active_edges:
            break
        u, v, mode, cost_scaled, time_minutes = active_edges[curr]
        cost_won = int(cost_scaled * graph.scale_factor)

        route.append(
            RouteEdge(
                from_node=u,
                to_node=v,
                mode=mode,
                category=edge_category(mode),
                cost_won=cost_won,
                time_minutes=time_minutes,
            )
        )
        total_cost += cost_won
        total_time += time_minutes

        for node in (u, v):
            if node.endswith("_Entry") or node.endswith("_Exit"):
                visited_iata.add(node.rsplit("_", 1)[0])
            elif node not in visited_cities:
                visited_cities.append(node)

        curr = v
        if curr == start_node:
            break

    return route, sorted(visited_iata), visited_cities, total_cost, total_time


def stay_time_minutes(
    y_values: dict[str, int],
    stay_days: dict[str, int] | None,
) -> int:
    """방문한(``y == 1``) 목적지의 체류시간 총합(분).

    deadline 시간 제약에 포함된 체류시간과 의미를 일치시키기 위해
    ``OptimizeResult.total_time_minutes`` 에도 동일하게 더한다.
    """
    if not stay_days:
        return 0
    return sum(
        stay_days.get(d, 0) * 1440
        for d, y in y_values.items()
        if y == 1
    )
