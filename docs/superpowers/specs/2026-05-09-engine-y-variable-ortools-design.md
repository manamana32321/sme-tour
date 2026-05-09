# 엔진 모델 교체: `y[d]` 도시 방문 결정 변수 도입 (OR-Tools)

작성: 2026-05-09
관련 이슈: [manamana32321/sme-tour#29](https://github.com/manamana32321/sme-tour/issues/29)
스코프: OR-Tools 솔버만. Gurobi는 후속 PR.

## 목표

`y[d] ∈ {0, 1}` 명시적 결정변수를 도입해 도시 방문 여부를 모델 수준에서 표현한다. 기존 모델은 흐름 보존(in==out) 만으로 방문을 암묵 표현하며, 향후 도시별 체류시간([#30](https://github.com/manamana32321/sme-tour/issues/30)) 또는 도시 단위 명시 선택([#31](https://github.com/manamana32321/sme-tour/issues/31)) 같은 확장이 어렵다. 이번 변경은 표현력만 확장하고 동작은 동등하게 유지한다.

## 비목표

- 동작/응답 변경. 동일 입력에 대해 머지 전과 동일한 경로·비용·시간 응답을 보장한다.
- API 계약 변경. `OptimizeRequest`/`OptimizeResult` 모두 그대로.
- Gurobi 솔버 변경. 별도 PR.
- 도시별 체류시간(stay_days), 도시 단위 명시 선택(required_cities) 도입. 후속 이슈.

## 배경

[10주차 노션 코드](https://www.notion.so/32cd32f6b7c2802c9cb7e80545915c98)의 신모델은 `y[d]`를 명시 도입해 다음을 한 번에 풀어냈다.

- `y[d] = 1` ↔ 도시 d 방문 (binary, deterministic)
- `MustVisit / DoNotVisit`을 `y[d] == 1 / 0`으로 1줄에 표현
- `stay_time = Σ stay_days[d] · 1440 · y[d]`로 시간 제약에 체류시간 자연 합산

현재 [engine/src/solvers/ortools.py](https://github.com/manamana32321/sme-tour/blob/main/engine/src/solvers/ortools.py)는 `x[edge]`만 의사결정변수로 두고, 흐름 보존 식의 우변 상수(`== 1` vs `== flow`)로 방문 여부를 결정한다. 이 방식은 stay_time 합산이나 명시적 도시 선택을 표현할 식 자체가 없다.

## 설계

### 결정변수 — `y[d]` 도시 단위

- 내륙 도시: 노드 1개당 `y` 1개. `Graph.virtual_nodes` 중 `_City` 접미사 노드 30개에 매핑.
- 허브 도시: Entry/Exit 가상 노드 2개를 묶어 허브 자체에 `y` 1개. `Graph.hubs` 15개에 매핑.
- 총 45개 binary 변수 추가. `BoolVar` (CP-SAT) 사용.

키 명명: `y[node_or_hub_iata]`. 예: `y["CDG"]`, `y["NCE_City"]`, `y["Bruges_City"]`.

### 제약 변경

기존 흐름 보존 (요지):
```
∀ 노드 n:
  if n is internal city and city's hub in required_countries:
    Σ x[(*, n)] == 1, Σ x[(n, *)] == 1
  else:
    Σ x[(*, n)] == Σ x[(n, *)]
```

신 흐름 보존:
```
∀ 내륙 도시 c:
  Σ x[(*, c)] == y[c]
  Σ x[(c, *)] == y[c]

∀ 허브 h:
  Σ x[(*, h_Entry)]  == Σ x[(h_Entry, *)]    # Entry 통과 흐름 보존 (기존과 동일)
  Σ x[(*, h_Exit)]   == Σ x[(h_Exit, *)]     # Exit 통과 흐름 보존 (기존과 동일)
  Σ x[(h_Entry, h_Exit, "Hub_Stay")] == y[h]  # Hub_Stay 에지 사용 ↔ 허브 방문
```

신 필수 방문 고정 (기존 의미 1:1 매칭):
```
∀ h ∈ required_countries:
  y[h] == 1

∀ c ∈ {도시 c | hub_of(c) ∈ required_countries}:
  y[c] == 1
```

### 동작 동등성

기존 모델과 신 모델은 같은 feasible region을 가져야 한다.

- `required_countries`로 `y[d] == 1` 고정된 노드: 기존 `Σ x == 1` 제약과 동일한 의미 ✓
- `required_countries` 외 노드: `Σ x == y[d]`이고 `y[d]` 자유. `y[d] = 1`이면 `Σ x == 1`, `y[d] = 0`이면 `Σ x == 0`. 기존 `Σ x_in == Σ x_out` 자유와 사실상 동일 ✓
- 목적함수 변화 없음. `y` 변수가 목적함수에 등장하지 않으므로 최적해 동일.

검증: 71 기존 tests를 그대로 통과해야 한다.

### 결과 응답

`OptimizeResult.visited_iata`, `visited_cities`는 기존처럼 route 재구성 후 추출. 솔버 응답에서 `y[d]` 값을 직접 읽지 않는다 (응답 invariant: `y[d] = 1 ↔ d ∈ visited_*`은 신 invariant 테스트로 검증).

## 테스트

### 기존 71 tests — 회귀 검증

전부 통과해야 한다. 실패하면 동작 동등성이 깨진 것.

### 신규 invariant 테스트 (~5개)

`engine/tests/test_solvers_ortools.py`에 추가.

- `y[h] == 1 ↔ h ∈ visited_iata`: 모든 15개 허브에 대해.
- `y[c] == 1 ↔ c ∈ visited_cities`: 30개 내륙 도시에 대해.
- `y[h] == 0 → 해당 허브 Entry/Exit 사용 흐름 == 0` (스킵된 허브는 아예 통과도 안 함).
- `required_countries 안의 모든 허브와 그 자식 내륙 도시는 y == 1`.
- 작은 시나리오(허브 3개 + 내륙도시 2개)에서 모델 솔브 후 `y` invariant 직접 assert.

신규 테스트는 솔버에 `y` 변수 노출이 필요하므로 솔버 내부에서 `y` dict를 임시 저장하고 디버그용 인터페이스(`solver._last_y_values`)로 노출. 프로덕션 응답에는 영향 없음.

## 영향도

- 코드 변경: `engine/src/solvers/ortools.py` 한 파일 + `engine/tests/test_solvers_ortools.py` 추가/확장.
- API 계약: 변경 없음.
- 응답 동등: 같은 입력 → 같은 응답 (route 순서, 비용, 시간, objective_value 모두).
- 성능: BoolVar 45개 + 추가 흐름 제약. CP-SAT은 binary 변수 추가에 강건. 실측에서 5초→6초 미만 예상. 측정해서 회귀 시 별도 처리.
- 운영: 현재 production은 OR-Tools만 사용. Gurobi는 fallback으로 등록되어 있지만 WLS 라이센스 미주입 상태라 활성화되지 않음. 따라서 이번 PR과 다음 Gurobi PR 사이에 운영 영향 0.

## 롤아웃

1. PR 머지 → GHA 엔진 이미지 빌드 → Image Updater write-back → ArgoCD sync → pod 롤아웃 (~5분).
2. 자동 검증:
   - production `/optimize` 에 동일 페이로드 머지 전/후 호출 → 응답 SHA 비교 (별도 스크립트 1회 실행).
   - blackbox probe 알람 비활성 확인.
3. 회귀 발견 시: GHCR 이전 이미지 SHA로 [k8s/deployment.yaml](https://github.com/manamana32321/sme-tour/blob/main/k8s/deployment.yaml) 일시 pin → ArgoCD 즉시 롤백 → 재현/수정 후 재머지.

## 의존 이슈

후속 이슈가 이번 PR을 의존:
- [#30](https://github.com/manamana32321/sme-tour/issues/30) `stay_days` — `y[d]`에 stay_time 곱하는 식 작성
- [#31](https://github.com/manamana32321/sme-tour/issues/31) `required_cities` — `y[c] == 1`로 명시 고정

이번 PR은 이들의 표현 기반만 깐다. 실제 기능은 후속 PR.

## Out of scope (이번 PR이 다루지 않는 것)

- Gurobi 솔버 변경 (별도 PR)
- 도시별 체류시간 (#30)
- 도시 단위 명시 선택 (#31)
- API 계약 변경
- 프론트엔드 변경
