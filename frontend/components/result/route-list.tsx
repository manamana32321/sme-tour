"use client";

import { useRef } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RouteEdgeCard } from "./route-edge-card";
import type { RouteEdge } from "@/lib/schemas";

export function RouteList({ edges }: { edges: RouteEdge[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: edges.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,
    overscan: 5,
  });

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">📍 경로 상세 ({edges.length} steps)</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 p-0 overflow-hidden">
        <div
          ref={parentRef}
          className="h-[500px] overflow-auto"
        >
          <div
            style={{ height: `${virtualizer.getTotalSize()}px`, width: "100%", position: "relative" }}
          >
            {virtualizer.getVirtualItems().map((virtualItem) => (
              <div
                key={virtualItem.key}
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "100%",
                  transform: `translateY(${virtualItem.start}px)`,
                }}
              >
                <RouteEdgeCard edge={edges[virtualItem.index]} index={virtualItem.index} />
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
