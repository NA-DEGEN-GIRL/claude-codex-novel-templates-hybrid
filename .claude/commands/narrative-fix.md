서사 리뷰, WHY-CHECK, 또는 OAG 보고서를 기반으로 수정한다.

## 사용법

```
/narrative-fix                    # narrative-review 보고서 기반 (기본)
/narrative-fix C1,H1,H2          # 특정 항목만 수정
/narrative-fix --source why-check # why-check 보고서 기반 (설명 보강)
/narrative-fix --source why-check --scope priority-6+  # 고우선도만
/narrative-fix --source arc-read # arc-readthrough 기반 (흐름 결함 수정)
/narrative-fix --source oag      # oag-report 기반 (행동 갭 메우기)
/narrative-fix --source oag --items OAG-01,OAG-02  # 특정 항목만
```

## 세 가지 모드

### 기본 모드 (narrative-review 기반)
- 입력: `summaries/narrative-review-report.md`
- 전략: S1~S6 (구조적 서사 수정)
- 범위: 제한 없음 (다화 수정, 장면 재구성 가능)

### WHY-CHECK 모드 (`--source why-check`)
- 입력: `summaries/why-check-report.md`
- 전략: E1~E4 (경량 설명 보강)
- 범위: **항목당 1~3문장, 단일 화수, 기존 장면 내부 삽입만**
- **MISSING + CONSEQUENCE GAP** 기본 대상. INFERABLE은 `--promote` 시만.
- **CAUSAL CHAIN BREAK → 자동 HOLD** (plot-repair 또는 narrative-review로 이관)

### Arc-Read 모드 (`--source arc-read`)
- 입력: `summaries/arc-readthrough-report.md`
- 전략: R1~R4 (중복 제거 / 순서 조정 / 반응 보강 / 전환 매끄럽게)
- 최소 수정 우선이나, 흐름을 살리기 위해 필요한 만큼 자유롭게 수정
- `patch-feasible: yes` 항목만 처리. `[HOLD]` 항목은 `/narrative-review`로 이관.

### OAG 모드 (`--source oag`)
- 입력: `summaries/oag-report.md`
- 전략: A1~A3 (행동 갭 메우기 — blocker 명시 / 판단 독백 / 행동 삽입)
- 범위: **항목당 1~3문장, 단일 화수**
- oag-report의 "Missing info"를 읽고, **캐릭터 성격에 맞는 방식**으로 본문에 메운다
- oag-checker가 "뭐가 빠졌는지" 알려주면, narrative-fixer가 "어떻게 메울지" 결정

## 실행

1. 해당 보고서 파일이 없으면 해당 체커를 먼저 실행하라고 안내.
2. `.claude/agents/narrative-fixer.md`를 읽고 지시에 따른다.
3. 수정 전 계획을 사용자에게 보여주고 승인을 받는다.
4. **최소한의 수정으로 해결할 수 있으면 그렇게 한다.** 단, 서사가 구조적으로 변경되어야 하는 경우에는 유연하게 대응한다. 무조건 최소 수정만 고집하지 않는다.
5. 산출물: 수정된 에피소드 + 해당 로그 (`narrative-fix-log.md` / `why-fix-log.md` / `oag-fix-log.md`)
