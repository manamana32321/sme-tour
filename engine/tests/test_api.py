"""FastAPI 엔드포인트 통합 테스트.

httpx TestClient로 /optimize, /healthz, /readyz를 검증한다.
실제 solver를 사용 — OR-Tools fallback이 자동 적용.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestHealthEndpoints:
    def test_healthz(self, client: TestClient) -> None:
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_readyz(self, client: TestClient) -> None:
        r = client.get("/readyz")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["solver"] in ("gurobi", "ortools")
        assert int(body["nodes"]) >= 30
        assert int(body["edges"]) >= 100

    def test_meta_version(self, client: TestClient) -> None:
        r = client.get("/meta/version")
        assert r.status_code == 200
        assert "version" in r.json()


class TestOptimize:
    def test_valid_request(self, client: TestClient) -> None:
        r = client.post("/optimize", json={
            "budget_won": 10_000_000,
            "deadline_days": 14,
            "start_hub": "CDG",
            "w_cost": 0.5,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in ("optimal", "feasible")
        assert len(body["route"]) > 0
        assert body["total_cost_won"] > 0
        assert body["total_time_minutes"] > 0
        assert body["solver"] in ("gurobi", "ortools")

    def test_422_on_invalid_budget(self, client: TestClient) -> None:
        r = client.post("/optimize", json={
            "budget_won": 500,  # below min 1M
            "deadline_days": 14,
            "start_hub": "CDG",
            "w_cost": 0.5,
        })
        assert r.status_code == 422

    def test_422_on_missing_field(self, client: TestClient) -> None:
        r = client.post("/optimize", json={
            "budget_won": 10_000_000,
        })
        assert r.status_code == 422

    def test_cost_priority_vs_time_priority(self, client: TestClient) -> None:
        """가중치가 다르면 다른 해를 반환할 수 있다."""
        r_cost = client.post("/optimize", json={
            "budget_won": 10_000_000,
            "deadline_days": 14,
            "start_hub": "CDG",
            "w_cost": 0.9,
        })
        r_time = client.post("/optimize", json={
            "budget_won": 10_000_000,
            "deadline_days": 14,
            "start_hub": "CDG",
            "w_cost": 0.1,
        })
        # 둘 다 200이어야
        assert r_cost.status_code == 200
        assert r_time.status_code == 200
        # 비용 우선이면 total_cost_won이 더 낮을 가능성 (보장은 안 되지만)
        # 여기선 둘 다 유효한 응답인지만 확인
        assert r_cost.json()["status"] in ("optimal", "feasible", "timeout")
        assert r_time.json()["status"] in ("optimal", "feasible", "timeout")

    def test_cors_header(self, client: TestClient) -> None:
        """OPTIONS preflight가 CORS 헤더를 반환하는지."""
        r = client.options("/optimize", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        })
        assert r.status_code == 200
        assert "access-control-allow-origin" in r.headers
