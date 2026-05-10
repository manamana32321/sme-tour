"""Pydantic 모델 — `/optimize` 엔드포인트의 요청/응답 계약.

프론트엔드의 Zod 스키마(`frontend/lib/schemas.ts`)와 1:1 미러링되므로
필드 이름·타입·제약을 임의로 바꾸면 계약이 깨집니다.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, computed_field, field_validator


class Status(str, Enum):
    """솔버가 반환하는 해의 상태."""

    OPTIMAL = "optimal"
    """최적해 발견."""

    FEASIBLE = "feasible"
    """실행 가능한 해 (타임아웃 내 최적성 미확인)."""

    INFEASIBLE = "infeasible"
    """제약 조건을 만족하는 해가 존재하지 않음."""

    TIMEOUT = "timeout"
    """솔버 시간 초과, 해 없음."""


class OptimizeRequest(BaseModel):
    """`/optimize` 요청 본문.

    필드 제약은 프론트 슬라이더 범위와 반드시 일치해야 합니다.
    """

    budget_won: int = Field(
        ...,
        ge=1_000_000,
        le=30_000_000,
        description="총 예산 (KRW). 1,000,000 ≤ budget ≤ 30,000,000",
    )
    deadline_days: int = Field(
        ...,
        ge=3,
        le=30,
        description="여행 기간 (일). 3 ≤ days ≤ 30",
    )
    start_hub: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="출발 공항 IATA 3자리 코드 (예: 'CDG')",
    )
    w_cost: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="비용 가중치. 0.0 = 시간 최우선, 1.0 = 비용 최우선",
    )
    required_countries: list[str] | None = Field(
        None,
        description="방문 필수 국가 IATA 코드 리스트. None이면 전체 15개국 필수 방문.",
    )
    stay_days: dict[str, int] | None = Field(
        None,
        description=(
            "도시별 체류일 (key: 허브 IATA 또는 내륙 도시 노드명, value: 0~30일). "
            "None이면 체류시간 미반영 (이동시간만 시간 제약 검사). "
            "지정한 도시가 실제 방문되지 않으면(y[d]=0) 시간 기여 0."
        ),
    )

    @field_validator("stay_days")
    @classmethod
    def validate_stay_days(cls, v: dict[str, int] | None) -> dict[str, int] | None:
        if v is None:
            return None
        for key, days in v.items():
            if not isinstance(days, int) or days < 0 or days > 30:
                raise ValueError(
                    f"stay_days[{key!r}] = {days} (0~30 사이 정수여야 함)"
                )
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def w_time(self) -> float:
        """시간 가중치 (1 - w_cost). 응답으로 그대로 반환."""
        return 1.0 - self.w_cost

    @computed_field  # type: ignore[prop-decorator]
    @property
    def deadline_minutes(self) -> int:
        """일 단위 deadline을 솔버 입력용 분 단위로 변환."""
        return self.deadline_days * 24 * 60


class RouteEdge(BaseModel):
    """경로의 한 에지(한 단계 이동).

    `from_node`, `to_node`는 가상 노드 식별자:
    - 허브: ``{IATA}_Entry`` 또는 ``{IATA}_Exit`` (예: ``CDG_Entry``)
    - 내륙 도시: ``{CityName}_City`` (예: ``NCE_City``)

    `mode`는 ``Air_{carrier}`` / ``Ground_{transport}`` / ``Hub_Stay``.
    `category`는 UI 아이콘 결정용 프리계산 필드.
    """

    from_node: str
    to_node: str
    mode: str
    category: Literal["air", "ground", "hub_stay"]
    cost_won: int
    time_minutes: int


class OptimizeResult(BaseModel):
    """`/optimize` 응답 본문.

    infeasible/timeout 케이스에서도 status 필드만 설정하고
    route/총합은 기본값(빈 리스트, 0)으로 반환합니다.
    HTTP 상태 코드 매핑은 `main.py` 의 exception handler 참조.
    """

    status: Status
    route: list[RouteEdge]
    total_cost_won: int
    total_time_minutes: int
    objective_value: float
    solve_time_ms: int
    solver: Literal["gurobi", "ortools"]
    visited_iata: list[str]
    visited_cities: list[str]
    engine_version: str
