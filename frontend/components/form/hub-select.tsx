"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { HUB_LIST } from "@/lib/hubs";

interface HubSelectProps {
  value: string;
  onChange: (value: string) => void;
}

export function HubSelect({ value, onChange }: HubSelectProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">출발 공항</label>
      <Select value={value} onValueChange={(v) => { if (v) onChange(v); }}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="출발 공항 선택" />
        </SelectTrigger>
        <SelectContent>
          {HUB_LIST.map((hub) => (
            <SelectItem key={hub.iata} value={hub.iata}>
              {hub.flag} {hub.iata} · {hub.city_kr}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
