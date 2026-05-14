"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { HUBS, IATA_CODES } from "@/lib/hubs";
import { citiesByHub } from "@/lib/cities";
import { cn } from "@/lib/utils";

export type PickerMode = "full" | "select";

interface DestinationPickerProps {
  mode: PickerMode;
  selectedHubs: string[];
  selectedCities: string[];
  stayDays: Record<string, number>;
  onModeChange: (m: PickerMode) => void;
  onSelectedHubsChange: (v: string[]) => void;
  onSelectedCitiesChange: (v: string[]) => void;
  onStayDaysChange: (v: Record<string, number>) => void;
}

export function DestinationPicker({
  mode,
  selectedHubs,
  selectedCities,
  stayDays,
  onModeChange,
  onSelectedHubsChange,
  onSelectedCitiesChange,
  onStayDaysChange,
}: DestinationPickerProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const isSelect = mode === "select";
  const hubSet = new Set(selectedHubs);
  const citySet = new Set(selectedCities);

  function toggleGroup(iata: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(iata)) next.delete(iata);
      else next.add(iata);
      return next;
    });
  }

  function toggleHub(iata: string) {
    const next = new Set(hubSet);
    if (next.has(iata)) next.delete(iata);
    else next.add(iata);
    onSelectedHubsChange([...next]);
  }

  function toggleCity(node: string) {
    const next = new Set(citySet);
    if (next.has(node)) next.delete(node);
    else next.add(node);
    onSelectedCitiesChange([...next]);
  }

  function setDays(node: string, value: string) {
    const days = parseInt(value, 10);
    const clamped = isNaN(days) || days < 0 ? 0 : Math.min(days, 30);
    onStayDaysChange({ ...stayDays, [node]: clamped });
  }

  const totalStay = Object.values(stayDays).reduce((a, b) => a + b, 0);
  const selectedCount = selectedHubs.length + selectedCities.length;

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">방문지 + 체류일</label>

      <div className="flex gap-1">
        <Button
          variant={mode === "full" ? "default" : "outline"}
          size="sm"
          className="flex-1 text-xs h-7"
          onClick={() => onModeChange("full")}
        >
          전체 완주
        </Button>
        <Button
          variant={mode === "select" ? "default" : "outline"}
          size="sm"
          className="flex-1 text-xs h-7"
          onClick={() => onModeChange("select")}
        >
          선택 방문
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        {isSelect
          ? "방문할 곳을 직접 고르세요. 고르지 않은 곳은 경로에 따라 자유 선택됩니다."
          : "15개국 45개 도시를 모두 방문합니다. 아래에서 체류일만 설정하세요."}
      </p>

      <div className="space-y-1">
        {IATA_CODES.map((iata) => {
          const hub = HUBS[iata];
          const cities = citiesByHub(iata);
          const isOpen = expanded.has(iata);
          const groupSelected =
            (hubSet.has(iata) ? 1 : 0) +
            cities.filter((c) => citySet.has(c.node)).length;
          return (
            <div key={iata} className="border border-border/50 rounded">
              <button
                type="button"
                onClick={() => toggleGroup(iata)}
                className={cn(
                  "w-full flex items-center gap-1.5 px-2 py-1 text-xs hover:bg-accent/50 transition-colors rounded",
                  isSelect && groupSelected > 0 && "bg-accent/20",
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
                {isSelect && groupSelected > 0 && (
                  <span className="text-muted-foreground">
                    {groupSelected}/{cities.length + 1}
                  </span>
                )}
              </button>
              {isOpen && (
                <div className="px-2 pb-1.5 space-y-1">
                  <PlaceRow
                    label={`${hub.city_kr} (허브)`}
                    isSelect={isSelect}
                    selected={hubSet.has(iata)}
                    days={stayDays[iata] ?? 0}
                    onToggle={() => toggleHub(iata)}
                    onDaysChange={(v) => setDays(iata, v)}
                  />
                  {cities.map((c) => (
                    <PlaceRow
                      key={c.node}
                      label={c.city_kr}
                      isSelect={isSelect}
                      selected={citySet.has(c.node)}
                      days={stayDays[c.node] ?? 0}
                      onToggle={() => toggleCity(c.node)}
                      onDaysChange={(v) => setDays(c.node, v)}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className="text-xs text-muted-foreground text-center">
        {isSelect ? `${selectedCount}곳 강제 방문` : "45곳 전체"} · 체류일 합계 {totalStay}일
      </p>
    </div>
  );
}

interface PlaceRowProps {
  label: string;
  isSelect: boolean;
  selected: boolean;
  days: number;
  onToggle: () => void;
  onDaysChange: (value: string) => void;
}

function PlaceRow({ label, isSelect, selected, days, onToggle, onDaysChange }: PlaceRowProps) {
  return (
    <div className="flex items-center gap-1.5">
      {isSelect ? (
        <Button
          variant={selected ? "default" : "outline"}
          size="sm"
          className="text-xs h-6 w-12 px-0 shrink-0"
          onClick={onToggle}
        >
          {selected ? "방문" : "선택"}
        </Button>
      ) : (
        <span className="text-xs text-muted-foreground shrink-0 w-12 text-center">
          ✓
        </span>
      )}
      <span className="text-xs flex-1 truncate">{label}</span>
      <Input
        type="number"
        min={0}
        max={30}
        value={days}
        onChange={(e) => onDaysChange(e.target.value)}
        className="h-6 w-12 text-xs"
        aria-label={`${label} 체류일`}
      />
      <span className="text-xs text-muted-foreground shrink-0">일</span>
    </div>
  );
}
