"""Pydantic 모델 검증 테스트.

프론트 Zod 스키마와의 드리프트를 조기에 잡기 위해 경계값과
잘못된 입력을 모두 커버합니다.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models import Alternative, OptimizeRequest, OptimizeResult, RouteEdge, Status


class TestOptimizeRequest:
    def test_valid_request(self) -> None:
        req = OptimizeRequest(
            budget_won=10_000_000,
            deadline_days=14,
            start_hub="CDG",
            w_cost=0.5,
        )
        assert req.budget_won == 10_000_000
        assert req.deadline_days == 14
        assert req.start_hub == "CDG"
        assert req.w_cost == 0.5

    def test_computed_w_time(self) -> None:
        req = OptimizeRequest(
            budget_won=5_000_000, deadline_days=7, start_hub="CDG", w_cost=0.3
        )
        assert req.w_time == pytest.approx(0.7)

    def test_computed_deadline_minutes(self) -> None:
        req = OptimizeRequest(
            budget_won=5_000_000, deadline_days=14, start_hub="CDG", w_cost=0.5
        )
        assert req.deadline_minutes == 14 * 24 * 60  # 20160

    def test_default_w_cost_is_half(self) -> None:
        req = OptimizeRequest(budget_won=5_000_000, deadline_days=7, start_hub="CDG")
        assert req.w_cost == 0.5
        assert req.w_time == 0.5

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("budget_won", 999_999),  # below min
            ("budget_won", 30_000_001),  # above max
            ("deadline_days", 2),  # below min
            ("deadline_days", 31),  # above max
            ("w_cost", -0.01),
            ("w_cost", 1.01),
        ],
    )
    def test_rejects_out_of_range(self, field: str, value: float) -> None:
        base = {
            "budget_won": 5_000_000,
            "deadline_days": 7,
            "start_hub": "CDG",
            "w_cost": 0.5,
        }
        base[field] = value
        with pytest.raises(ValidationError):
            OptimizeRequest(**base)  # type: ignore[arg-type]

    @pytest.mark.parametrize("hub", ["CD", "CDGG", ""])
    def test_rejects_invalid_hub_length(self, hub: str) -> None:
        with pytest.raises(ValidationError):
            OptimizeRequest(
                budget_won=5_000_000, deadline_days=7, start_hub=hub, w_cost=0.5
            )

    def test_rejects_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            OptimizeRequest(budget_won=5_000_000)  # type: ignore[call-arg]


class TestOptimizeRequestStayDays:
    def test_stay_days_none_default(self) -> None:
        req = OptimizeRequest(budget_won=10_000_000, deadline_days=14, start_hub="CDG")
        assert req.stay_days is None

    def test_stay_days_valid_dict(self) -> None:
        req = OptimizeRequest(
            budget_won=10_000_000, deadline_days=14, start_hub="CDG",
            stay_days={"CDG": 2, "FCO": 1},
        )
        assert req.stay_days == {"CDG": 2, "FCO": 1}

    def test_stay_days_zero_allowed(self) -> None:
        req = OptimizeRequest(
            budget_won=10_000_000, deadline_days=14, start_hub="CDG",
            stay_days={"CDG": 0},
        )
        assert req.stay_days == {"CDG": 0}

    def test_stay_days_max_allowed(self) -> None:
        req = OptimizeRequest(
            budget_won=10_000_000, deadline_days=30, start_hub="CDG",
            stay_days={"CDG": 30},
        )
        assert req.stay_days == {"CDG": 30}

    def test_stay_days_negative_rejected(self) -> None:
        with pytest.raises(ValueError):
            OptimizeRequest(
                budget_won=10_000_000, deadline_days=14, start_hub="CDG",
                stay_days={"CDG": -1},
            )

    def test_stay_days_too_large_rejected(self) -> None:
        with pytest.raises(ValueError):
            OptimizeRequest(
                budget_won=10_000_000, deadline_days=14, start_hub="CDG",
                stay_days={"CDG": 31},
            )

    def test_stay_days_empty_dict_allowed(self) -> None:
        req = OptimizeRequest(
            budget_won=10_000_000, deadline_days=14, start_hub="CDG",
            stay_days={},
        )
        assert req.stay_days == {}


class TestOptimizeRequestRequiredCities:
    def test_default_none(self):
        req = OptimizeRequest(budget_won=10_000_000, deadline_days=14, start_hub="CDG")
        assert req.required_cities is None

    def test_valid_list(self):
        req = OptimizeRequest(
            budget_won=10_000_000, deadline_days=14, start_hub="CDG",
            required_cities=["NCE_City", "MIL_City"],
        )
        assert req.required_cities == ["NCE_City", "MIL_City"]

    def test_empty_list_allowed(self):
        req = OptimizeRequest(
            budget_won=10_000_000, deadline_days=14, start_hub="CDG",
            required_cities=[],
        )
        assert req.required_cities == []


class TestRouteEdge:
    def test_valid_edge(self) -> None:
        edge = RouteEdge(
            from_node="CDG_Exit",
            to_node="PRG_Entry",
            mode="Air_CZA",
            category="air",
            cost_won=246_665,
            time_minutes=105,
        )
        assert edge.category == "air"

    @pytest.mark.parametrize("category", ["air", "ground", "hub_stay"])
    def test_all_categories_allowed(self, category: str) -> None:
        RouteEdge(
            from_node="A",
            to_node="B",
            mode="x",
            category=category,  # type: ignore[arg-type]
            cost_won=0,
            time_minutes=0,
        )

    def test_rejects_unknown_category(self) -> None:
        with pytest.raises(ValidationError):
            RouteEdge(
                from_node="A",
                to_node="B",
                mode="x",
                category="rocket",  # type: ignore[arg-type]
                cost_won=0,
                time_minutes=0,
            )


class TestOptimizeResult:
    def test_optimal_result(self) -> None:
        result = OptimizeResult(
            status=Status.OPTIMAL,
            route=[],
            total_cost_won=4_187_641,
            total_time_minutes=11_340,
            objective_value=0.489718,
            solve_time_ms=103,
            solver="gurobi",
            visited_iata=["CDG", "PRG"],
            visited_cities=["NCE_City"],
            engine_version="sme-tour-engine 0.1.0 (abc1234)",
        )
        assert result.status == Status.OPTIMAL
        assert result.solver == "gurobi"

    def test_infeasible_result(self) -> None:
        """Infeasible도 유효한 응답 — HTTP 200 + status=infeasible."""
        result = OptimizeResult(
            status=Status.INFEASIBLE,
            route=[],
            total_cost_won=0,
            total_time_minutes=0,
            objective_value=0.0,
            solve_time_ms=200,
            solver="gurobi",
            visited_iata=[],
            visited_cities=[],
            engine_version="sme-tour-engine 0.1.0",
        )
        assert result.status == Status.INFEASIBLE
        assert result.route == []

    def test_accepts_both_solver_literals(self) -> None:
        """gurobi와 ortools 모두 허용 (OR-Tools fallback 지원)."""
        for solver_name in ("gurobi", "ortools"):
            result = OptimizeResult(
                status=Status.OPTIMAL,
                route=[],
                total_cost_won=0,
                total_time_minutes=0,
                objective_value=0.0,
                solve_time_ms=0,
                solver=solver_name,  # type: ignore[arg-type]
                visited_iata=[],
                visited_cities=[],
                engine_version="x",
            )
            assert result.solver == solver_name

    def test_rejects_unknown_solver(self) -> None:
        """Literal constraint가 gurobi/ortools 외 다른 값을 차단."""
        with pytest.raises(ValidationError):
            OptimizeResult(
                status=Status.OPTIMAL,
                route=[],
                total_cost_won=0,
                total_time_minutes=0,
                objective_value=0.0,
                solve_time_ms=0,
                solver="cplex",  # type: ignore[arg-type]
                visited_iata=[],
                visited_cities=[],
                engine_version="x",
            )


class TestAlternative:
    """원 조건 infeasible 시 자동 완화 결과를 노출하는 Alternative 모델."""

    def test_default_alternative_is_none(self) -> None:
        """alternative 필드는 기본 None — 평소 응답엔 안 들어감."""
        result = OptimizeResult(
            status=Status.OPTIMAL,
            route=[],
            total_cost_won=0,
            total_time_minutes=0,
            objective_value=0.0,
            solve_time_ms=0,
            solver="gurobi",
            visited_iata=[],
            visited_cities=[],
            engine_version="x",
        )
        assert result.alternative is None

    def test_alternative_populated(self) -> None:
        """완화 적용 시 alternative 객체가 채워지고, applied_* 필드로 변경된
        입력이 노출된다."""
        alt = Alternative(
            type="선택 도시 일부 제외: ['CDG'] 제외",
            applied_budget_won=10_000_000,
            applied_deadline_days=21,
            applied_required_countries=["FCO", "VIE"],
            applied_required_cities=["NCE_City", "Interlaken_City"],
            applied_stay_days={"FCO": 2, "VIE": 1},
        )
        result = OptimizeResult(
            status=Status.OPTIMAL,
            route=[],
            total_cost_won=1_224_954,
            total_time_minutes=11_700,
            objective_value=0.2557,
            solve_time_ms=80,
            solver="gurobi",
            visited_iata=["FCO", "VIE"],
            visited_cities=["NCE_City", "Interlaken_City"],
            engine_version="x",
            alternative=alt,
        )
        assert result.alternative is not None
        assert result.alternative.type.startswith("선택 도시 일부 제외")
        assert result.alternative.applied_required_countries == ["FCO", "VIE"]

    def test_alternative_accepts_null_applied_fields(self) -> None:
        """applied_required_* / applied_stay_days 는 None 허용 (해당 입력
        없었으면 자연스럽게 None)."""
        alt = Alternative(
            type="예산 증가",
            applied_budget_won=12_000_000,
            applied_deadline_days=14,
            applied_required_countries=None,
            applied_required_cities=None,
            applied_stay_days=None,
        )
        assert alt.applied_required_countries is None
        assert alt.applied_stay_days is None
