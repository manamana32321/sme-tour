# DestinationPicker 통합 컴포넌트 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 방문지 선택(`CountrySelect` + `CitySelect`)과 체류일 입력(`StayDaysInput`)을 단일 컴포넌트 `DestinationPicker`로 통합하고, 허브·내륙 도시 45곳 모두에 대해 선택과 체류일을 한 곳에서 다루게 한다.

**Architecture:** 3개 폼 컴포넌트를 1개로 흡수. "전체 완주 / 선택 방문" 모드 토글로 엔진의 `required_countries=null`(완주) vs `subset`(선택) 시맨틱을 명시적으로 노출. 상태는 `mode` + `selectedHubs` + `selectedCities` + `stayDays`로 정리되어 page.tsx가 보유하고, 컴포넌트는 controlled. 부수적으로 엔진의 `required_countries=[]` 처리 버그(falsy→전체)를 수정해 "선택 방문 + 도시만 선택" 케이스를 올바르게 만든다.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind, shadcn/ui (Button·Input), nuqs (URL 상태), 엔진은 Python + Gurobi/OR-Tools + pytest.

---

## File Structure

| 파일 | 역할 | 액션 |
|---|---|---|
| `engine/src/solvers/gurobi.py` | `required_countries` None/`[]` 구분 | Modify (1줄) |
| `engine/src/solvers/ortools.py` | 동일 | Modify (1줄) |
| `engine/tests/test_solvers_ortools.py` | `[]` 시맨틱 회귀 테스트 | Modify (테스트 추가) |
| `frontend/components/form/destination-picker.tsx` | 통합 방문지+체류일 컴포넌트 | Create |
| `frontend/components/form/optimize-form.tsx` | 구 3개 컴포넌트 → `DestinationPicker` 교체 | Modify |
| `frontend/app/page.tsx` | `mode` 상태 추가, 페이로드 파생, 재배선 | Modify |
| `frontend/components/form/country-select.tsx` | — | Delete |
| `frontend/components/form/city-select.tsx` | — | Delete |
| `frontend/components/form/stay-days-input.tsx` | — | Delete |

**검증 전략:** 프론트엔드에 단위 테스트 러너가 없다(`package.json` scripts = dev/build/start/lint). 프론트 태스크는 `pnpm lint`(ESLint) + `pnpm build`(타입체크 포함)를 게이트로 쓰고, Task 5에서 브라우저 도그푸딩으로 기능 검증한다(프로젝트 `CLAUDE.md`의 프론트엔드 개발 사이클 5·6단계). 엔진 태스크는 pytest로 정식 TDD.

---

### Task 1: 엔진 — `required_countries=[]` 시맨틱 수정

`required_countries`가 `[]`(빈 배열)일 때 현재 코드는 `if req.required_countries`로 검사해 falsy → "전체 허브 강제"로 처리한다. 이는 "선택 방문 모드인데 허브를 하나도 안 고름"을 표현 불가능하게 만든다. `is not None` 검사로 바꿔 `[]`=강제 없음, `None`=전체 강제로 구분한다.

**Files:**
- Modify: `engine/src/solvers/gurobi.py:162`
- Modify: `engine/src/solvers/ortools.py:73`
- Test: `engine/tests/test_solvers_ortools.py`

- [ ] **Step 1: 회귀 테스트 작성**

`engine/tests/test_solvers_ortools.py`의 `TestOrToolsSolverBasic` 클래스 끝에 아래 메서드를 추가한다 (들여쓰기는 클래스 메서드 레벨, 기존 `def test_...`와 동일):

