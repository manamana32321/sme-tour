# OR-Tools `y[d]` 변수 도입 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OR-Tools 솔버에 `y[d] ∈ {0,1}` 도시 방문 결정변수를 도입하고, 흐름 보존 식을 `Σ x == y[d]` 형태로 재작성하여 기존 71 tests 회귀 없이 후속 이슈(#30 stay_days, #31 required_cities)의 표현 기반을 구축.

**Architecture:** `OrToolsSolver.solve()` 한 함수 안에서 (1) 도시 단위 `y` 변수 추가, (2) 내륙 도시 흐름 보존을 `y`에 묶기, (3) 허브 `Hub_Stay` 에지 사용을 `y[h]`에 묶기, (4) `required_countries`로 결정되는 강제 방문을 `y[d] == 1` 핀으로 대체. 모델 외 코드(API/Graph/응답)는 손대지 않음.

**Tech Stack:** Python 3.12, OR-Tools CP-SAT (`ortools.sat.python.cp_model`), pytest, uv

---

## File Structure

- **Modify**: `engine/src/solvers/ortools.py` — `OrToolsSolver.solve()` 내부만 변경. 새 의존성 없음. `_last_y_values: dict[str, int] | None` 인스턴스 속성 추가 (테스트용 디버그 인터페이스).
- **Modify**: `engine/tests/test_solvers_ortools.py` — `TestOrToolsYVariable` 클래스 추가. 5개 invariant 테스트.

다른 파일(`graph.py`, `models.py`, `main.py`, frontend, k8s)은 변경 없음.

---

## 사전 조건

- 작업 디렉토리: `/home/json/sme-tour-worktrees/engine-y-variable`
- 브랜치: `feat/engine-y-variable`
- spec 문서가 git에 커밋된 상태 (`docs/superpowers/specs/2026-05-09-engine-y-variable-ortools-design.md`)

---

### Task 1: Baseline 회귀 테스트 — 71 tests 모두 pass 확인

**Files:**
- 변경 없음 (관찰만)

- [ ] **Step 1: 모든 테스트 통과 확인**

```bash
cd /home/json/sme-tour-worktrees/engine-y-variable/engine
uv run --active pytest -v 2>&1 | tail -20
```

Expected: `71 passed` (또는 그 이상). 실패 시 즉시 중단하고 사용자 알림.

- [ ] **Step 2: 현재 솔버 상태 스냅샷 (성능 baseline)**

```bash
uv run --active pytest tests/test_solvers_ortools.py -v --durations=10 2>&1 | tail -20
```

가장 오래 걸린 5개 테스트의 소요시간을 기록 (Task 6에서 비교용). 메모만, 커밋 없음.

---

### Task 2: TDD — `_last_y_values` 인터페이스 + 빈 dict로 초기화 (실패 테스트 → 구현 → 통과)

목표: solve() 호출 후 `solver._last_y_values`가 `dict[str, int]` 형태로 노출되도록 인프라만 깐다. 아직 y 변수가 모델에 들어가지 않으므로 기존 동작 영향 없음.

**Files:**
- Modify: `engine/src/solvers/ortools.py`
- Test: `engine/tests/test_solvers_ortools.py` (TestOrToolsYVariable 클래스 신규)

- [ ] **Step 1: 실패할 테스트 작성**

`engine/tests/test_solvers_ortools.py` 파일 끝에 추가:

```python
class TestOrToolsYVariable:
    """y[d] 결정변수 도입 invariants."""

    def test_y_values_exposed_after_solve(self, solver: OrToolsSolver, mini_graph) -> None:
        """solve() 후 _last_y_values가 노출되어야."""
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        # mini fixture: 3 hubs (CDG, FCO, AMS) + 2 cities (NCE_City, MIL_City) = 5 keys
        expected_keys = mini_graph.hubs | mini_graph.internal_cities
        assert set(solver._last_y_values.keys()) == expected_keys
        # 모든 값이 0 또는 1 (binary)
        assert all(v in (0, 1) for v in solver._last_y_values.values())
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd /home/json/sme-tour-worktrees/engine-y-variable/engine
uv run --active pytest tests/test_solvers_ortools.py::TestOrToolsYVariable::test_y_values_exposed_after_solve -v 2>&1 | tail
```

