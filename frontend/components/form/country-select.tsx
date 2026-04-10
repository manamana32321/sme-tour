"use client";

import { HUB_LIST } from "@/lib/hubs";

interface CountrySelectProps {
  value: string[] | null;
  onChange: (countries: string[] | null) => void;
}

export function CountrySelect({ value, onChange }: CountrySelectProps) {
  const selected = value ? new Set(value) : new Set(HUB_LIST.map((h) => h.iata));
  const allSelected = selected.size === HUB_LIST.length;

  function toggle(iata: string) {
    const next = new Set(selected);
    if (next.has(iata)) {
      next.delete(iata);
    } else {
      next.add(iata);
    }
    // 전부 선택이면 null (기본값 = 전체)
    onChange(next.size === HUB_LIST.length ? null : Array.from(next));
  }

  function toggleAll() {
    onChange(allSelected ? [] : null);
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">방문 국가</label>
        <button
          type="button"
          onClick={toggleAll}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          {allSelected ? "전체 해제" : "전체 선택"}
        </button>
      </div>
      <div className="grid grid-cols-3 gap-1">
        {HUB_LIST.map((hub) => {
          const checked = selected.has(hub.iata);
          return (
            <button
              key={hub.iata}
              type="button"
              onClick={() => toggle(hub.iata)}
              className={`text-xs px-2 py-1.5 rounded border transition-colors text-left truncate ${
                checked
                  ? "bg-primary/10 border-primary/30 text-foreground"
                  : "bg-muted/30 border-transparent text-muted-foreground"
              }`}
            >
              {hub.flag} {hub.city_kr}
            </button>
          );
        })}
      </div>
      <p className="text-xs text-muted-foreground text-center">
        {selected.size}/{HUB_LIST.length}개국 선택
      </p>
    </div>
  );
}
