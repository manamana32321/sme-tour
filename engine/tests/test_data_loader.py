"""data_loader 통합 테스트.

실제 프로덕션 CSV(Airplane/city dataset.csv)를 로드해 그래프가
유의미한 크기로 빌드되는지 검증한다.
"""

from __future__ import annotations

import pytest

from src.data_loader import AIRPLANE_CSV, CITY_CSV, load_default_graph


class TestLoadDefaultGraph:
    @pytest.fixture(scope="class")
    def graph(self):
        return load_default_graph()

    def test_csvs_exist(self) -> None:
        assert AIRPLANE_CSV.exists(), f"Missing: {AIRPLANE_CSV}"
        assert CITY_CSV.exists(), f"Missing: {CITY_CSV}"

    def test_hubs_are_15(self, graph) -> None:
        assert len(graph.hubs) == 15

    def test_internal_cities_exist(self, graph) -> None:
        assert len(graph.internal_cities) > 0

    def test_virtual_nodes_count(self, graph) -> None:
        expected_min = 15 * 2 + len(graph.internal_cities)  # 30 hub nodes + cities
        assert len(graph.virtual_nodes) >= expected_min

    def test_has_air_edges(self, graph) -> None:
        air = graph.edges_by_category("air")
        assert len(air) > 100  # 15 hubs → 210 pairs, multiple carriers

    def test_has_ground_edges(self, graph) -> None:
        ground = graph.edges_by_category("ground")
        assert len(ground) > 10

    def test_has_hub_stay_edges(self, graph) -> None:
        stay = graph.edges_by_category("hub_stay")
        assert len(stay) == 15  # one per hub

    def test_scale_factor_default(self, graph) -> None:
        assert graph.scale_factor == 10_000

    def test_filenotfound_on_missing_csv(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_default_graph(airplane_csv="/nonexistent.csv")
