"use client";

import { Input } from "@/components/ui/input";
import { HUBS } from "@/lib/hubs";

interface StayDaysInputProps {
  selectedCountries: string[] | null; // null = all 15 countries
  stayDays: Record<string, number>;
  onChange: (next: Record<string, number>) => void;
}

const ALL_IATAS = Object.keys(HUBS);

export function StayDaysInput({ selectedCountries, stayDays, onChange }: StayDaysInputProps) {
  const visible = selectedCountries ?? ALL_IATAS;

  if (visible.length === 0) {
    return null;
  }

  function setOne(iata: string, value: string) {
    const days = parseInt(value, 10);
    if (isNaN(days) || days < 0) {
      onChange({ ...stayDays, [iata]: 0 });
      return;
    }
    onChange({ ...stayDays, [iata]: Math.min(days, 30) });
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">국가별 체류일</label>
        <span className="text-xs text-muted-foreground">기본 0일</span>
      </div>
      <div className="grid grid-cols-2 gap-1.5">
        {visible.map((iata) => {
          const hub = HUBS[iata];
          if (!hub) return null;
          return (
            <div key={iata} className="flex items-center gap-1.5">
              <span className="text-xs flex-1 truncate">
                {hub.flag} {hub.city_kr}
              </span>
              <Input
                type="number"
                min={0}
                max={30}
                value={stayDays[iata] ?? 0}
                onChange={(e) => setOne(iata, e.target.value)}
                className="h-7 w-14 text-xs"
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
