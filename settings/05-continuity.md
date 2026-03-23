# Continuity Management

> Continuity verification is performed by the project's primary review workflow.
> Summary file updates are performed by the project's primary writing pipeline during post-processing.
> This file defines EPISODE_META writing rules and per-novel continuity settings.

**Language Contract: All narrative output, summaries, and review text MUST be in Korean.**

---

## EPISODE_META Writing Rules

Write metadata at the end of each episode using the YAML template from the project's top-level operating document (`CLAUDE.md` or `CODEX.md`). Follow these rules:

1. **Record all characters**: Include every named character in `characters_appeared`
2. **Track state changes**: Injuries, emotional shifts, location changes MUST be recorded — this is the foundation for next-episode continuity
3. **Foreshadowing management**: New threads go in `unresolved`; resolved threads are removed and results reflected in `summary`
4. **Maintain unresolved list**: Remove resolved items from previous episodes, add new ones

---

## Per-Novel Continuity Settings

### Timeline Baseline

- **Starting point**: {{TIMELINE_START}} (e.g., "현대 2026년 3월", "D-Day", "서기 1234년 봄")
- **Time unit**: {{TIME_UNIT}} (e.g., "24시간제", "십이지시", "계절 단위")
- **Calendar system**: {{CALENDAR}} (e.g., "양력", "음력", "가상 달력")

### Continuity Invariants (불변 조건 표)

> 설정 여러 개를 조합해야 도출되는 "당연히 맞아야 하는" 사실을 명시적으로 기록한다.
> AI가 매번 추론하지 않도록, **한 번 도출한 뒤 여기에 승격**한다.
> writer와 reviewer는 이 표의 값을 본문 수치와 직접 대조한다.
> compile_brief에 자동 포함된다.

| # | 불변 조건 | 값 | 도출 근거 | 위반 시 영향 |
|---|---------|-----|---------|------------|
| I1 | {{INVARIANT_1}} | {{VALUE}} | {{SOURCES}} | {{IMPACT}} |
| I2 | {{INVARIANT_2}} | {{VALUE}} | {{SOURCES}} | {{IMPACT}} |

<!-- 작성 가이드:
- "사건 X는 인물이 N세일 때 발생" 처럼 나이/시점이 추론으로만 도출되는 것을 기록
- "회귀 시점이 17세 + 마적 습격이 1개월 후 = 마적 습격 시 17세" 같은 교차 추론 결과
- 03-characters, 04-worldbuilding에 흩어진 정보를 조합한 결과
- 명시적으로 한 곳에만 적혀있는 사실은 여기에 적지 않아도 됨 (원본에서 직접 확인 가능)
-->

### Key Timeline Markers

> 핵심 사건의 절대 시점. 이 표도 compile_brief에 자동 포함된다.

| 시점 | 사건 | 관련 인물 | 비고 |
|------|------|---------|------|
| {{TIMELINE_MARKER_1}} | {{EVENT}} | {{CHARACTERS}} | {{NOTE}} |

---

### Episode-Level Time Continuity Gate

> 아래 항목 중 하나라도 있으면 writer와 reviewer는 `settings/05-continuity.md`를 직접 대조한다.
> - 회상/과거 서술
> - "사흘 뒤", "한 달 전", "며칠째" 같은 상대 시간 표현
> - 이동 시간, 추적 기간, 수련 기간, 부상 회복 기간
> - 나이/학년/세대/동기처럼 시점에 묶인 인물 정보
> - 약속 만기, 습격 예정일, 회수 시점 같은 deadline

점검 질문:

1. 이번 화의 현재 시점은 직전 화 이후 얼마나 지났는가?
2. 회상 속 나이, 가족 상태, 소속, 사건 순서는 불변 조건 표와 timeline markers에 맞는가?
3. 이동/회복/수련/추적에 필요한 시간이 본문에서 실제로 확보되었는가?
4. "곧", "조만간", "한참 뒤" 같은 모호 표현이 기존 마감 이벤트와 충돌하지 않는가?
5. 확신이 없으면 `novel-calc` MCP의 날짜/기간 도구를 직접 호출하거나, 더 보수적인 서술로 낮춘다.

이 게이트는 선택 사항이 아니다. 시간축이 장면 기능에 영향을 주는 화에서는 반드시 통과해야 한다.

---

### Long-Term Continuity Management

#### Every 8~12 episodes (or at arc transitions)

1. **Character master sheet** (`03-characters.md`): Update changed relationships, add new characters
2. **Worldbuilding settings** (`04-worldbuilding.md`): Add newly revealed settings, update timeline
3. **Unresolved thread list**: Full thread inventory, check for long-outstanding unresolved threads (떡밥)

#### At part/arc transitions

- Write a full summary of the previous part
- Record character states as a reset point
- Sort unresolved threads into carry-forward vs. discard for the next part
- Classify arc findings into `patch-feasible` vs `HOLD` and record them in `summaries/review-log.md`
- If a `forward-fix` is chosen, sync it across `review-log.md`, `running-context.md`, and the next arc plot file
- If arc-boundary edits changed text, re-sync affected summaries and trackers before entering the next arc
- Reflect the next-episode runway in `summaries/running-context.md` before entering the next arc

---