```python
    def test_required_countries_empty_vs_none(self, solver: OrToolsSolver, mini_graph) -> None:
        """required_countries=[] → 허브 강제 없음. None → 전체 허브 강제. 둘은 구분돼야 함."""
        common = dict(budget_won=30_000_000, deadline_days=30, start_hub="CDG", w_cost=0.5)
        r_none = solver.solve(mini_graph, OptimizeRequest(**common, required_countries=None))
        r_empty = solver.solve(mini_graph, OptimizeRequest(**common, required_countries=[]))

        assert r_none.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert r_empty.status in (Status.OPTIMAL, Status.FEASIBLE)
        # None: mini fixture의 모든 허브를 강제 방문
        assert set(r_none.visited_iata) == set(mini_graph.hubs)
        # []: 출발 허브만 강제 → solver가 자유롭게 더 적게 방문 가능
        assert len(r_empty.visited_iata) < len(r_none.visited_iata)
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

Run: `cd engine && uv run pytest tests/test_solvers_ortools.py::TestOrToolsSolverBasic::test_required_countries_empty_vs_none -v`
Expected: FAIL — `assert len(r_empty.visited_iata) < len(r_none.visited_iata)`에서 실패 (수정 전엔 `[]`도 전체 허브를 강제하므로 두 값이 같음).

- [ ] **Step 3: gurobi.py 수정**

`engine/src/solvers/gurobi.py` 162번째 줄:

```python
        required = set(req.required_countries) if req.required_countries else graph.hubs
```

를 아래로 변경:

```python
        required = set(req.required_countries) if req.required_countries is not None else graph.hubs
```

- [ ] **Step 4: ortools.py 수정**

`engine/src/solvers/ortools.py` 73번째 줄:

```python
        required = set(req.required_countries) if req.required_countries else graph.hubs
```

를 아래로 변경:

```python
        required = set(req.required_countries) if req.required_countries is not None else graph.hubs
```

- [ ] **Step 5: 테스트 실행 — 통과 확인**

Run: `cd engine && uv run pytest tests/test_solvers_ortools.py -v`
Expected: PASS — 신규 테스트 포함 전체 통과. (`required_cities`는 기존대로 `if ... else set()` 유지 — `[]`와 `None`이 모두 "강제 없음"으로 동일 의미라 변경 불필요.)

- [ ] **Step 6: 커밋**

```bash
git add engine/src/solvers/gurobi.py engine/src/solvers/ortools.py engine/tests/test_solvers_ortools.py
git commit -m "fix(engine): required_countries=[] 를 '강제 없음'으로 구분 (None=전체 강제)"
```

---

### Task 2: 프론트 — `DestinationPicker` 컴포넌트 생성

방문지 선택 + 체류일 입력을 단일 controlled 컴포넌트로 작성한다. 모드 토글(전체 완주 / 선택 방문), 허브별 collapsible 그룹, 그룹 안에 허브-도시 1개 + 내륙 도시 N개의 행. 각 행은 선택 토글(선택 모드일 때) + 체류일 number input. 하단에 요약 라인.

**Files:**
- Create: `frontend/components/form/destination-picker.tsx`

- [ ] **Step 1: 컴포넌트 파일 작성**

`frontend/components/form/destination-picker.tsx` 전체 내용:

```tsx
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
```

- [ ] **Step 2: 타입체크 — 컴포넌트 단독 검증**

Run: `cd frontend && pnpm build`
Expected: 빌드 성공. `destination-picker.tsx`는 아직 어디서도 import 안 되므로 이 시점엔 "사용되지 않음" 경고는 없을 수 있으나 타입 에러가 없어야 함. (ESLint의 unused 규칙은 export된 컴포넌트엔 적용 안 됨.)

- [ ] **Step 3: 커밋**

```bash
git add frontend/components/form/destination-picker.tsx
git commit -m "feat(frontend): DestinationPicker — 방문지 선택 + 체류일 통합 컴포넌트"
```

---

### Task 3: 프론트 — `optimize-form.tsx` 재배선

`OptimizeForm`이 받던 `required_countries`/`required_cities`/`stay_days` + 3개 콜백을 `mode`/`selectedHubs`/`selectedCities`/`stayDays` + 4개 콜백으로 교체하고, 렌더에서 `CountrySelect`·`CitySelect`·`StayDaysInput` 3개를 `DestinationPicker` 1개로 바꾼다.

**Files:**
- Modify: `frontend/components/form/optimize-form.tsx`

- [ ] **Step 1: `optimize-form.tsx` 전체 교체**

`frontend/components/form/optimize-form.tsx` 전체 내용을 아래로 교체:

```tsx
"use client";

