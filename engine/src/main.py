"""SME Tour Optimization API.

FastAPI 앱 진입점. 시작 시 그래프 로드 + 솔버 초기화를 수행하고,
``/optimize`` 엔드포인트로 최적 경로를 반환한다.
"""

from __future__ import annotations

import logging
import os
import time as time_mod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .data_loader import load_default_graph
from .graph import Graph
from .models import OptimizeRequest, OptimizeResult
from .solvers import BaseSolver, get_solver
from .solvers.base import SolverInitializationError

logger = logging.getLogger(__name__)

# ── 앱 상태 (lifespan에서 초기화) ───────────────────────────
_graph: Graph | None = None
_solver: BaseSolver | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """앱 시작/종료 이벤트."""
    global _graph, _solver

    logger.info("Loading graph from CSV...")
    _graph = load_default_graph()
    logger.info(
        "Graph loaded: %d nodes, %d edges, %d hubs",
        len(_graph.virtual_nodes),
        len(_graph.edges),
        len(_graph.hubs),
    )

    logger.info("Initializing solver...")
    _solver = get_solver()
    logger.info("Solver ready: %s", _solver.name)

    yield

    logger.info("Shutting down.")


app = FastAPI(
    title="SME Tour Optimization API",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────
# Starlette CORSMiddleware는 allow_origins에 glob 미지원 — vercel preview 처럼
# 동적 sub-domain은 allow_origin_regex로 매치해야 함.
_cors_origins = [
    s
    for s in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "https://sme-tour.json-server.win,http://localhost:3000",
    ).split(",")
    if s
]
_cors_origin_regex = os.environ.get(
    "CORS_ALLOWED_ORIGIN_REGEX",
    r"https://sme-tour-.*\.vercel\.app",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_cors_origin_regex,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)


# ── Exception Handlers ───────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_handler(_request: object, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# ── Endpoints ────────────────────────────────────────────────
@app.post("/optimize", response_model=OptimizeResult)
def optimize(req: OptimizeRequest) -> OptimizeResult:
    """사용자 제약 조건으로 최적 경로를 계산한다."""
    if _graph is None or _solver is None:
        raise HTTPException(status_code=503, detail="Engine not ready")

    start = time_mod.perf_counter()
    try:
        result = _solver.solve(_graph, req)
    except SolverInitializationError as e:
        raise HTTPException(status_code=500, detail=f"Solver error: {e}") from e
    except Exception as e:
        logger.exception("Unexpected solver error")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}") from e

    elapsed_ms = int((time_mod.perf_counter() - start) * 1000)
    logger.info(
        "optimize: status=%s solver=%s time=%dms cost=%d",
        result.status.value,
        result.solver,
        elapsed_ms,
        result.total_cost_won,
    )
    return result


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe — FastAPI가 살아있으면 OK."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    """Readiness probe — 그래프 + 솔버 초기화 완료 여부."""
    if _graph is None:
        raise HTTPException(status_code=503, detail="Graph not loaded")
    if _solver is None:
        raise HTTPException(status_code=503, detail="Solver not initialized")
    return {
        "status": "ok",
        "solver": _solver.name,
        "nodes": str(len(_graph.virtual_nodes)),
        "edges": str(len(_graph.edges)),
    }


@app.get("/meta/version")
def meta_version() -> dict[str, str]:
    """엔진 버전 및 메타 정보."""
    from . import __version__

    return {
        "version": __version__,
        "solver": _solver.name if _solver else "not initialized",
    }
