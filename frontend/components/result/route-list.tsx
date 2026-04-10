"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RouteEdgeCard } from "./route-edge-card";
import type { RouteEdge } from "@/lib/schemas";

interface RouteListProps {
  edges: RouteEdge[];
  totalCost: number;
  activeIndex: number | null;
  openIndex: number | null;
  onActiveChange: (index: number | null) => void;
  onOpenChange: (index: number | null) => void;
}

export function RouteList({ edges, totalCost, activeIndex, openIndex, onActiveChange, onOpenChange }: RouteListProps) {
  const cumulative = useMemo(() => {
    let cost = 0;
    let time = 0;
    return edges.map((e) => {
      cost += e.cost_won;
      time += e.time_minutes;
      return { cost, time };
    });
  }, [edges]);

  function handleToggle(index: number) {
    const nextOpen = openIndex === index ? null : index;
    onOpenChange(nextOpen);
    onActiveChange(nextOpen);
  }

  function handleHover(index: number | null) {
    if (openIndex !== null) return;
    onActiveChange(index);
  }

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">📍 경로 상세 ({edges.length} steps)</CardTitle>
      </CardHeader>
      <CardContent className="p-0 max-h-[600px] overflow-auto">
        {edges.map((edge, i) => (
          <RouteEdgeCard
            key={i}
            edge={edge}
            index={i}
            cumulativeCost={cumulative[i].cost}
            cumulativeTime={cumulative[i].time}
            totalCost={totalCost}
            totalEdges={edges.length}
            isActive={activeIndex === i}
            isOpen={openIndex === i}
            onToggle={handleToggle}
            onHover={handleHover}
          />
        ))}
      </CardContent>
    </Card>
  );
}
