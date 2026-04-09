"""Graph 빌더 유닛 테스트.

mini fixtures (3 hubs + 2 internal cities)로 노드/에지 생성 로직을
결정론적으로 검증한다. 실제 데이터(Airplane/city dataset.csv)는
`test_data_loader.py`(Task 7)에서 통합 검증.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.graph import Edge, Graph, build_graph

FIXTURES = Path(__file__).parent / "fixtures"
MINI_AIR = FIXTURES / "mini_air.csv"
MINI_CITY = FIXTURES / "mini_city.csv"


@pytest.fixture(scope="module")
def mini_graph() -> Graph:
    return build_graph(MINI_AIR, MINI_CITY)


class TestHubsAndCities:
    def test_hubs_extracted_from_air_csv(self, mini_graph: Graph) -> None:
        assert mini_graph.hubs == {"CDG", "FCO", "AMS"}

    def test_internal_cities_exclude_hubs(self, mini_graph: Graph) -> None:
        assert mini_graph.internal_cities == {"NCE_City", "MIL_City"}

    def test_virtual_nodes_contain_entry_exit_for_each_hub(self, mini_graph: Graph) -> None:
        for iata in ("CDG", "FCO", "AMS"):
            assert f"{iata}_Entry" in mini_graph.virtual_nodes
            assert f"{iata}_Exit" in mini_graph.virtual_nodes

    def test_virtual_nodes_contain_internal_cities(self, mini_graph: Graph) -> None:
        assert "NCE_City" in mini_graph.virtual_nodes
        assert "MIL_City" in mini_graph.virtual_nodes

    def test_virtual_nodes_total_count(self, mini_graph: Graph) -> None:
        # 3 hubs × 2 (Entry/Exit) + 2 internal cities = 8
        assert len(mini_graph.virtual_nodes) == 8


class TestEdges:
    def test_air_edges_count(self, mini_graph: Graph) -> None:
        """mini_air.csv에 6행 — 모두 Air_TEST_x 에지."""
        air_edges = mini_graph.edges_by_category("air")
        assert len(air_edges) == 6

    def test_air_edges_use_exit_to_entry_pattern(self, mini_graph: Graph) -> None:
        for e in mini_graph.edges_by_category("air"):
            assert e.u.endswith("_Exit"), f"air edge u must end with _Exit: {e.u}"
            assert e.v.endswith("_Entry"), f"air edge v must end with _Entry: {e.v}"

    def test_ground_edges_count(self, mini_graph: Graph) -> None:
        """mini_city.csv에 4행 — hub→city / city→hub 각 2쌍."""
        ground_edges = mini_graph.edges_by_category("ground")
        assert len(ground_edges) == 4

    def test_ground_hub_to_city_uses_entry(self, mini_graph: Graph) -> None:
        """CDG → NCE_City 는 CDG_Entry → NCE_City 로 변환되어야."""
        edges = [
            e for e in mini_graph.edges_by_category("ground")
            if e.u == "CDG_Entry" and e.v == "NCE_City"
        ]
        assert len(edges) == 1

    def test_ground_city_to_hub_uses_exit(self, mini_graph: Graph) -> None:
        """NCE_City → CDG 는 NCE_City → CDG_Exit 로 변환."""
        edges = [
            e for e in mini_graph.edges_by_category("ground")
            if e.u == "NCE_City" and e.v == "CDG_Exit"
        ]
        assert len(edges) == 1

    def test_hub_stay_edges_auto_generated(self, mini_graph: Graph) -> None:
        """모든 허브에 Entry→Exit 통과 에지가 자동 추가."""
        stay = mini_graph.edges_by_category("hub_stay")
        assert len(stay) == 3  # 3 hubs
        for e in stay:
            assert e.cost_scaled == 0.0
            assert e.time_minutes == 0
            assert e.mode == "Hub_Stay"

    def test_total_edge_count(self, mini_graph: Graph) -> None:
        # 6 air + 4 ground + 3 hub_stay = 13
        assert len(mini_graph.edges) == 13

    def test_all_edges_have_valid_category(self, mini_graph: Graph) -> None:
        valid = {"air", "ground", "hub_stay"}
        for e in mini_graph.edges:
            assert e.category in valid


class TestScaleFactor:
    def test_default_scale_factor(self, mini_graph: Graph) -> None:
        assert mini_graph.scale_factor == 10_000

    def test_air_cost_is_scaled(self, mini_graph: Graph) -> None:
        """CDG_Exit → FCO_Entry 에지는 원본 300000원 → 30.0."""
        edges = [
            e for e in mini_graph.edges
            if e.u == "CDG_Exit" and e.v == "FCO_Entry"
        ]
        assert len(edges) == 1
        assert edges[0].cost_scaled == pytest.approx(30.0)

    def test_ground_cost_is_scaled(self, mini_graph: Graph) -> None:
        """CDG_Entry → NCE_City 는 원본 50000원 → 5.0."""
        edges = [
            e for e in mini_graph.edges
            if e.u == "CDG_Entry" and e.v == "NCE_City"
        ]
        assert edges[0].cost_scaled == pytest.approx(5.0)

    def test_custom_scale_factor(self) -> None:
        g = build_graph(MINI_AIR, MINI_CITY, scale_factor=1000)
        edges = [e for e in g.edges if e.u == "CDG_Exit" and e.v == "FCO_Entry"]
        assert edges[0].cost_scaled == pytest.approx(300.0)


class TestEdgeUniqueness:
    def test_no_duplicate_edge_keys(self, mini_graph: Graph) -> None:
        """(u, v, mode) 삼중 키는 유일해야 한다."""
        keys = [(e.u, e.v, e.mode) for e in mini_graph.edges]
        assert len(keys) == len(set(keys))


class TestCategorize:
    """_categorize 동작 — 직접 에지를 만들어 dataclass validation 확인."""

    def test_edge_is_immutable(self) -> None:
        e = Edge(u="A", v="B", mode="Air_X", category="air", cost_scaled=1.0, time_minutes=60)
        with pytest.raises(Exception):  # frozen dataclass → FrozenInstanceError
            e.cost_scaled = 2.0  # type: ignore[misc]
