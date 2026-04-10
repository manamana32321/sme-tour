"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { HUB_LIST } from "@/lib/hubs";

interface CountrySelectProps {
  value: string[] | null;
  onApply: (countries: string[] | null) => void;
}

export function CountrySelect({ value, onApply }: CountrySelectProps) {
  const allIatas = HUB_LIST.map((h) => h.iata);
  const [draft, setDraft] = useState<Set<string>>(new Set(value ?? allIatas));
  const committed = value ?? allIatas;
  const allSelected = draft.size === allIatas.length;
  const isDirty = JSON.stringify([...draft].sort()) !== JSON.stringify([...committed].sort());

  function toggle(iata: string) {
    setDraft((prev) => {
      const next = new Set(prev);
      if (next.has(iata)) next.delete(iata);
      else next.add(iata);
      return next;
    });
  }

  function handleApply() {
    onApply(draft.size === allIatas.length ? null : [...draft]);
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">방문 국가</label>
        <Button
          variant="ghost"
          size="sm"
          className="h-auto py-0.5 px-1.5 text-xs"
          onClick={() => setDraft(new Set(allSelected ? [] : allIatas))}
        >
          {allSelected ? "전체 해제" : "전체 선택"}
        </Button>
      </div>
      <div className="flex flex-wrap gap-1">
        {HUB_LIST.map((hub) => {
          const on = draft.has(hub.iata);
          return (
            <Button
              key={hub.iata}
              variant={on ? "default" : "outline"}
              size="sm"
              className="text-xs h-7 px-2 transition-all hover:scale-105"
              onClick={() => toggle(hub.iata)}
            >
              {hub.flag} {hub.city_kr}
            </Button>
          );
        })}
      </div>
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {draft.size}/{allIatas.length}개국
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