Expected: `AttributeError: 'OrToolsSolver' object has no attribute '_last_y_values'`

- [ ] **Step 3: 인터페이스 구현 (y 변수는 아직 안 만듦, 빈 dict로 채움)**

`engine/src/solvers/ortools.py`의 `OrToolsSolver.__init__`에 추가:

```python
class OrToolsSolver(BaseSolver):
    """OR-Tools CP-SAT + Iterative DFJ subtour elimination."""

    name = "ortools"

    def __init__(self) -> None:
        """OR-Tools는 라이센스 불필요."""
        self._last_y_values: dict[str, int] | None = None
```

`solve()` 함수 끝, return문 직전에 임시 채움 (다음 Task에서 모델 기반으로 교체):

`engine/src/solvers/ortools.py:200` 근처 (return OptimizeResult 직전, `visited_iata`/`visited_cities` 계산 직후) 에 다음 추가:

```python
        # ── y[d] 결정변수 노출 (Task 2: 임시로 visited 기반 derive) ──
        all_destinations = graph.hubs | graph.internal_cities
        self._last_y_values = {
            d: 1 if (d in visited_iata or d in visited_cities) else 0
            for d in all_destinations
        }
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run --active pytest tests/test_solvers_ortools.py::TestOrToolsYVariable -v 2>&1 | tail
```

Expected: `1 passed`

- [ ] **Step 5: 전체 회귀 확인**

```bash
uv run --active pytest -v 2>&1 | tail -5
```

Expected: `72 passed` (71 기존 + 1 신규)

- [ ] **Step 6: 커밋**

```bash
git add engine/src/solvers/ortools.py engine/tests/test_solvers_ortools.py
git commit -m "$(cat <<'EOF'
feat(engine): expose _last_y_values for y[d] invariant tests

y[d] 변수를 모델에 도입하기 전 단계로, 솔버 출력에서 도시 방문 여부를
dict 형태로 노출하는 인터페이스를 먼저 마련한다. 이번 커밋은 visited_*
응답값에서 derive하는 임시 구현이며, Task 3-5에서 실제 모델 변수로 교체된다.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: 내륙 도시 흐름 보존을 `y[c]`로 재작성

목표: 모델에 `y[c] ∈ {0,1}` 변수를 추가하고, 내륙 도시 흐름 보존 제약을 `Σ x == y[c]`로 변경. `required_countries` 처리는 이전과 동일하게 두되 (강제 흐름 = 1), 표현만 `y[c] == 1`로 핀.

**Files:**
- Modify: `engine/src/solvers/ortools.py:73-87` (흐름 보존 블록)

- [ ] **Step 1: 현재 흐름 보존 코드 확인**

`engine/src/solvers/ortools.py:73-87`의 현재 코드:

```python
        # 흐름 보존
        for n in nodes:
            out_idx = [i for i, ek in enumerate(edge_keys) if ek[0] == n]
            in_idx = [i for i, ek in enumerate(edge_keys) if ek[1] == n]
            if "_Entry" in n or "_Exit" in n:
                model.add(sum(x[i] for i in out_idx) == sum(x[i] for i in in_idx))
            else:
                # 내륙 도시: 소속 국가가 required면 강제 방문, 아니면 선택적
                hub = graph.city_to_hub.get(n)
                if hub and hub in required:
                    model.add(sum(x[i] for i in out_idx) == 1)
                    model.add(sum(x[i] for i in in_idx) == 1)
                else:
                    # 선택적: in=out (0=0 허용)
                    model.add(sum(x[i] for i in out_idx) == sum(x[i] for i in in_idx))
