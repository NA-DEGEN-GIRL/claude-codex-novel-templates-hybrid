"왜?", "어떻게?" 질문을 생성하고, 본문에 답이 있는지 검사한다. 설정 구멍/플롯 홀 탐지.

## 사용법

```
/why-check                      # 전체 소설 (text mode, default)
/why-check full                 # 전체 (text mode, 명시적)
/why-check text arc-03          # 특정 아크 (text mode, 명시적)
/why-check arc-03               # 특정 아크 (text mode, plan 없으면 text)
/why-check 41-51                # 범위 지정 (text mode)
/why-check plan arc-06          # 플롯 사전 검증 (Planning Mode)
/why-check delta                # 수정된 화수 + 인접 1화만 재검증
```

> `text`는 기본 모드의 명시적 별칭이다. `plan`이 없으면 모두 Text Mode로 처리한다.
> `/why-check full`과 `/why-check text full`은 동일하다.

## 실행

1. `.claude/agents/why-checker.md`를 읽고 지시에 따른다.
2. **기본은 text-only** — 에피소드 본문만으로 판단. 단, 다음은 예외:
   - CLAUDE.md §5.1 (intentional mysteries) — Phase 2 후 참조
   - `plan` 모드 — plot 파일이 입력
   - (OAG는 별도 에이전트 `/oag-check`가 담당. why-check는 설명 누락만.)
3. **Phase 1 (질문 생성)은 반드시 1화부터 순서대로 읽는다. 병렬 금지.** Phase 2 (답 검색)는 질문 목록 확정 후 병렬 가능.
4. 산출물:
   - text/full 모드: `summaries/why-check-report.md`
   - plan 모드: `summaries/why-check-plan-{arc}.md`
   - delta 모드: 기존 report에 resolved/new/still-missing 분류 추가
