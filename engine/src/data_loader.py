"""기본 데이터 로더.

``engine/data/processed/`` 의 CSV 파일을 읽어 ``Graph`` 를 빌드한다.
FastAPI 앱 시작 시 1회 호출되어 메모리에 상주하는 그래프를 생성한다.
"""

from __future__ import annotations

from pathlib import Path

from .graph import Graph, build_graph

_DATA_DIR = Path(__file__).parent.parent / "data" / "processed"

AIRPLANE_CSV = _DATA_DIR / "Airplane dataset.csv"
CITY_CSV = _DATA_DIR / "city dataset.csv"


def load_default_graph(
    airplane_csv: Path | str = AIRPLANE_CSV,
    city_csv: Path | str = CITY_CSV,
) -> Graph:
    """프로덕션 데이터로 그래프를 빌드한다.

    Args:
        airplane_csv: 항공편 CSV 경로. 기본값은 ``engine/data/processed/Airplane dataset.csv``.
        city_csv: 도시 CSV 경로. 기본값은 ``engine/data/processed/city dataset.csv``.

    Returns:
        완전히 빌드된 ``Graph`` 객체.

    Raises:
        FileNotFoundError: CSV 파일이 존재하지 않을 때.
    """
    airplane_path = Path(airplane_csv)
    city_path = Path(city_csv)

    if not airplane_path.exists():
        raise FileNotFoundError(f"Airplane CSV not found: {airplane_path}")
    if not city_path.exists():
        raise FileNotFoundError(f"City CSV not found: {city_path}")

    return build_graph(airplane_path, city_path)
