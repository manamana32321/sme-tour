"""솔버 독립 그래프 빌더.

두 CSV 파일(Airplane dataset + city dataset)을 읽어 가상 노드 그래프를
구축합니다. 이 모듈은 Gurobi/OR-Tools/기타 솔버에 관계없이 동일한
`Graph` 객체를 반환하므로, 솔버 포팅 시 이 레이어는 수정이 불필요합니다.

### 가상 노드 구조 (Chisman 1975, 군집 연속성)
- 허브 공항은 `{IATA}_Entry` / `{IATA}_Exit` 두 개의 가상 노드로 분할
- 내륙 도시는 단일 노드 (`{CityName}_City` 등, CSV의 원본 이름 유지)

### 에지 종류
1. **Air** (국가 간 항공): `{origin}_Exit → {dest}_Entry`
2. **Ground** (국가 내 지상):
   - hub → city: `{hub}_Entry → city`
   - city → hub: `city → {hub}_Exit`
   - city → city: `city → city`
3. **Hub_Stay** (공항 내 경유): `{hub}_Entry → {hub}_Exit` (cost=0, time=0)
   — 방문한 적 없는 국가를 건너뛰게 하는 자동 생성 에지

### 비용 스케일링
원본 KRW 값이 수십만~수백만이라 MIP solver의 numerical stability를 위해
`scale_factor`(기본 10_000)로 나눠 저장. 결과 변환 시 다시 곱해야 함.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pandas as pd

EdgeCategory = Literal["air", "ground", "hub_stay"]


@dataclass(frozen=True)
class Edge:
    """단일 에지. `(u, v, mode)` 삼중 키로 고유하게 식별된다."""

    u: str
    """출발 가상 노드 (예: 'CDG_Exit', 'NCE_City')."""

    v: str
    """도착 가상 노드."""

    mode: str
    """이동 수단 태그: 'Air_{carrier}' | 'Ground_{transport}' | 'Hub_Stay'."""

    category: EdgeCategory
    """UI 아이콘 결정 + 집계용 프리계산 카테고리."""

    cost_scaled: float
    """비용 (KRW) ÷ scale_factor. 솔버 입력용."""

    time_minutes: int
    """소요 시간 (분)."""


@dataclass
class Graph:
    """전체 가상 그래프. 솔버에 전달될 유일한 입력 구조."""

    hubs: set[str] = field(default_factory=set)
    """허브 IATA 코드 집합 (예: {'CDG', 'FCO'})."""

    internal_cities: set[str] = field(default_factory=set)
    """내륙 도시 노드 이름 집합 (예: {'NCE_City', 'Brno_City'})."""

    virtual_nodes: list[str] = field(default_factory=list)
    """전체 가상 노드 (hub_Entry, hub_Exit, city 모두 포함)."""

    edges: list[Edge] = field(default_factory=list)
    """전체 에지 리스트."""

    city_to_hub: dict[str, str] = field(default_factory=dict)
    """내륙 도시 → 소속 허브 IATA 매핑 (예: {'NCE_City': 'CDG'})."""

    scale_factor: int = 10_000
    """비용 정규화 인자. 솔버 결과 해석 시 되돌려 곱해야 함."""

    def edges_by_category(self, category: EdgeCategory) -> list[Edge]:
        """카테고리별 에지 필터. 테스트/디버깅용."""
        return [e for e in self.edges if e.category == category]


def _categorize(mode: str) -> EdgeCategory:
    """`mode` prefix 기반 카테고리 결정."""
    if mode.startswith("Air_"):
        return "air"
    if mode.startswith("Ground_"):
        return "ground"
    if mode == "Hub_Stay":
        return "hub_stay"
    raise ValueError(f"Unknown mode prefix: {mode!r}")


def build_graph(
    airplane_csv: Path | str,
    city_csv: Path | str,
    scale_factor: int = 10_000,
) -> Graph:
    """두 CSV에서 가상 노드 그래프를 빌드한다.

    Args:
        airplane_csv: Airplane dataset.csv 경로. 필수 컬럼: origin_iata,
            dest_iata, carriers, price_eur_won, duration_minutes
        city_csv: city dataset.csv 경로. 필수 컬럼: origin_node,
            destination_node, transport_mode, price_won, duration_min
        scale_factor: 비용 정규화 인자. 기본 10_000.

    Returns:
        완전히 빌드된 `Graph` 객체.

    Raises:
        FileNotFoundError: CSV 파일이 없을 때.
        KeyError: 필수 컬럼이 누락되었을 때 (pandas가 에러 발생).
    """
    air_df = pd.read_csv(airplane_csv)
    city_df = pd.read_csv(city_csv)

    # 1) 허브/내륙 도시 분류
    hubs: set[str] = set(air_df["origin_iata"]) | set(air_df["dest_iata"])
    all_city_nodes: set[str] = set(city_df["origin_node"]) | set(city_df["destination_node"])
    internal_cities: set[str] = all_city_nodes - hubs

    # 2) 가상 노드 목록
    virtual_nodes: list[str] = []
    for h in sorted(hubs):
        virtual_nodes.extend([f"{h}_Entry", f"{h}_Exit"])
    virtual_nodes.extend(sorted(internal_cities))

    # 3) 에지 구축. `edges_seen` 은 중복 방지용 (동일 u,v,mode 삼중 키는 한 번만).
    edges: list[Edge] = []
    edges_seen: set[tuple[str, str, str]] = set()

    def _add(u: str, v: str, mode: str, cost_won: float, time_minutes: int) -> None:
        key = (u, v, mode)
        if key in edges_seen:
            return
        edges_seen.add(key)
        edges.append(
            Edge(
                u=u,
                v=v,
                mode=mode,
                category=_categorize(mode),
                cost_scaled=cost_won / scale_factor,
                time_minutes=int(time_minutes),
            )
        )

    # 3a) 항공 에지: {origin}_Exit → {dest}_Entry
    for _, row in air_df.iterrows():
        u = f"{row['origin_iata']}_Exit"
        v = f"{row['dest_iata']}_Entry"
        mode = f"Air_{row['carriers']}"
        _add(u, v, mode, float(row["price_eur_won"]), int(row["duration_minutes"]))

    # 3b) 지상 에지: Chisman 군집 연속성 반영
    for _, row in city_df.iterrows():
        u_raw = row["origin_node"]
        v_raw = row["destination_node"]
        if u_raw in hubs and v_raw in internal_cities:
            u_node, v_node = f"{u_raw}_Entry", v_raw
        elif u_raw in internal_cities and v_raw in hubs:
            u_node, v_node = u_raw, f"{v_raw}_Exit"
        elif u_raw in internal_cities and v_raw in internal_cities:
            u_node, v_node = u_raw, v_raw
        else:
            # hub↔hub, hub 자기 자신, 기타 케이스는 항공 에지가 담당하므로 skip
            continue
        mode = f"Ground_{row['transport_mode']}"
        _add(u_node, v_node, mode, float(row["price_won"]), int(row["duration_min"]))

    # 3c) Hub_Stay: 모든 허브에 Entry → Exit 직결 (cost=0, time=0)
    for h in sorted(hubs):
        _add(f"{h}_Entry", f"{h}_Exit", "Hub_Stay", 0.0, 0)

    # 4) 내륙 도시 → 소속 허브 매핑 (city_csv에서 hub→city 관계 추출)
    city_to_hub: dict[str, str] = {}
    for _, row in city_df.iterrows():
        u_raw, v_raw = row["origin_node"], row["destination_node"]
        if u_raw in hubs and v_raw in internal_cities:
            city_to_hub.setdefault(v_raw, u_raw)
        elif u_raw in internal_cities and v_raw in hubs:
            city_to_hub.setdefault(u_raw, v_raw)

    return Graph(
        hubs=hubs,
        internal_cities=internal_cities,
        virtual_nodes=virtual_nodes,
        edges=edges,
        city_to_hub=city_to_hub,
        scale_factor=scale_factor,
    )
