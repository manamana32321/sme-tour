# 엔진 모델 교체: `y[d]` 도시 방문 결정 변수 도입 (Gurobi 미러)

작성: 2026-05-09
관련 이슈: [manamana32321/sme-tour#39](https://github.com/manamana32321/sme-tour/issues/39)
선행 작업: PR #37 (OR-Tools 동일 변경), 설계 공유: [2026-05-09-engine-y-variable-ortools-design.md](./2026-05-09-engine-y-variable-ortools-design.md)
스코프: Gurobi 솔버만. 모델 의미는 OR-Tools 구현과 동일.

## 목표

PR #37에서 OR-Tools 솔버에 도입한 `y[d] ∈ {0, 1}` 명시적 결정변수를 Gurobi 솔버에 미러한다. 두 솔버는 동일한 MIP 모델을 표현하므로, 같은 입력에 대해 동등한 결과(경로·비용·시간)를 반환해야 한다.

모델 의미, 배경, 동작 동등성 분석은 OR-Tools 설계 문서에서 상세히 설명한다. 이 문서는 **Gurobi API 차이**와 **테스트 전략**에 집중한다.

## 비목표

OR-Tools 설계 문서와 동일. 추가로:
- OR-Tools 솔버 수정 — 이미 PR #37에서 완료.
- Gurobi WLS 라이센스 조달 — 운영 환경은 OR-Tools 전용; Gurobi는 선택적 백엔드.

## Gurobi API 차이

OR-Tools(CP-SAT)와 Gurobi는 같은 MIP를 다른 API로 표현한다.

### 결정변수 선언

```python
# OR-Tools (CP-SAT)
y_city = {c: model.new_bool_var(f"y_city_{c}") for c in graph.internal_cities}
y_hub  = {h: model.new_bool_var(f"y_hub_{h}")  for h in graph.hubs}

# Gurobi
y_city = m.addVars(graph.internal_cities, vtype=GRB.BINARY, name="y_city")
y_hub  = m.addVars(graph.hubs,            vtype=GRB.BINARY, name="y_hub")
```

`m.addVars`는 iterable을 받아 `{key: Var}` 형태의 `tupledict`를 반환한다. 개별 변수 접근은 `y_city[c]`, `y_hub[h]`.

### 제약 표현

```python
# OR-Tools
model.add(sum(x[i] for i in idx) == y_hub[h])

# Gurobi
m.addConstr(gp.quicksum(x[e] for e in entry_out_edges) == y_hub[h])
```

`gp.quicksum`은 대규모 합산 시 Python `sum`보다 빠르다. Gurobi `addConstr`는 즉시 모델에 등록된다.

### 변수 값 읽기

```python
# OR-Tools
solver.value(y_city[c])   # → int

# Gurobi
y_city[c].X               # → float (e.g. 0.9999999)
int(round(y_city[c].X))   # → int (0 or 1)
```

Gurobi BINARY 변수는 최적해 후에도 `.X`가 float을 반환한다. `int(round(...))` 로 정수화 필수.

### Subtour Elimination

OR-Tools는 Iterative DFJ(루프 내 재풀기), Gurobi는 lazy callback(Branch & Cut)을 사용한다. `y[d]` 변수는 callback 내부에서 접근하지 않으므로 callback 구조 변경은 없다.

## y_hub 정의 — 주의사항

OR-Tools 설계 문서와 동일한 semantics:

- `y_hub[h] == Σ x[(h_Entry, *)]` — h_Entry로부터의 outflow 합
- `Hub_Stay` 에지는 0-cost shortcut이며 방문 indicator **아님**
- 시작 허브는 `start_out == 1` 제약으로 자동 `y_hub == 1`
- `required_countries` 내 허브는 **start_hub 포함 전부** `y_hub == 1` 핀

```python
# 올바른 정의
for h in graph.hubs:
    entry_out_edges = [e for e in edge_dict if e[0] == f"{h}_Entry"]
    m.addConstr(gp.quicksum(x[e] for e in entry_out_edges) == y_hub[h])

# 잘못된 정의 (Hub_Stay 에지만으로 y 정의하면 안 됨)
# m.addConstr(x[(f"{h}_Entry", f"{h}_Exit", "Hub_Stay")] == y_hub[h])  ← 오류
```

## 흐름 보존 제약 변경

기존 Gurobi 모델은 허브 가상 노드를 `"_Entry" in n or "_Exit" in n` substring 매치로 구분했다. 신 모델은 OR-Tools와 동일하게 명시적 집합 `hub_virtual_nodes`를 사용한다.

```python
hub_virtual_nodes = {f"{h}_Entry" for h in graph.hubs} | {f"{h}_Exit" for h in graph.hubs}
```

## 테스트 전략

### WLS 라이센스 부재 처리

로컬 개발 환경과 일반 CI에는 WLS 환경변수가 없다. `GurobiSolver.__init__()`은 환경변수 미설정 시 `SolverInitializationError`를 raise하므로, fixture 단계에서 실패한다.

해결: `pytestmark = pytest.mark.skipif(not (HAS_GUROBI and HAS_WLS), reason="...")`를 모듈 레벨에 선언해 **fixture 생성 이전**에 전체 모듈을 skip한다.

```python
HAS_WLS = all(
    os.environ.get(k)
    for k in ("GUROBI_LICENSE_ID", "GUROBI_WLS_ACCESS_ID", "GUROBI_WLS_SECRET")
)

pytestmark = pytest.mark.skipif(
    not (HAS_GUROBI and HAS_WLS),
    reason="gurobipy 또는 WLS 환경변수 미설정"
)
```

### CI 통합

WLS secrets(`GUROBI_LICENSE_ID`, `GUROBI_WLS_ACCESS_ID`, `GUROBI_WLS_SECRET`)를 GitHub Actions secrets에 등록하면 CI에서도 Gurobi 테스트가 실행된다. secrets 미등록 시 skip — OR-Tools 76 tests는 항상 실행.

### 테스트 클래스 구조

OR-Tools `TestOrToolsYVariable`과 동일한 invariant를 `TestGurobiYVariable`로 미러:

- `test_y_values_exposed_after_solve` — `_last_y_values` 노출, keys/values 타입 검증
- `test_y_hub_matches_visited_iata` — `y[h] == 1 ↔ h ∈ visited_iata`
- `test_y_city_matches_visited_cities` — `y[c] == 1 ↔ c ∈ visited_cities`
- `test_required_countries_pinned_to_one` — required 허브와 자식 도시 핀 검증

## 영향도

- 코드 변경: `engine/src/solvers/gurobi.py` + `engine/tests/test_solvers_gurobi.py` 신규
- API 계약: 변경 없음
- OR-Tools 76 tests: 회귀 없이 전부 통과해야 함
- 운영: production은 OR-Tools 전용. Gurobi WLS 미주입 상태라 이번 변경의 운영 영향 0.