```

- [ ] **Step 2: y_city 변수 + 흐름 보존 재작성**

위 블록을 다음으로 교체:

```python
        # ── y[d] 도시 방문 결정변수 ──────────────────────────
        # 내륙 도시 단위 (도시 1개 = y 1개)
        y_city = {
            c: model.new_bool_var(f"y_city_{c}")
            for c in graph.internal_cities
        }

        # 흐름 보존
        for n in nodes:
            out_idx = [i for i, ek in enumerate(edge_keys) if ek[0] == n]
            in_idx = [i for i, ek in enumerate(edge_keys) if ek[1] == n]
            if "_Entry" in n or "_Exit" in n:
                # 허브 가상 노드: 통과 흐름 보존 (Task 4에서 y[h] 추가)
                model.add(sum(x[i] for i in out_idx) == sum(x[i] for i in in_idx))
            else:
                # 내륙 도시: outflow == inflow == y[c]
                model.add(sum(x[i] for i in out_idx) == y_city[n])
                model.add(sum(x[i] for i in in_idx) == y_city[n])

        # required_countries에 속한 내륙 도시는 y[c] = 1 강제
        for c in graph.internal_cities:
            hub = graph.city_to_hub.get(c)
            if hub and hub in required:
                model.add(y_city[c] == 1)
```

- [ ] **Step 3: solve 후 y_city 값을 _last_y_values에 반영 (Task 2에서 임시로 만든 derive 코드 교체 일부)**

`engine/src/solvers/ortools.py`의 Task 2에서 추가한 블록을 다음으로 교체:

```python
        # ── y[d] 결정변수 노출 ───────────────────────────────
        # internal cities: 모델에서 직접
        # hubs: Task 4 전까지는 visited_iata에서 derive (Task 4에서 모델 기반으로 교체)
        self._last_y_values = {
            **{c: int(solver.value(y_city[c])) for c in graph.internal_cities},
            **{h: 1 if h in visited_iata else 0 for h in graph.hubs},
        }
```

- [ ] **Step 4: 회귀 테스트**

```bash
uv run --active pytest -v 2>&1 | tail -10
```

Expected: `72 passed` (모두 그대로 통과). 실패 시 변경 분석.

- [ ] **Step 5: 커밋**

```bash
git add engine/src/solvers/ortools.py
git commit -m "$(cat <<'EOF'
feat(engine,ortools): y[c] 내륙 도시 결정변수 도입

내륙 도시의 흐름 보존을 명시적 y[c] ∈ {0,1} 변수로 재작성.
- 흐름: outflow == inflow == y[c]
- required_countries 안의 도시: y[c] == 1 핀
- 허브 (y[h])는 다음 커밋에서 Hub_Stay 에지와 연결

기존 동작과 동등 — 71 + 1 invariant tests 모두 그대로 통과.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: 허브에 `y[h]` 변수 추가 + Hub_Stay 에지 연결

목표: 허브 단위 `y[h] ∈ {0,1}`를 모델에 추가하고, `Hub_Stay` 에지 사용량과 연결 (`Σ x[Hub_Stay edges of h] == y[h]`). 허브의 일반 흐름 보존은 그대로.

**Files:**
- Modify: `engine/src/solvers/ortools.py` (y_city 정의 블록 + 흐름 보존 블록)

- [ ] **Step 1: y_hub 변수 + Hub_Stay 연결 제약 추가**

Task 3에서 만든 `y_city = {...}` 정의 블록 바로 아래에 다음 추가:

