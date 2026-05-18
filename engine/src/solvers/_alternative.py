"""원 조건 infeasible 시 자동 완화 대안 탐색.

10주차 PoC의 ``find_alternative_conditions`` (예산↑/기간↑/도시↓/복합) 4단계
전략을 엔진 모듈 구조로 이식. 솔버에 의존하지 않도록 ``solve_once`` 콜백을
받아 호출 — Gurobi/OR-Tools 둘 다 동일 인터페이스로 재사용 가능.

각 전략은 첫 번째 OPTIMAL/FEASIBLE 후보를 발견하면 즉시 반환하며, 모두
실패하면 ``None``. PoC와 동일하게 전략 순서는 비용·부담이 적은 쪽부터:
1. 예산 증가 — 가장 간단, 도시·기간 변경 없음
2. 여행 기간 연장 — 사용자 일정만 늘림
3. 사용자 선택 도시 일부 제외 — 가장 큰 의도 손실
4. 복합 — 위 세 가지 조합 (1~3 단독으로 풀리지 않을 때만 진입)
"""

from __future__ import annotations

from collections.abc import Callable
from itertools import combinations

from ..graph import Graph
from ..models import Alternative, OptimizeRequest, OptimizeResult, Status

SolveCallable = Callable[[Graph, OptimizeRequest], OptimizeResult]

# OptimizeRequest 스키마의 상한과 일치해야 함 (engine/src/models.py)
_BUDGET_MAX = 30_000_000
_DEADLINE_MAX = 30

# 전략 1 (단독 예산 증가) — 작은 폭부터 점진적으로
_BUDGET_MULTIPLIERS_SIMPLE: tuple[float, ...] = (1.1, 1.2, 1.3, 1.5, 2.0)
# 전략 4 (복합) — 단독보다 보수적인 폭만 시도 (이미 도시 제외와 결합되므로)
_BUDGET_MULTIPLIERS_COMPOSITE: tuple[float, ...] = (1.1, 1.2, 1.5)

# 전략 2 (단독 기간 연장) — 1일부터 10일까지
_EXTRA_DAYS_SIMPLE: tuple[int, ...] = (1, 2, 3, 5, 7, 10)
# 전략 4 (복합) — 기간 연장폭도 보수적으로
_EXTRA_DAYS_COMPOSITE: tuple[int, ...] = (1, 3, 5, 7)


def find_alternative(
    graph: Graph,
    req: OptimizeRequest,
    solve_once: SolveCallable,
) -> tuple[Alternative, OptimizeResult] | None:
    """원 조건 infeasible 시 4단계 완화로 첫 OPTIMAL 후보를 찾는다.

    Args:
        graph: 솔버에 그대로 전달할 그래프 (불변).
        req: 원 요청. 이 함수가 ``model_copy(update=...)`` 로 변형해 시도한다.
        solve_once: 재귀 없이 한 번만 푸는 솔버 호출 (보통 ``solver._solve_internal``).

    Returns:
        ``(Alternative, OptimizeResult)`` — 완화 메타와 그 입력의 풀이 결과.
        모든 전략 실패 시 ``None``.
    """
    user_selected = _user_selected(req)

    # 전략 1: 예산 증가
    for mult in _BUDGET_MULTIPLIERS_SIMPLE:
        new_budget = int(req.budget_won * mult)
        if new_budget > _BUDGET_MAX or new_budget == req.budget_won:
            continue
        alt_req = req.model_copy(update={"budget_won": new_budget})
        result = solve_once(graph, alt_req)
        if _is_solved(result):
            return _build_alternative(alt_req, "예산 증가"), result

    # 전략 2: 여행 기간 연장
    for extra in _EXTRA_DAYS_SIMPLE:
        new_days = req.deadline_days + extra
        if new_days > _DEADLINE_MAX:
            continue
        alt_req = req.model_copy(update={"deadline_days": new_days})
        result = solve_once(graph, alt_req)
        if _is_solved(result):
            return _build_alternative(alt_req, "여행 기간 연장"), result

    # 전략 3: 사용자 선택 일부 제외 (user_selected 비어있으면 skip)
    if user_selected:
        for remove_count in range(1, len(user_selected)):
            for removed_tuple in combinations(user_selected, remove_count):
                removed = set(removed_tuple)
                alt_req = _reduce_selection(req, removed)
                result = solve_once(graph, alt_req)
                if _is_solved(result):
                    label = f"선택 도시 일부 제외: {list(removed_tuple)} 제외"
                    return _build_alternative(alt_req, label), result

    # 전략 4: 복합 (예산 x 기간 x 도시 제외) — user_selected 비어있으면 skip
    if user_selected:
        for mult in _BUDGET_MULTIPLIERS_COMPOSITE:
            new_budget = int(req.budget_won * mult)
            if new_budget > _BUDGET_MAX:
                continue
            for extra in _EXTRA_DAYS_COMPOSITE:
                new_days = req.deadline_days + extra
                if new_days > _DEADLINE_MAX:
                    continue
                for remove_count in range(0, len(user_selected)):
                    for removed_tuple in combinations(user_selected, remove_count):
                        removed = set(removed_tuple)
                        reduced = _reduce_selection(req, removed)
                        alt_req = reduced.model_copy(
                            update={
                                "budget_won": new_budget,
                                "deadline_days": new_days,
                            }
                        )
                        result = solve_once(graph, alt_req)
                        if _is_solved(result):
                            label = (
                                f"복합 조건 완화: 예산 {mult:.1f}배, "
                                f"{extra}일 연장, {list(removed_tuple)} 제외"
                            )
                            return _build_alternative(alt_req, label), result

    return None


def _is_solved(r: OptimizeResult) -> bool:
    return r.status in (Status.OPTIMAL, Status.FEASIBLE)


def _user_selected(req: OptimizeRequest) -> list[str]:
    """사용자가 명시 선택한 허브 + 내륙 도시 합산 (도시 제외 전략의 대상)."""
    out: list[str] = []
    if req.required_countries:
        out.extend(req.required_countries)
    if req.required_cities:
        out.extend(req.required_cities)
    return out


def _reduce_selection(req: OptimizeRequest, removed: set[str]) -> OptimizeRequest:
    """req의 required_* 와 stay_days에서 ``removed`` 항목 모두 제거.

    None 필드는 그대로 None — full mode 의미를 보존하기 위함.
    """
    new_hubs = (
        [h for h in req.required_countries if h not in removed]
        if req.required_countries is not None
        else None
    )
    new_cities = (
        [c for c in req.required_cities if c not in removed]
        if req.required_cities is not None
        else None
    )
    new_stay = (
        {k: v for k, v in req.stay_days.items() if k not in removed}
        if req.stay_days is not None
        else None
    )
    return req.model_copy(
        update={
            "required_countries": new_hubs,
            "required_cities": new_cities,
            "stay_days": new_stay,
        }
    )


def _build_alternative(applied: OptimizeRequest, type_label: str) -> Alternative:
    """완화 후 적용된 req로부터 Alternative 객체 생성."""
    return Alternative(
        type=type_label,
        applied_budget_won=applied.budget_won,
        applied_deadline_days=applied.deadline_days,
        applied_required_countries=applied.required_countries,
        applied_required_cities=applied.required_cities,
        applied_stay_days=applied.stay_days,
    )