import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { HubSelect } from "./hub-select";
import { BudgetSlider } from "./budget-slider";
import { DeadlineSlider } from "./deadline-slider";
import { WeightSlider } from "./weight-slider";
import { DestinationPicker, type PickerMode } from "./destination-picker";

export type FocusField = "budget" | "deadline" | "countries" | null;

interface OptimizeFormProps {
  budget_won: number;
  deadline_days: number;
  start_hub: string;
  w_cost: number;
  mode: PickerMode;
  selectedHubs: string[];
  selectedCities: string[];
  stayDays: Record<string, number>;
  focusField: FocusField;
  onBudgetChange: (v: number) => void;
  onDeadlineChange: (v: number) => void;
  onHubChange: (v: string) => void;
  onWeightChange: (v: number) => void;
  onModeChange: (v: PickerMode) => void;
  onSelectedHubsChange: (v: string[]) => void;
  onSelectedCitiesChange: (v: string[]) => void;
  onStayDaysChange: (v: Record<string, number>) => void;
}

export function OptimizeForm(props: OptimizeFormProps) {
  const budgetRef = useRef<HTMLDivElement>(null);
  const deadlineRef = useRef<HTMLDivElement>(null);
  const countriesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ref =
      props.focusField === "budget"
        ? budgetRef
        : props.focusField === "deadline"
          ? deadlineRef
          : props.focusField === "countries"
            ? countriesRef
            : null;
    ref?.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [props.focusField]);

  return (
    <Card className="h-fit lg:sticky lg:top-4">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">입력 조건</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <HubSelect value={props.start_hub} onChange={props.onHubChange} />
        <FocusableField fieldRef={budgetRef} active={props.focusField === "budget"}>
          <BudgetSlider value={props.budget_won} onChange={props.onBudgetChange} />
        </FocusableField>
        <FocusableField fieldRef={deadlineRef} active={props.focusField === "deadline"}>
          <DeadlineSlider value={props.deadline_days} onChange={props.onDeadlineChange} />
        </FocusableField>
        <WeightSlider value={props.w_cost} onChange={props.onWeightChange} />
        <FocusableField fieldRef={countriesRef} active={props.focusField === "countries"}>
          <DestinationPicker
            mode={props.mode}
            selectedHubs={props.selectedHubs}
            selectedCities={props.selectedCities}
            stayDays={props.stayDays}
            onModeChange={props.onModeChange}
            onSelectedHubsChange={props.onSelectedHubsChange}
            onSelectedCitiesChange={props.onSelectedCitiesChange}
            onStayDaysChange={props.onStayDaysChange}
          />
        </FocusableField>
      </CardContent>
    </Card>
  );
}

interface FocusableFieldProps {
  active: boolean;
  children: React.ReactNode;
  fieldRef: React.RefObject<HTMLDivElement | null>;
}

