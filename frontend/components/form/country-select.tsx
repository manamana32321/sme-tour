"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Button } from "@/components/ui/button";
import { HUB_LIST } from "@/lib/hubs";

interface CountrySelectProps {
  value: string[] | null;
  onChange: (countries: string[] | null) => void;
}

export function CountrySelect({ value, onChange }: CountrySelectProps) {
  const allIatas = HUB_LIST.map((h) => h.iata);
  const selected = value ?? allIatas;
  const allSelected = selected.length === allIatas.length;

  function handleChange(next: string[]) {
    onChange(next.length === allIatas.length ? null : next);
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">방문 국가</label>
        <Button
          variant="ghost"
          size="sm"
          className="h-auto py-0.5 px-1.5 text-xs"
          onClick={() => onChange(allSelected ? [] : null)}
        >
          {allSelected ? "전체 해제" : "전체 선택"}
        </Button>
      </div>
      <ToggleGroup
        value={selected}
        onValueChange={handleChange}
        className="flex flex-wrap gap-1 justify-start"
      >
        {HUB_LIST.map((hub) => (
          <ToggleGroupItem
            key={hub.iata}
            value={hub.iata}
            size="sm"
            className="text-xs px-2 py-1 h-auto data-[state=on]:bg-primary/10 data-[state=on]:border-primary/30"
          >
            {hub.flag} {hub.city_kr}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
      <p className="text-xs text-muted-foreground text-center">
        {selected.length}/{allIatas.length}개국
      </p>
    </div>
  );
}
