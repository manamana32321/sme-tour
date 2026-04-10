import { categoryIcon, categoryLabel, formatKRW, formatEdgeDuration } from "@/lib/format";
import type { RouteEdge } from "@/lib/schemas";

export function RouteEdgeCard({ edge, index }: { edge: RouteEdge; index: number }) {
  return (
    <div className="flex items-center gap-3 py-2 px-3 border-b last:border-b-0">
      <span className="text-xs text-muted-foreground w-6 text-right tabular-nums">
        {String(index + 1).padStart(2, "0")}
      </span>
      <span className="text-base">{categoryIcon(edge.category)}</span>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">
          {edge.from_node} → {edge.to_node}
        </div>
        <div className="text-xs text-muted-foreground">
          {categoryLabel(edge.category)} · {edge.mode.replace(/^(Air_|Ground_)/, "")}
        </div>
      </div>
      <div className="text-right shrink-0">
        <div className="text-sm tabular-nums">{formatKRW(edge.cost_won)}</div>
        <div className="text-xs text-muted-foreground tabular-nums">{formatEdgeDuration(edge.time_minutes)}</div>
      </div>
    </div>
  );
}
