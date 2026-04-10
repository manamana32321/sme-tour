"use client";

import { useState } from "react";
import { formatKRW, formatEdgeDuration } from "@/lib/format";
import { formatNode, formatMode, nodeCountry } from "@/lib/node-label";
import type { RouteEdge } from "@/lib/schemas";

interface RouteEdgeCardProps {
  edge: RouteEdge;
  index: number;
  cumulativeCost: number;
  cumulativeTime: number;
  totalCost: number;
  totalEdges: number;
  onHover: (index: number | null) => void;
}

export function RouteEdgeCard({
  edge,
  index,
  cumulativeCost,
  cumulativeTime,
  totalCost,
  totalEdges,
  onHover,
}: RouteEdgeCardProps) {
  const [open, setOpen] = useState(false);
  const mode = formatMode(edge.mode);
  const costRatio = totalCost > 0 ? ((edge.cost_won / totalCost) * 100).toFixed(1) : "0";

  return (
    <div className="border-b last:border-b-0">
      {/* 트리거 (호버 + 클릭) — 이벤트는 여기에만 */}
      <div
        className="flex items-center gap-3 py-2.5 px-3 cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={() => setOpen(!open)}
        onMouseEnter={() => onHover(index)}
        onMouseLeave={() => onHover(null)}
      >
        <span className="text-xs text-muted-foreground w-6 text-right tabular-nums shrink-0">
          {String(index + 1).padStart(2, "0")}
        </span>
        <span className="text-base shrink-0">{mode.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate">
            {formatNode(edge.from_node)} → {formatNode(edge.to_node)}
          </div>
          <div className="text-xs text-muted-foreground">{mode.label}</div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-sm tabular-nums">{formatKRW(edge.cost_won)}</div>
          <div className="text-xs text-muted-foreground tabular-nums">
            {formatEdgeDuration(edge.time_minutes)}
          </div>
        </div>
        <span className="text-xs text-muted-foreground shrink-0">{open ? "▲" : "▼"}</span>
      </div>

      {/* 바디 (이벤트 없음) */}
      {open && (
        <div className="px-3 pb-3 pt-1 ml-9 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs border-t border-dashed">
          <Detail label="교통수단" value={`${mode.icon} ${mode.label}`} />
          <Detail label="비용 비율" value={`전체의 ${costRatio}%`} />
          <Detail
            label="누적 비용"
            value={`${formatKRW(cumulativeCost)} (${totalCost > 0 ? ((cumulativeCost / totalCost) * 100).toFixed(0) : 0}%)`}
          />
          <Detail label="누적 시간" value={formatEdgeDuration(cumulativeTime)} />
          <CountryDetail from={edge.from_node} to={edge.to_node} />
          <Detail label="구간" value={`${totalEdges}개 중 ${index + 1}번째`} />
        </div>
      )}
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <>
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </>
  );
}

function CountryDetail({ from, to }: { from: string; to: string }) {
  const fc = nodeCountry(from);
  const tc = nodeCountry(to);
  if (fc && tc && fc.country_kr !== tc.country_kr) {
    return <Detail label="국가 이동" value={`${fc.flag} ${fc.country_kr} → ${tc.flag} ${tc.country_kr}`} />;
  }
  if (fc) {
    return <Detail label="국가" value={`${fc.flag} ${fc.country_kr}`} />;
  }
  return null;
}
