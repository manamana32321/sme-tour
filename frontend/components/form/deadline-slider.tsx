"use client";

import { Slider } from "@/components/ui/slider";

interface DeadlineSliderProps {
  value: number;
  onChange: (value: number) => void;
}

export function DeadlineSlider({ value, onChange }: DeadlineSliderProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">기간</label>
        <span className="text-sm font-semibold tabular-nums">{value}일</span>
      </div>
      <Slider
        min={3}
        max={30}
        step={1}
        value={[value]}
        onValueChange={(v) => { const arr = Array.isArray(v) ? v : [v]; onChange(arr[0]); }}
      />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>3일</span>
        <span>30일</span>
      </div>
    </div>
  );
}
