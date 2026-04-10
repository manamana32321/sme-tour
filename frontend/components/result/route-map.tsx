"use client";

import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { HUBS } from "@/lib/hubs";
import type { RouteEdge } from "@/lib/schemas";

interface RouteMapProps {
  edges: RouteEdge[];
  visitedIata: string[];
}

/** 허브 노드에서 좌표 추출. `{IATA}_Entry` / `{IATA}_Exit` → HUBS 좌표. */
function hubCoord(node: string): [number, number] | null {
  const m = node.match(/^([A-Z]{3})_(Entry|Exit)$/);
  if (m) {
    const hub = HUBS[m[1]];
    return hub ? [hub.lat, hub.lon] : null;
  }
  return null;
}

/**
 * 경로 에지에서 내륙 도시 → 소속 허브 좌표 매핑을 구축한다.
 * 엔진의 Chisman 군집 연속성에 의해 내륙 도시는 항상 같은 허브의
 * Entry/Exit 사이에 위치하므로, 인접 에지에서 허브를 추론할 수 있다.
 */
function buildCityCoordMap(edges: RouteEdge[]): Map<string, [number, number]> {
  const cityCoords = new Map<string, [number, number]>();

  for (const edge of edges) {
    // hub → city: from이 허브면 to(도시)에 허브 좌표 부여
    const fromHub = hubCoord(edge.from_node);
    if (fromHub && !hubCoord(edge.to_node)) {
      cityCoords.set(edge.to_node, fromHub);
    }
    // city → hub: to가 허브면 from(도시)에 허브 좌표 부여
    const toHub = hubCoord(edge.to_node);
    if (toHub && !hubCoord(edge.from_node)) {
      if (!cityCoords.has(edge.from_node)) {
        cityCoords.set(edge.from_node, toHub);
      }
    }
  }
  return cityCoords;
}

const AIR_COLOR = "#3b82f6"; // blue-500
const GROUND_COLOR = "#f97316"; // orange-500

export function RouteMap({ edges, visitedIata }: RouteMapProps) {
  const cityCoords = buildCityCoordMap(edges);

  /** 노드 좌표: 허브 → HUBS에서 직접, 내륙 도시 → 소속 허브 좌표(근사). */
  function nodeCoord(node: string): [number, number] | null {
    return hubCoord(node) ?? cityCoords.get(node) ?? null;
  }

  const airLines: [number, number][][] = [];
  const groundLines: [number, number][][] = [];

  for (const edge of edges) {
    if (edge.category === "hub_stay") continue;
    const from = nodeCoord(edge.from_node);
    const to = nodeCoord(edge.to_node);
    if (!from || !to) continue;
    if (from[0] === to[0] && from[1] === to[1]) continue; // 같은 좌표면 skip

    if (edge.category === "air") {
      airLines.push([from, to]);
    } else {
      groundLines.push([from, to]);
    }
  }

  // 허브 마커 (방문 여부로 색상 구분)
  const hubMarkers = Object.values(HUBS).map((hub) => ({
    ...hub,
    visited: visitedIata.includes(hub.iata),
  }));

  return (
    <MapContainer
      center={[48.5, 10]}
      zoom={4}
      className="h-[500px] w-full rounded-lg"
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://carto.com">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/voyager/{z}/{x}/{y}{r}.png"
      />

      {/* 항공 경로 (파란색 실선) */}
      {airLines.map((line, i) => (
        <Polyline key={`air-${i}`} positions={line} color={AIR_COLOR} weight={2} opacity={0.7} />
      ))}

      {/* 지상 경로 (주황색 점선) */}
      {groundLines.map((line, i) => (
        <Polyline key={`gnd-${i}`} positions={line} color={GROUND_COLOR} weight={2} opacity={0.5} dashArray="6 4" />
      ))}

      {/* 허브 마커 */}
      {hubMarkers.map((hub) => (
        <CircleMarker
          key={hub.iata}
          center={[hub.lat, hub.lon]}
          radius={hub.visited ? 7 : 4}
          fillColor={hub.visited ? AIR_COLOR : "#94a3b8"}
          fillOpacity={hub.visited ? 0.9 : 0.4}
          color={hub.visited ? AIR_COLOR : "#94a3b8"}
          weight={1}
        >
          <Tooltip direction="top" offset={[0, -8]}>
            {hub.flag} {hub.iata} · {hub.city_kr}
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
