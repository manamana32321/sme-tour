"use client";

import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { HUBS } from "@/lib/hubs";
import type { RouteEdge } from "@/lib/schemas";

const START_COLOR = "#16a34a"; // green-600

interface RouteMapProps {
  edges: RouteEdge[];
  visitedIata: string[];
  activeIndex: number | null;
  requiredCountries: string[] | null;
  startHub: string;
  onEdgeHover: (index: number | null) => void;
  onEdgeClick: (index: number) => void;
}

function hubCoord(node: string): [number, number] | null {
  const m = node.match(/^([A-Z]{3})_(Entry|Exit)$/);
  if (m) {
    const hub = HUBS[m[1]];
    return hub ? [hub.lat, hub.lon] : null;
  }
  return null;
}

function buildCityCoordMap(edges: RouteEdge[]): Map<string, [number, number]> {
  const cityCoords = new Map<string, [number, number]>();
  for (const edge of edges) {
    const fromHub = hubCoord(edge.from_node);
    if (fromHub && !hubCoord(edge.to_node)) cityCoords.set(edge.to_node, fromHub);
    const toHub = hubCoord(edge.to_node);
    if (toHub && !hubCoord(edge.from_node) && !cityCoords.has(edge.from_node)) {
      cityCoords.set(edge.from_node, toHub);
    }
  }
  return cityCoords;
}

const AIR_COLOR = "#3b82f6";
const GROUND_COLOR = "#f97316";
const HIGHLIGHT_COLOR = "#a855f7";

export function RouteMap({ edges, visitedIata, activeIndex, requiredCountries, startHub, onEdgeClick, onEdgeHover }: RouteMapProps) {
  const cityCoords = buildCityCoordMap(edges);
  const selectedSet = requiredCountries ? new Set(requiredCountries) : null;

  function nodeCoord(node: string): [number, number] | null {
    return hubCoord(node) ?? cityCoords.get(node) ?? null;
  }

  /** 노드가 선택된 국가에 속하는지 */
  function isNodeSelected(node: string): boolean {
    if (!selectedSet) return true; // null = 전체 선택
    const m = node.match(/^([A-Z]{3})_(Entry|Exit)$/);
    if (m) return selectedSet.has(m[1]);
    // 내륙 도시는 visitedIata에 소속 허브가 있으면 표시
    return true; // 엔진 결과에 포함된 도시는 표시
  }

  const lines: { from: [number, number]; to: [number, number]; category: string; index: number }[] = [];
  for (let i = 0; i < edges.length; i++) {
    const edge = edges[i];
    if (edge.category === "hub_stay") continue;
    const from = nodeCoord(edge.from_node);
    const to = nodeCoord(edge.to_node);
    if (!from || !to) continue;
    if (from[0] === to[0] && from[1] === to[1]) continue;
    lines.push({ from, to, category: edge.category, index: i });
  }

  const highlightedNodes = new Set<string>();
  if (activeIndex !== null && edges[activeIndex]) {
    const active = edges[activeIndex];
    if (active.category === "ground") {
      highlightedNodes.add(active.from_node);
      highlightedNodes.add(active.to_node);
    }
  }

  const hubMarkers = Object.values(HUBS)
    .filter((hub) => !selectedSet || selectedSet.has(hub.iata))
    .map((hub) => {
      const isHighlighted =
        highlightedNodes.has(`${hub.iata}_Entry`) || highlightedNodes.has(`${hub.iata}_Exit`);
      const isStart = hub.iata === startHub;
      return { ...hub, visited: visitedIata.includes(hub.iata), isHighlighted, isStart };
    });

  return (
    <MapContainer center={[48.5, 10]} zoom={4} className="h-[500px] w-full rounded-lg" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://carto.com">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
      />

      {lines.map((line) => {
        const isActive = activeIndex === line.index;
        const baseColor = line.category === "air" ? AIR_COLOR : GROUND_COLOR;
        return (
          <span key={`line-${line.index}`}>
            {/* 투명 히트 영역 (클릭 반경 확대) */}
            <Polyline
              positions={[line.from, line.to]}
              pathOptions={{ color: "transparent", weight: 20, opacity: 0 }}
              eventHandlers={{
                click: () => onEdgeClick(line.index),
                mouseover: () => onEdgeHover(line.index),
                mouseout: () => onEdgeHover(null),
              }}
            />
            {/* 실제 표시 에지 */}
            <Polyline
              key={`vis-${line.index}-${isActive}`}
              positions={[line.from, line.to]}
              pathOptions={{
                color: isActive ? HIGHLIGHT_COLOR : baseColor,
                weight: isActive ? 5 : 2,
                opacity: 0.7,
                dashArray: line.category === "ground" && !isActive ? "6 4" : undefined,
              }}
              interactive={false}
            />
          </span>
        );
      })}

      {hubMarkers.map((hub) => {
        const color = hub.isHighlighted
          ? HIGHLIGHT_COLOR
          : hub.isStart
            ? START_COLOR
            : hub.visited ? AIR_COLOR : "#94a3b8";
        return (
          <CircleMarker
            key={`${hub.iata}-${hub.isHighlighted}-${hub.isStart}`}
            center={[hub.lat, hub.lon]}
            radius={hub.isHighlighted ? 10 : hub.isStart ? 9 : hub.visited ? 7 : 4}
            pathOptions={{
              fillColor: color,
              fillOpacity: hub.isHighlighted || hub.isStart ? 1 : hub.visited ? 0.9 : 0.4,
              color,
              weight: hub.isStart ? 3 : hub.isHighlighted ? 2 : 1,
            }}
          >
            <Tooltip direction="top" offset={[0, -8]}>
              {hub.isStart ? "📍 " : ""}{hub.flag} {hub.iata} · {hub.city_kr}
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