function FocusableField({ active, children, fieldRef }: FocusableFieldProps) {
  return (
    <div
      ref={fieldRef}
      className={cn(
        "rounded-lg p-2 -m-2 transition-shadow",
        active && "ring-2 ring-amber-400 animate-pulse",
      )}
    >
      {children}
    </div>
  );
}
```

- [ ] **Step 2: 구 컴포넌트 3개 삭제**

```bash
cd frontend && rm components/form/country-select.tsx components/form/city-select.tsx components/form/stay-days-input.tsx
```

- [ ] **Step 3: 타입체크 — page.tsx 미수정 상태라 실패 예상**

Run: `cd frontend && pnpm build`
Expected: FAIL — `app/page.tsx`가 아직 구 props(`required_countries` 등)로 `OptimizeForm`을 호출하므로 타입 에러. 다음 태스크에서 page.tsx를 고친다. (커밋은 Task 4와 함께.)

---

### Task 4: 프론트 — `page.tsx` 상태/페이로드 재배선

`page.tsx`에 `mode` nuqs 상태를 추가하고, `requiredCountries`(구 useState)를 `selectedHubs`로 교체, 페이로드를 모드에 따라 파생한다.

**Files:**
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: import 줄 수정**

`frontend/app/page.tsx` 5번째 줄:

```tsx
import { useQueryStates, parseAsInteger, parseAsFloat, parseAsString, parseAsArrayOf, useQueryState } from "nuqs";
```

를 아래로 변경 (`parseAsStringEnum` 추가):

```tsx
import { useQueryStates, parseAsInteger, parseAsFloat, parseAsString, parseAsArrayOf, parseAsStringEnum, useQueryState } from "nuqs";
```

- [ ] **Step 2: 상태 선언 교체**

`page.tsx`의 53번째 줄:

```tsx
  const [requiredCountries, setRequiredCountries] = useState<string[] | null>(null);
```

를 아래로 변경:

```tsx
  const [mode, setMode] = useQueryState(
    "mode",
    parseAsStringEnum<"full" | "select">(["full", "select"]).withDefault("full"),
  );
  const [selectedHubs, setSelectedHubs] = useState<string[]>([]);
```

- [ ] **Step 3: 페이로드 파생 + useOptimize 호출 수정**

`page.tsx`의 73~83번째 줄 (현재):

```tsx
  const stayDaysPayload = Object.keys(stayDays).length > 0 ? stayDays : null;

  const { result, loading, error } = useOptimize({
    budget_won: params.budget_won,
    deadline_days: params.deadline_days,
    start_hub: params.start_hub,
    w_cost: params.w_cost,
    required_countries: requiredCountries,
    required_cities: requiredCities,
    stay_days: stayDaysPayload,
  });
```

를 아래로 변경:

```tsx
  const stayDaysPayload = Object.keys(stayDays).length > 0 ? stayDays : null;
  const isFull = mode === "full";

  const { result, loading, error } = useOptimize({
    budget_won: params.budget_won,
    deadline_days: params.deadline_days,
    start_hub: params.start_hub,
    w_cost: params.w_cost,
    required_countries: isFull ? null : selectedHubs,
    required_cities: isFull ? null : requiredCities,
    stay_days: stayDaysPayload,
  });
```

(`requiredCities`는 기존 nuqs 파생값을 그대로 재사용 — `requiredCitiesArr.length > 0 ? requiredCitiesArr : null`.)

- [ ] **Step 4: `OptimizeForm` 호출부 교체**

`page.tsx`의 `<OptimizeForm ... />` 블록 (현재 92~108번째 줄):

```tsx
        <OptimizeForm
          budget_won={params.budget_won}
          deadline_days={params.deadline_days}
          start_hub={params.start_hub}
          w_cost={params.w_cost}
          required_countries={requiredCountries}
          required_cities={requiredCities}
          stay_days={stayDays}
          focusField={focusField}
          onBudgetChange={(v) => setParams({ budget_won: v })}
          onDeadlineChange={(v) => setParams({ deadline_days: v })}
          onHubChange={(v) => setParams({ start_hub: v })}
          onWeightChange={(v) => setParams({ w_cost: v })}
          onCountriesChange={setRequiredCountries}
          onCitiesChange={setRequiredCities}
          onStayDaysChange={setStayDays}
        />
```

를 아래로 변경:

```tsx
        <OptimizeForm
          budget_won={params.budget_won}
          deadline_days={params.deadline_days}
          start_hub={params.start_hub}
          w_cost={params.w_cost}
          mode={mode}
          selectedHubs={selectedHubs}
          selectedCities={requiredCities ?? []}
          stayDays={stayDays}
          focusField={focusField}
          onBudgetChange={(v) => setParams({ budget_won: v })}
          onDeadlineChange={(v) => setParams({ deadline_days: v })}
          onHubChange={(v) => setParams({ start_hub: v })}
          onWeightChange={(v) => setParams({ w_cost: v })}
          onModeChange={setMode}
          onSelectedHubsChange={setSelectedHubs}
          onSelectedCitiesChange={(v) => setRequiredCities(v.length > 0 ? v : null)}
          onStayDaysChange={setStayDays}
        />
