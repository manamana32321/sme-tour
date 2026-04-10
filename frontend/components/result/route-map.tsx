"use client";

import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { HUBS } from "@/lib/hubs";
import type { RouteEdge } from "@/lib/schemas";

interface RouteMapProps {
  edges: RouteEdge[];
  visitedIata: string[];
}

/** 노드 이름에서 좌표 추출. 허브는 HUBS에서, 내륙 도시는 가장 가까운 허브 좌표 사용 (근사). */
function nodeCoord(node: string): [number, number] | null {
  // {IATA}_Entry / {IATA}_Exit
  const hubMatch = node.match(/^([A-Z]{3})_(Entry|Exit)$/);
  if (hubMatch) {
    const hub = HUBS[hubMatch[1]];
    return hub ? [hub.lat, hub.lon] : null;
  }
  // 내륙 도시 — HUBS에서 좌표를 못 찾음. null 반환.
  return null;
}

const AIR_COLOR = "#3b82f6"; // blue-500
const GROUND_COLOR = "#f97316"; // orange-500

export function RouteMap({ edges, visitedIata }: RouteMapProps) {
  // 경로 선 좌표 추출 (좌표 없는 노드는 건너뜀)
  const airLines: [number, number][][] = [];
  const groundLines: [number, number][][] = [];

  for (const edge of edges) {
    const from = nodeCoord(edge.from_node);
    const to = nodeCoord(edge.to_node);
    if (!from || !to) continue;
    if (from[0] === to[0] && from[1] === to[1]) continue; // hub_stay skip

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
