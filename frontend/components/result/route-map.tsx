"use client";

import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { HUBS } from "@/lib/hubs";
import type { RouteEdge } from "@/lib/schemas";

interface RouteMapProps {
  edges: RouteEdge[];
  visitedIata: string[];
  hoveredIndex: number | null;
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
const HIGHLIGHT_COLOR = "#a855f7"; // purple-500

export function RouteMap({ edges, visitedIata, hoveredIndex }: RouteMapProps) {
  const cityCoords = buildCityCoordMap(edges);

  function nodeCoord(node: string): [number, number] | null {
    return hubCoord(node) ?? cityCoords.get(node) ?? null;
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

  // 호버 시 노드 하이라이트: 국가 내 이동(ground)만 from/to 노드 강조
  const highlightedNodes = new Set<string>();
  if (hoveredIndex !== null && edges[hoveredIndex]) {
    const hovered = edges[hoveredIndex];
    if (hovered.category === "ground") {
      highlightedNodes.add(hovered.from_node);
      highlightedNodes.add(hovered.to_node);
    }
  }

  const hubMarkers = Object.values(HUBS).map((hub) => {
    const isHighlighted =
      highlightedNodes.has(`${hub.iata}_Entry`) || highlightedNodes.has(`${hub.iata}_Exit`);
    return { ...hub, visited: visitedIata.includes(hub.iata), isHighlighted };
  });

  return (
    <MapContainer center={[48.5, 10]} zoom={4} className="h-[500px] w-full rounded-lg" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://carto.com">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
      />

      {lines.map((line) => {
        const isHovered = hoveredIndex === line.index;
        const baseColor = line.category === "air" ? AIR_COLOR : GROUND_COLOR;
        return (
          <Polyline
            key={`line-${line.index}`}
            positions={[line.from, line.to]}
            color={isHovered ? HIGHLIGHT_COLOR : baseColor}
            weight={isHovered ? 5 : 2}
            opacity={isHovered ? 1 : hoveredIndex !== null ? 0.15 : 0.7}
            dashArray={line.category === "ground" && !isHovered ? "6 4" : undefined}
          />
        );
      })}

      {hubMarkers.map((hub) => (
        <CircleMarker
          key={hub.iata}
          center={[hub.lat, hub.lon]}
          radius={hub.isHighlighted ? 10 : hub.visited ? 7 : 4}
          fillColor={hub.isHighlighted ? HIGHLIGHT_COLOR : hub.visited ? AIR_COLOR : "#94a3b8"}
          fillOpacity={hub.isHighlighted ? 1 : hub.visited ? 0.9 : 0.4}
          color={hub.isHighlighted ? HIGHLIGHT_COLOR : hub.visited ? AIR_COLOR : "#94a3b8"}
          weight={hub.isHighlighted ? 2 : 1}
        >
          <Tooltip direction="top" offset={[0, -8]}>
            {hub.flag} {hub.iata} · {hub.city_kr}
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