```python
        # 허브 단위 (Entry/Exit 묶음 → y 1개)
        y_hub = {
            h: model.new_bool_var(f"y_hub_{h}")
            for h in graph.hubs
        }

        # Hub_Stay 에지 사용량 = 허브 방문 여부
        # Hub_Stay edge: ({h}_Entry → {h}_Exit, "Hub_Stay")
        for h in graph.hubs:
            hub_stay_idx = [
                i for i, ek in enumerate(edge_keys)
                if ek[0] == f"{h}_Entry" and ek[1] == f"{h}_Exit" and ek[2] == "Hub_Stay"
            ]
            # mini fixture / production 모두 허브당 정확히 1개의 Hub_Stay 에지 존재
            assert len(hub_stay_idx) == 1, f"허브 {h}에 Hub_Stay 에지가 {len(hub_stay_idx)}개"
            model.add(sum(x[i] for i in hub_stay_idx) == y_hub[h])
```

- [ ] **Step 2: `_last_y_values` 노출을 모델 기반으로 교체**

Task 3에서 만든 `_last_y_values` 블록을 다음으로 교체:

```python
        # ── y[d] 결정변수 노출 ───────────────────────────────
        self._last_y_values = {
            **{c: int(solver.value(y_city[c])) for c in graph.internal_cities},
            **{h: int(solver.value(y_hub[h])) for h in graph.hubs},
        }
```

- [ ] **Step 3: 회귀 테스트**

```bash
uv run --active pytest -v 2>&1 | tail -10
```

Expected: `72 passed`. `y[h]`는 아직 어떤 제약에도 묶여있지 않으므로 (Hub_Stay 사용량과 양방향 == 관계만 있음, 강제 1 제약은 Task 5에서 추가) 기존 동작 영향 없음. 단, Hub_Stay 에지의 흐름 패턴이 솔버 결과에 영향을 줄 수 있어 행위 변화 가능성이 있음 → 모든 테스트가 정상 통과해야 함.

- [ ] **Step 4: 커밋**

```bash
git add engine/src/solvers/ortools.py
git commit -m "$(cat <<'EOF'
feat(engine,ortools): y[h] 허브 결정변수 + Hub_Stay 에지 연결

허브 자체에 y[h] ∈ {0,1} 변수를 두고 Hub_Stay 에지 사용량과 1:1 연결.
- y[h] == 1 ↔ {h}_Entry → {h}_Exit "Hub_Stay" 에지 사용
- _last_y_values dict가 이제 모델 기반 (visited_iata derive 아닌)

다음 커밋에서 required_countries 핀을 y[h]/y[c] == 1로 일원화.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: `required_countries` 핀을 `y[d] == 1`로 일원화

목표: 현재 `required` 처리가 흐름 1 강제(이미 Task 3에서 도시 측은 `y[c] == 1`로 변경됨)와 허브 통과(현재 자유)로 흩어져 있는 것을 `y[h] == 1`로 통일. 결과: required 안의 허브는 반드시 Hub_Stay 사용 → 명시적 방문.

**중요 — 동작 동등성 검증**: 기존 모델은 required_countries 안의 허브가 자동으로 방문되는지가 명시되지 않았음. 흐름 보존만으론 "통과"와 "방문" 구분이 안 됐다. 다만 자식 내륙 도시가 강제 방문되어야 했으므로(`Σ x == 1`), 그 도시를 들어가려면 부모 허브의 Entry/Exit를 거쳐야 했고 → 사실상 허브도 방문됨. 이번 변경으로 이 암묵적 invariant가 명시화됨. 71 기존 tests가 통과하는 한 동작 동등.

**Files:**
- Modify: `engine/src/solvers/ortools.py` (required 핀 블록)

- [ ] **Step 1: required_countries 핀 일원화**

Task 3에서 만든 다음 블록:

```python
        # required_countries에 속한 내륙 도시는 y[c] = 1 강제
        for c in graph.internal_cities:
            hub = graph.city_to_hub.get(c)
            if hub and hub in required:
                model.add(y_city[c] == 1)