```

- [ ] **Step 5: `InfeasibleBanner`의 `requiredCountries` prop 수정**

`page.tsx`의 `<InfeasibleBanner ... />` 블록 (현재 127~135번째 줄)에서 `requiredCountries` prop을 모드 반영하도록 변경. 현재:

```tsx
        {result?.status === "infeasible" && (
          <InfeasibleBanner
            requiredCountries={requiredCountries}
            currentBudget={params.budget_won}
            currentDays={params.deadline_days}
            onFocusBudget={() => setFocusField("budget")}
            onFocusDeadline={() => setFocusField("deadline")}
            onFocusCountries={() => setFocusField("countries")}
          />
        )}
```

를 아래로 변경 (`requiredCountries` 한 줄만 교체):

```tsx
        {result?.status === "infeasible" && (
          <InfeasibleBanner
            requiredCountries={isFull || selectedHubs.length === 0 ? null : selectedHubs}
            currentBudget={params.budget_won}
            currentDays={params.deadline_days}
            onFocusBudget={() => setFocusField("budget")}
            onFocusDeadline={() => setFocusField("deadline")}
            onFocusCountries={() => setFocusField("countries")}
          />
        )}
```

- [ ] **Step 6: 사용하지 않게 된 import 확인**

`page.tsx` 상단 import에서 `useState`가 여전히 쓰이는지 확인한다 (`selectedHubs`, `activeIndex`, `openIndex`, `focusField`가 `useState`를 쓰므로 유지돼야 함). `parseAsString`도 `stay_days`/`start_hub`에서 쓰이므로 유지. 제거할 import는 없음 — 확인만 하고 넘어간다.

- [ ] **Step 7: 타입체크 + 린트**

Run: `cd frontend && pnpm build && pnpm lint`
Expected: PASS — 빌드·린트 모두 통과. 타입 에러 0, ESLint 에러 0.

- [ ] **Step 8: 커밋**

```bash
git add frontend/components/form/optimize-form.tsx frontend/app/page.tsx
git commit -m "feat(frontend): DestinationPicker로 방문지+체류일 통합, 구 컴포넌트 3개 제거"
```

---

### Task 5: 브라우저 도그푸딩 검증

프로젝트 `CLAUDE.md`의 프론트엔드 개발 사이클(5 시각 검증 / 6 이벤트 검증)에 따라 dev 서버에서 직접 확인한다.

**Files:** 없음 (검증 전용)

- [ ] **Step 1: dev 서버 기동**

Run: `cd frontend && pnpm dev`
별도 터미널/백그라운드로 실행. `http://localhost:3000` 접속.

> 엔진 API가 필요하다. `frontend/lib/api.ts`가 가리키는 API base URL을 확인해, 로컬 엔진(`cd engine && uv run uvicorn src.main:app --reload --port 8000`)을 띄우거나 배포된 `api.sme-tour.json-server.win`를 쓰도록 한다.

- [ ] **Step 2: 전체 완주 모드 — happy path**

- 페이지 로드 시 기본 모드가 "전체 완주"인지 확인
- 허브 그룹을 펼쳐 도시 행이 보이는지, 각 행에 "✓" + 체류일 input이 있는지 확인
- 체류일을 몇 개 입력 → 하단 요약 "45곳 전체 · 체류일 합계 N일"이 갱신되는지
- 결과 지도/요약/경로가 정상 갱신되는지
- URL에 `stay_days` 파라미터가 반영되는지

- [ ] **Step 3: 선택 방문 모드 — happy path**

