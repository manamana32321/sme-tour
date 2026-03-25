#!/usr/bin/env python3
"""
Sky Scrapper API를 사용하여 15개국 허브 공항 간 항공편 데이터 수집.

사용법:
    python scripts/collect_flights.py --date 2026-07-01
    python scripts/collect_flights.py --date 2026-07-01 --resume  # 이전 중단 지점부터 재개
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from itertools import permutations
from pathlib import Path
from urllib.parse import urlencode

from airports import AIRPORTS

API_HOST = "sky-scrapper.p.rapidapi.com"
BASE_URL = f"https://{API_HOST}/api/v1/flights"
REQUEST_DELAY = 1.5  # 초 (rate limit 대비)
MAX_RETRIES = 3  # 빈 결과 시 재시도 횟수


def load_api_key() -> str:
    """환경변수 또는 .env.local에서 API 키 로드"""
    key = os.environ.get("RAPIDAPI_KEY")
    if key:
        return key

    env_file = Path(__file__).parent.parent / ".env.local"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("RAPIDAPI_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    print("ERROR: RAPIDAPI_KEY not found. Set it in .env.local or environment.")
    sys.exit(1)


def api_get(url: str, params: dict, api_key: str) -> dict:
    """curl을 사용한 API 호출 (WSL2 Python SSL 타임아웃 우회)"""
    query = urlencode(params)
    full_url = f"{url}?{query}"
    result = subprocess.run(
        [
            "curl", "-s", "--max-time", "60",
            "-H", f"x-rapidapi-host: {API_HOST}",
            "-H", f"x-rapidapi-key: {api_key}",
            full_url,
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr}")
    if not result.stdout.strip():
        raise RuntimeError("Empty response from API")
    return json.loads(result.stdout)


def search_airport(iata: str, api_key: str) -> dict | None:
    """공항 IATA 코드로 skyId, entityId 조회"""
    data = api_get(
        f"{BASE_URL}/searchAirport",
        {"query": iata, "locale": "en-US"},
        api_key,
    )
    for item in data.get("data", []):
        nav = item.get("navigation", {})
        if nav.get("entityType") == "AIRPORT":
            return {
                "skyId": item["skyId"],
                "entityId": item["entityId"],
                "name": nav.get("localizedName", ""),
            }
    return None


def resolve_all_airports(api_key: str, raw_dir: Path) -> dict[str, dict]:
    """모든 공항의 skyId/entityId 조회 및 캐시"""
    cache_file = raw_dir / "airport_ids.json"
    if cache_file.exists():
        cached = json.loads(cache_file.read_text())
        if len(cached) == len(AIRPORTS):
            print(f"Cached airport IDs loaded ({len(cached)} airports)")
            return cached

    resolved = {}
    for code, info in AIRPORTS.items():
        iata = info["iata"]
        print(f"  Resolving {iata} ({info['city']})...", end=" ")
        result = search_airport(iata, api_key)
        if result:
            resolved[code] = {**info, **result}
            print(f"OK → skyId={result['skyId']}, entityId={result['entityId']}")
        else:
            print("FAILED")
            sys.exit(1)
        time.sleep(0.5)

    cache_file.write_text(json.dumps(resolved, indent=2, ensure_ascii=False))
    return resolved


def search_flights(origin: dict, destination: dict, date: str, api_key: str) -> dict:
    """두 공항 간 항공편 검색"""
    return api_get(
        f"{BASE_URL}/searchFlights",
        {
            "originSkyId": origin["skyId"],
            "destinationSkyId": destination["skyId"],
            "originEntityId": origin["entityId"],
            "destinationEntityId": destination["entityId"],
            "date": date,
            "adults": "1",
            "currency": "EUR",
        },
        api_key,
    )


def extract_summary(raw_data: dict, origin_code: str, dest_code: str) -> list[dict]:
    """raw API 응답에서 항공편 요약 추출"""
    rows = []
    itineraries = raw_data.get("data", {}).get("itineraries", [])

    for itin in itineraries:
        legs = itin.get("legs", [])
        if not legs:
            continue

        leg = legs[0]
        price_raw = itin.get("price", {}).get("raw", None)
        price_formatted = itin.get("price", {}).get("formatted", "")

        carriers = leg.get("carriers", {}).get("marketing", [])
        carrier_names = [c.get("name", "") for c in carriers]

        segments = leg.get("segments", [])
        stop_count = leg.get("stopCount", 0)

        rows.append({
            "origin_country": origin_code,
            "origin_iata": AIRPORTS[origin_code]["iata"],
            "dest_country": dest_code,
            "dest_iata": AIRPORTS[dest_code]["iata"],
            "departure": leg.get("departure", ""),
            "arrival": leg.get("arrival", ""),
            "duration_minutes": leg.get("durationInMinutes", None),
            "stop_count": stop_count,
            "carriers": ", ".join(carrier_names),
            "price_eur": price_raw,
            "price_formatted": price_formatted,
            "segment_count": len(segments),
            "itinerary_id": itin.get("id", ""),
        })

    return rows


def get_completed_pairs(raw_dir: Path) -> set[tuple[str, str]]:
    """이미 수집 완료된 쌍 조회 (resume 용)"""
    completed = set()
    for f in raw_dir.glob("*.json"):
        if f.name == "airport_ids.json":
            continue
        parts = f.stem.split("_")
        if len(parts) >= 2:
            completed.add((parts[0], parts[1]))
    return completed


def main():
    parser = argparse.ArgumentParser(description="유럽 허브 공항 간 항공편 데이터 수집")
    parser.add_argument("--date", required=True, help="검색 날짜 (YYYY-MM-DD)")
    parser.add_argument("--resume", action="store_true", help="중단된 지점부터 재개")
    args = parser.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: Invalid date format: {args.date} (expected YYYY-MM-DD)")
        sys.exit(1)

    api_key = load_api_key()

    # Setup directories
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw" / args.date
    processed_dir = project_root / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Resolve airport IDs
    print("=== Step 1: Resolving airport IDs ===")
    airports = resolve_all_airports(api_key, raw_dir)

    # Step 2: Generate all ATSP pairs
    country_codes = list(AIRPORTS.keys())
    all_pairs = list(permutations(country_codes, 2))  # 210 pairs
    print(f"\n=== Step 2: Collecting {len(all_pairs)} flight pairs (ATSP) ===")
    print(f"Date: {args.date}")

    # Resume support
    completed = get_completed_pairs(raw_dir) if args.resume else set()
    if completed:
        print(f"Resuming: {len(completed)} pairs already collected, {len(all_pairs) - len(completed)} remaining")

    # Step 3: Collect flight data
    all_summaries: list[dict] = []
    errors: list[dict] = []

    for i, (orig, dest) in enumerate(all_pairs):
        if (orig, dest) in completed:
            raw_file = raw_dir / f"{orig}_{dest}.json"
            if raw_file.exists():
                raw_data = json.loads(raw_file.read_text())
                all_summaries.extend(extract_summary(raw_data, orig, dest))
            continue

        orig_info = airports[orig]
        dest_info = airports[dest]
        pair_label = f"{orig_info['iata']}→{dest_info['iata']}"
        progress = f"[{i + 1}/{len(all_pairs)}]"

        print(f"  {progress} {pair_label} ({orig_info['city']}→{dest_info['city']})...", end=" ", flush=True)

        try:
            raw_data = None
            for attempt in range(1, MAX_RETRIES + 1):
                raw_data = search_flights(orig_info, dest_info, args.date, api_key)
                itinerary_count = len(raw_data.get("data", {}).get("itineraries", []))
                if itinerary_count > 0:
                    break
                if attempt < MAX_RETRIES:
                    print(f"0 results, retry {attempt}/{MAX_RETRIES}...", end=" ", flush=True)
                    time.sleep(2)

            # Save raw response
            raw_file = raw_dir / f"{orig}_{dest}.json"
            raw_file.write_text(json.dumps(raw_data, indent=2, ensure_ascii=False))

            # Extract summary
            summaries = extract_summary(raw_data, orig, dest)
            all_summaries.extend(summaries)

            if summaries:
                cheapest = min(s["price_eur"] for s in summaries if s["price_eur"])
                print(f"OK ({itinerary_count} flights, cheapest €{cheapest:.0f})")
            else:
                print(f"EMPTY ({itinerary_count} flights after {MAX_RETRIES} tries)")

        except Exception as e:
            print(f"ERROR: {e}")
            errors.append({"pair": pair_label, "error": str(e)})
            if "429" in str(e):
                print("  Rate limited! Waiting 60s...")
                time.sleep(60)

        time.sleep(REQUEST_DELAY)

    # Step 4: Write summary CSV
    csv_file = processed_dir / f"flights_{args.date}.csv"
    print(f"\n=== Step 3: Writing summary CSV → {csv_file} ===")

    if all_summaries:
        fieldnames = list(all_summaries[0].keys())
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_summaries)
        print(f"  {len(all_summaries)} rows written")

    # Step 5: Write cost matrix (cheapest per pair)
    matrix_file = processed_dir / f"cost_matrix_{args.date}.csv"
    print(f"\n=== Step 4: Writing cost matrix → {matrix_file} ===")

    cheapest_map: dict[tuple[str, str], dict] = {}
    for s in all_summaries:
        key = (s["origin_country"], s["dest_country"])
        if s["price_eur"] is not None:
            if key not in cheapest_map or s["price_eur"] < cheapest_map[key]["price_eur"]:
                cheapest_map[key] = s

    with open(matrix_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["from\\to"] + [AIRPORTS[c]["iata"] for c in country_codes]
        writer.writerow(header)
        for orig in country_codes:
            row = [AIRPORTS[orig]["iata"]]
            for dest in country_codes:
                if orig == dest:
                    row.append("-")
                else:
                    entry = cheapest_map.get((orig, dest))
                    row.append(f"{entry['price_eur']:.0f}" if entry and entry["price_eur"] else "N/A")
            writer.writerow(row)

    # Duration matrix
    duration_file = processed_dir / f"duration_matrix_{args.date}.csv"
    with open(duration_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for orig in country_codes:
            row = [AIRPORTS[orig]["iata"]]
            for dest in country_codes:
                if orig == dest:
                    row.append("-")
                else:
                    entry = cheapest_map.get((orig, dest))
                    row.append(str(entry["duration_minutes"]) if entry and entry["duration_minutes"] else "N/A")
            writer.writerow(row)

    print(f"  Cost matrix: {len(cheapest_map)} pairs")
    print(f"  Duration matrix: {duration_file}")

    # Report
    print(f"\n=== Done ===")
    print(f"  Total pairs: {len(all_pairs)}")
    print(f"  Successful: {len(all_pairs) - len(errors)}")
    print(f"  Errors: {len(errors)}")
    if errors:
        print("  Failed pairs:")
        for e in errors:
            print(f"    {e['pair']}: {e['error']}")

    print(f"\nOutput files:")
    print(f"  Raw JSON: {raw_dir}/")
    print(f"  All flights CSV: {csv_file}")
    print(f"  Cost matrix: {matrix_file}")
    print(f"  Duration matrix: {duration_file}")


if __name__ == "__main__":
    main()