```

위 블록을 다음으로 교체:

```python
        # ── 필수 방문 핀 ─────────────────────────────────────
        # required_countries 안의 허브 자체와 그 자식 내륙 도시 모두 강제 방문
        for h in required:
            if h in graph.hubs:  # 안전 가드 (잘못된 IATA 대비)
                model.add(y_hub[h] == 1)
        for c in graph.internal_cities:
            hub = graph.city_to_hub.get(c)
            if hub and hub in required:
                model.add(y_city[c] == 1)
```

- [ ] **Step 2: 회귀 테스트**

```bash
uv run --active pytest -v 2>&1 | tail -10
```

Expected: `72 passed`. 만약 `test_tight_budget_fewer_countries` 같이 "허브를 skip할 수 있다"를 검증하는 테스트가 실패하면 → required_countries=None인 경우 `required = graph.hubs`로 모든 허브를 강제하던 기존 코드와의 차이가 의심됨. 그 경우 다음 단계 진행 전 디버깅 필요.

- [ ] **Step 3: required_countries=None 시 동작 확인 (디버깅 단계, 통과 시 skip)**

`test_tight_budget_fewer_countries`가 통과하면 이 단계는 skip. 실패하면:

기존 [ortools.py:71](engine/src/solvers/ortools.py#L71):
```python
required = set(req.required_countries) if req.required_countries else graph.hubs
```

이 의미는 "사용자가 None을 보내면 모든 허브 강제 방문". 그런데 `test_tight_budget_fewer_countries`는 budget=1M, days=3에서 `len(visited_iata) <= 3`을 assert (3 = mini fixture의 모든 허브, 즉 "더 적게 방문 가능"). 기존 코드에서 이 테스트가 통과한다는 것은 INFEASIBLE 케이스를 허용하기 때문 (`if result.status != Status.INFEASIBLE`). 따라서 신모델에서도 INFEASIBLE 또는 일부만 방문이 가능해야 함. `required = graph.hubs`로 두면 1M/3일에서는 INFEASIBLE이 나올 것 — 이 경우도 테스트는 통과 (assert 분기 `if status != INFEASIBLE`).

검증: 위 변경 후 테스트가 실제로 무엇을 반환하는지 출력:

```bash
uv run --active pytest tests/test_solvers_ortools.py::TestOrToolsSolverBasic::test_tight_budget_fewer_countries -v -s 2>&1 | tail
```

INFEASIBLE 또는 visited_iata <= 3이면 통과.

- [ ] **Step 4: 커밋**

```bash
git add engine/src/solvers/ortools.py
git commit -m "$(cat <<'EOF'
feat(engine,ortools): required_countries 핀을 y[d] == 1로 일원화

기존엔 required_countries 안의 허브 자체에는 명시적 핀이 없고
자식 내륙 도시의 흐름 == 1을 통해 암묵적으로 방문이 보장되었다.
이번 변경으로 y[h] == 1을 명시 핀하여 의미를 분명히 한다.

기존 71 + invariant 1 = 72 tests 모두 통과 (동작 동등).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: 추가 invariant 테스트 4개 (visited 일치, 미방문 허브, required 핀)

목표: y[d]의 의미가 응답값과 일치하는지 명시적으로 검증.

**Files:**
- Modify: `engine/tests/test_solvers_ortools.py` (TestOrToolsYVariable 클래스 확장)

- [ ] **Step 1: 4개 테스트 추가**

`engine/tests/test_solvers_ortools.py`의 `TestOrToolsYVariable` 클래스 안 (Task 2에서 만든 테스트 아래)에 추가:

