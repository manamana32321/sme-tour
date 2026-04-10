"use client";

import { useState } from "react";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Button } from "@/components/ui/button";
import { HUB_LIST } from "@/lib/hubs";

interface CountrySelectProps {
  value: string[] | null;
  onApply: (countries: string[] | null) => void;
}

export function CountrySelect({ value, onApply }: CountrySelectProps) {
  const allIatas = HUB_LIST.map((h) => h.iata);
  const [draft, setDraft] = useState<string[]>(value ?? allIatas);
  const committed = value ?? allIatas;
  const allSelected = draft.length === allIatas.length;
  const isDirty = JSON.stringify([...draft].sort()) !== JSON.stringify([...committed].sort());

  function handleApply() {
    onApply(draft.length === allIatas.length ? null : draft);
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">방문 국가</label>
        <Button
          variant="ghost"
          size="sm"
          className="h-auto py-0.5 px-1.5 text-xs"
          onClick={() => setDraft(allSelected ? [] : [...allIatas])}
        >
          {allSelected ? "전체 해제" : "전체 선택"}
        </Button>
      </div>
      <ToggleGroup
        value={draft}
        onValueChange={setDraft}
        className="flex flex-wrap gap-1 justify-start"
      >
        {HUB_LIST.map((hub) => (
          <ToggleGroupItem
            key={hub.iata}
            value={hub.iata}
            size="sm"
            className="text-xs px-2 py-1 h-auto transition-all
              data-[state=on]:bg-primary/10 data-[state=on]:border-primary/30
              hover:bg-muted hover:scale-105"
          >
            {hub.flag} {hub.city_kr}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {draft.length}/{allIatas.length}개국
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