- "선택 방문" 토글 클릭 → 안내 문구가 바뀌고 각 행에 "선택/방문" 토글 버튼이 나타나는지
- 허브 1개 + 내륙 도시 몇 개를 "방문"으로 토글 → 그룹 헤더 카운트 배지, 하단 "N곳 강제 방문"이 갱신되는지
- 결과가 선택한 곳을 강제 방문하는지 (지도/경로에 반영)
- URL에 `mode=select` + `required_cities` 파라미터가 반영되는지

- [ ] **Step 4: 엣지 — 선택 방문 + 도시만 선택**

- 선택 방문 모드에서 허브는 하나도 안 고르고 내륙 도시만 1~2개 "방문" 토글
- 결과가 infeasible이 아니라 정상 경로를 반환하는지 확인 (Task 1 엔진 수정이 적용된 API 기준 — 로컬 엔진이면 이 worktree 코드, 배포 엔진이면 아직 구버전일 수 있음에 유의)
- infeasible이 뜬다면: 사용 중인 API가 Task 1 수정 전 버전인지 먼저 의심

- [ ] **Step 5: 모드 전환 + infeasible 배너**

- 선택 방문 → 전체 완주 전환 시 선택 상태가 보존되는지 (다시 선택 방문으로 돌아오면 복원)
- 예산을 최소로 낮춰 infeasible 유발 → `InfeasibleBanner`가 뜨고 "방문 국가 줄이기" 등 버튼이 `DestinationPicker`로 스크롤 포커스되는지

- [ ] **Step 6: 브라우저 콘솔 확인**

- 콘솔에 에러·경고 없는지 확인 (특히 React key warning, controlled input warning)

- [ ] **Step 7: 결과 보고**

- 각 단계 결과를 사용자에게 보고. 불일치·버그 발견 시 수정 후 재검증 (필요하면 fixup 커밋).
- 배포 엔진을 썼고 Task 1 수정이 아직 배포 안 됐다면, 엔진 배포(PR 머지 → ArgoCD/Image Updater) 후 Step 4 재검증이 필요함을 명시.

---

## Self-Review

**Spec coverage:**
- B(도시 단위 노출) → Task 2 `DestinationPicker`가 45곳(허브+내륙) 전부에 체류일 input 제공 ✓
- 3개 컴포넌트 → 1개 흡수 → Task 3 (구 3개 삭제 + 교체) ✓
- 모드 토글(완주/선택) → Task 2 모드 토글 + Task 4 `mode` nuqs 상태 ✓
- 기본 체류일 0 → `PlaceRow`의 `stayDays[node] ?? 0`, `setDays` 클램프 ✓
- 단일 SSOT 상태 → Task 4에서 `mode`+`selectedHubs`+`requiredCities`+`stayDays`로 정리 ✓
- 엔진 `[]` 시맨틱 footgun → Task 1 ✓

**Placeholder scan:** 모든 코드 스텝에 실제 코드 포함. "적절한 에러 처리" 류 없음. ✓

**Type consistency:**
- `PickerMode` = `"full" | "select"` — `destination-picker.tsx` export, `optimize-form.tsx`·`page.tsx`에서 동일 사용 ✓
- `DestinationPicker` props 4개 콜백 = `optimize-form.tsx` 전달 prop = `page.tsx` 핸들러 시그니처 일치 ✓
- `selectedCities` (컴포넌트) ← `requiredCities ?? []` (page) — `string[]` 타입 일치, `onSelectedCitiesChange`는 `[]→null` 변환 후 `setRequiredCities` ✓
- 엔진: `required_countries is not None` — `gurobi.py`·`ortools.py` 동일 변경 ✓

**알려진 한계 (스펙상 의도된 것):**
- 선택 방문 모드에서 허브 0개 + 도시 0개면 `required_countries=[]`, `required_cities=null` → 엔진은 "강제 없음" → solver가 출발 허브만 도는 최소 경로. 의도된 동작 (선택 안 하면 자유).
- `InfeasibleBanner`는 선택 방문 + 허브 0개일 때 `requiredCountries=null`로 넘겨 "15개국 모두" 문구가 표시됨 — 미세한 부정확이나 infeasible 힌트 용도라 허용.