```python
    def test_y_hub_matches_visited_iata(self, solver: OrToolsSolver, mini_graph) -> None:
        """y[h] == 1 ↔ h가 visited_iata에 포함."""
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        for h in mini_graph.hubs:
            visited = h in result.visited_iata
            y_val = solver._last_y_values[h]
            assert (y_val == 1) == visited, (
                f"허브 {h}: y={y_val}, visited={visited}"
            )

    def test_y_city_matches_visited_cities(self, solver: OrToolsSolver, mini_graph) -> None:
        """y[c] == 1 ↔ c가 visited_cities에 포함."""
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        for c in mini_graph.internal_cities:
            visited = c in result.visited_cities
            y_val = solver._last_y_values[c]
            assert (y_val == 1) == visited, (
                f"도시 {c}: y={y_val}, visited={visited}"
            )

    def test_y_hub_zero_means_no_hub_stay_edge(self, solver: OrToolsSolver, mini_graph) -> None:
        """y[h] == 0인 허브는 route에 Hub_Stay 에지가 없어야."""
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
        )
        result = solver.solve(mini_graph, req)
        assert solver._last_y_values is not None
        skipped_hubs = {h for h in mini_graph.hubs if solver._last_y_values[h] == 0}
        hub_stay_visited = {
            e.from_node.rsplit("_", 1)[0]
            for e in result.route
            if e.mode == "Hub_Stay"
        }
        assert skipped_hubs.isdisjoint(hub_stay_visited), (
            f"y[h]=0 허브 {skipped_hubs}와 Hub_Stay 사용 허브 {hub_stay_visited} 교집합 있음"
        )

    def test_required_countries_pinned_to_one(self, solver: OrToolsSolver, mini_graph) -> None:
        """required_countries 안의 허브와 자식 도시는 y[d] == 1."""
        req = OptimizeRequest(
            budget_won=30_000_000,
            deadline_days=30,
            start_hub="CDG",
            w_cost=0.5,
            required_countries=["CDG", "FCO"],  # AMS는 자유
        )
        result = solver.solve(mini_graph, req)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert solver._last_y_values is not None
        # 허브 핀
        assert solver._last_y_values["CDG"] == 1
        assert solver._last_y_values["FCO"] == 1
        # 자식 도시 핀 (mini_graph.city_to_hub: NCE_City→CDG, MIL_City→FCO)
        assert solver._last_y_values["NCE_City"] == 1
        assert solver._last_y_values["MIL_City"] == 1
```

- [ ] **Step 2: 추가 테스트 실행**

```bash
uv run --active pytest tests/test_solvers_ortools.py::TestOrToolsYVariable -v 2>&1 | tail -10
```

Expected: `5 passed` (Task 2의 1개 + 신규 4개).

- [ ] **Step 3: 전체 테스트 실행**

```bash
uv run --active pytest -v 2>&1 | tail -5
```

Expected: `75 passed` (71 기존 + 4 신규 invariant — Task 2의 1개는 이미 합산됨).

- [ ] **Step 4: 커밋**

