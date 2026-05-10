"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HUBS, IATA_CODES } from "@/lib/hubs";
import { citiesByHub, INTERNAL_CITIES } from "@/lib/cities";
import { cn } from "@/lib/utils";

interface CitySelectProps {
  value: string[] | null;
  onApply: (cities: string[] | null) => void;
}

export function CitySelect({ value, onApply }: CitySelectProps) {
  const allCities = INTERNAL_CITIES.map((c) => c.node);
  const [draft, setDraft] = useState<Set<string>>(new Set(value ?? []));
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const committed = value ?? [];
  const isDirty =
    JSON.stringify([...draft].sort()) !== JSON.stringify([...committed].sort());

  function toggleCity(node: string) {
    setDraft((prev) => {
      const next = new Set(prev);
      if (next.has(node)) next.delete(node);
      else next.add(node);
      return next;
    });
  }

  function toggleHub(hub: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(hub)) next.delete(hub);
      else next.add(hub);
      return next;
    });
  }

  function handleApply() {
    onApply(draft.size === 0 ? null : [...draft]);
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">방문 필수 도시 (선택)</label>
      </div>
      <div className="space-y-1">
        {IATA_CODES.map((iata) => {
          const hub = HUBS[iata];
          const cities = citiesByHub(iata);
          if (cities.length === 0) return null;
          const isOpen = expanded.has(iata);
          const selectedCount = cities.filter((c) => draft.has(c.node)).length;
          return (
            <div key={iata} className="border border-border/50 rounded">
              <button
                type="button"
                onClick={() => toggleHub(iata)}
                className={cn(
                  "w-full flex items-center gap-1.5 px-2 py-1 text-xs hover:bg-accent/50 transition-colors rounded",
                  selectedCount > 0 && "bg-accent/20",
                )}
              >
                {isOpen ? (
                  <ChevronDown className="size-3 shrink-0" />
                ) : (
                  <ChevronRight className="size-3 shrink-0" />
                )}
                <span className="flex-1 text-left">
                  {hub.flag} {hub.country_kr}
                </span>
                {selectedCount > 0 && (
                  <span className="text-muted-foreground">
                    {selectedCount}/{cities.length}
                  </span>
                )}
              </button>
              {isOpen && (
                <div className="px-2 pb-1.5 flex flex-wrap gap-1">
                  {cities.map((c) => {
                    const on = draft.has(c.node);
                    return (
                      <Button
                        key={c.node}
                        variant={on ? "default" : "outline"}
                        size="sm"
                        className="text-xs h-6 px-1.5"
                        onClick={() => toggleCity(c.node)}
                      >
                        {c.city_kr}
                      </Button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {draft.size}/{allCities.length}개 도시
        </p>
        <Button
          size="sm"
          onClick={handleApply}
          disabled={!isDirty}
          className="text-xs h-7"
        >
          적용
        </Button>
      </div>
    </div>
  );
}