```bash
git add engine/tests/test_solvers_ortools.py
git commit -m "$(cat <<'EOF'
test(engine,ortools): y[d] invariant 테스트 4개 추가

- y[h]가 visited_iata와 일치
- y[c]가 visited_cities와 일치
- y[h]=0 허브는 Hub_Stay 에지 미사용
- required_countries 안의 허브와 자식 도시는 y[d]=1 핀

후속 이슈 #30/#31에서 같은 invariant 위에 빌드.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: 성능 회귀 확인 + 디자인 문서 검증

**Files:**
- 변경 없음

- [ ] **Step 1: 성능 비교**

```bash
uv run --active pytest tests/test_solvers_ortools.py -v --durations=10 2>&1 | tail -20
```

Task 1 Step 2에서 기록한 baseline과 비교. **허용**: 가장 오래 걸린 5개 테스트의 합이 1.5배 이내.

초과 시: 사용자에게 알리고 진행 여부 결정 (예상보다 느린 경우 모델 다시 검토). 1.5배 이내면 다음 단계.

- [ ] **Step 2: spec 문서 핵심 요구 충족 확인 (수동 점검)**

spec ([docs/superpowers/specs/2026-05-09-engine-y-variable-ortools-design.md](docs/superpowers/specs/2026-05-09-engine-y-variable-ortools-design.md))의 다음 항목 충족 여부 확인. 모두 ✓ 되어야 함:

- [ ] `y[d] ∈ {0, 1}` 도시 단위 변수 (총 45개 / mini는 5개) — Task 3, 4
- [ ] 내륙 도시 `outflow == inflow == y[c]` — Task 3
- [ ] 허브 `Σ x[Hub_Stay edges of h] == y[h]` — Task 4
- [ ] required_countries 안의 허브와 자식 도시 `y[d] == 1` — Task 5
- [ ] 71 기존 tests 회귀 없음 — Task 1, 3, 4, 5
- [ ] y[d] invariant 5개 — Task 2, 6
- [ ] API 계약 변경 없음 — 코드 검토로 (graph.py, models.py, main.py 미변경)

`git diff main -- engine/src/graph.py engine/src/models.py engine/src/main.py | wc -l` → 0이어야 함.

```bash
git diff main -- engine/src/graph.py engine/src/models.py engine/src/main.py | wc -l
```

Expected: `0`

---

### Task 8: PR 생성

**Files:**
- 변경 없음 (push + PR)

- [ ] **Step 1: 푸시**

```bash
cd /home/json/sme-tour-worktrees/engine-y-variable
git push -u origin feat/engine-y-variable 2>&1 | tail -5
```

- [ ] **Step 2: PR 생성 (사용자 검토용 본문 초안 보여드린 후 승인 받고 진행)**

본문은 spec 핵심 요약 + Test plan. 사용자 승인 후 다음 명령:

```bash
gh pr create --title "feat(engine,ortools): y[d] 도시 방문 결정 변수 도입 (closes #29)" --body "$(cat <<'EOF'
## Summary
[#29](https://github.com/manamana32321/sme-tour/issues/29) 구현. OR-Tools 솔버에 도시 단위 `y[d] ∈ {0,1}` 결정변수를 도입하고 흐름 보존 식을 `Σ x == y[d]` 형태로 재작성한다. 동작은 기존과 동등 (회귀 0).

- `y_city[c]` (30개 내륙 도시) + `y_hub[h]` (15개 허브) = 45개 binary 변수 추가
- 내륙 도시 흐름: `outflow == inflow == y[c]`
- 허브 Hub_Stay 에지: `Σ x[Hub_Stay of h] == y[h]`
- `required_countries`: `y[d] == 1` 핀으로 일원화
- 디버그 노출: `solver._last_y_values: dict[str, int]` (테스트 invariant 검증용, 응답에는 영향 없음)

## Spec
[docs/superpowers/specs/2026-05-09-engine-y-variable-ortools-design.md](docs/superpowers/specs/2026-05-09-engine-y-variable-ortools-design.md)

## Test plan
- [x] 기존 71 tests 회귀 없음
- [x] 신규 invariant 5개 (`TestOrToolsYVariable`) pass
- [ ] 머지 후 production /optimize 응답 동등 확인 (수동, parity check)
- [ ] 솔버 시간 회귀 ≤ 1.5x baseline

## Out of scope
- Gurobi 솔버 변경 (별도 PR)
- 도시 체류시간 (#30), 도시 단위 명시 선택 (#31)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: PR URL 사용자에게 보고**

---

## 자기 점검

이 plan은 spec과 다음과 같이 매핑된다:

- spec §결정변수 → Task 3, 4
- spec §제약 변경 (a) 내륙 도시 흐름 → Task 3
- spec §제약 변경 (b) 허브 Hub_Stay 연결 → Task 4
- spec §제약 변경 (c) 필수 방문 고정 → Task 5
- spec §동작 동등성 → Task 1, 3, 4, 5 회귀 verification
- spec §결과 응답 → 변경 없음 확인 (Task 7 Step 2)
- spec §테스트 → Task 2, 6
- spec §롤아웃 → Task 8 + 머지 후 별도 작업

scope: 단일 솔버 (ortools), 단일 PR로 완결됨. ✓

placeholders: 모든 step에 실제 코드 또는 명령. ✓
