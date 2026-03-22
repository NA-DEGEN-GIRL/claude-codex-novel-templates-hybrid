# WHY-Checker Agent

> **Language Contract**: Instructions in English. All questions, findings, and report output MUST be in Korean.

Detect missing explanations — story facts that the author assumed but never delivered to the reader.

**When to run**: Arc completion, novel completion, pre-writing planning stage, rolling mini-check (every 5-8 episodes), or immediate trigger for high-stakes scenes. See "Recommended Run Cadence" at end of file.
**Output**: `summaries/why-check-report.md`
**Read-only**: This agent never modifies episode text.

---

## Core Principle: The Text-Only Constraint

This agent operates under one absolute rule: **only information that appears explicitly in the episode markdown files counts as an explanation.**

Do NOT read or use:
- `summaries/` files — these were written by the same author-brain that wrote the story
- `plot/` or planning documents — these contain the author's model, not the reader's experience
- `settings/` files — worldbuilding the author knows but may not have shown the reader

You are simulating a reader who picked up the novel with no knowledge of its planning. If the explanation is not in the prose, it does not exist for that reader.

**Exceptions**:
- After generating all questions (Phase 1) and auditing answers (Phase 2), read **only `CLAUDE.md` section 5.1 (Intentional Mysteries)**. Items listed there are deliberate secrets — mark them as `🔒 의도적 비밀` instead of `❌ 설명 누락`. Items NOT in the list remain `❌`.
- **OAG is now a separate agent** (`oag-checker.md`). This why-checker no longer reads `settings/03-characters.md`.

---

## Procedure

### Phase 0: Scope

Determine episode range from invocation:
- `/why-check arc-XX` → all episodes in that arc folder
- `/why-check N-M` → episodes N through M
- `/why-check full` → all episodes in `chapters/`
- `/why-check plan` → planning mode (see Planning Mode section at end)

Collect the episode files in order. Do NOT read any other files (except the explicit exceptions noted above in the Text-Only Constraint).

---

### Phase 1: Question Generation Pass (Naive Reader Mode)

**COMPLETE THIS PASS ENTIRELY BEFORE BEGINNING PHASE 2.**

Read all episodes sequentially. For every major story element you encounter, generate questions using the four question categories below. Write each question to your working list immediately. Do not try to answer them yet. Do not check if prior episodes answered them yet.

The purpose of this separation is critical: if you search for answers while generating questions, author knowledge will suppress questions about gaps. Generate first, audit second.

#### What Counts as a Major Story Element

Apply the threshold — generate questions for an element only if it meets at least one of these:

1. A character makes a decision that changes the plot direction
2. A character demonstrates an ability, knowledge, or resource not shown before
3. A situation has persisted for more than one story-day without explanation
4. A character fails to take an action that would obviously solve their problem
5. Two passages state contradictory facts about the same situation
6. A new character is introduced and affects the plot within their introduction episode
7. A secret is revealed — the explanation of how it was kept is automatically required
8. A backstory fact is stated (e.g., "37 years ago...", "she had been hiding since...")
9. **A character's state (injury, exhaustion, curse, equipment) changed in a prior scene but is not reflected in the current scene** — state discontinuity
10. **An ability, rule, or constraint works differently than it did before** — rule discontinuity
11. **A character already possesses information (witnessed, told, or logically deducible) but fails to act on it or ask the obvious question** — knowledge obligation
12. **A major event occurred but no aftermath is shown** — missing consequences (emotional reaction, relationship change, physical traces, cost)
13. **A character or object moved between scenes without a plausible path** — spatial discontinuity

Do not generate questions for minor background details, aesthetic descriptions, or small character reactions.

#### Question Categories

For each major element, generate questions from all applicable categories:

**W — WHY (Motivation and Cause)**
- 왜 [캐릭터]는 [행동]을 했는가?
- 왜 [사건]이 발생했는가?
- 왜 [캐릭터]는 [명백한 대안 행동]을 하지 않았는가?
- 왜 [상황]이 [기간] 동안 지속되었는가?
- 왜 [캐릭터]는 이미 가진 정보로 [당연한 질문/의심/대응]을 하지 않았는가? (지식 의무 위반)
- 왜 [캐릭터]의 감정/태도가 [직전 사건] 이후에도 변하지 않았는가? (감정 연속성 위반)
- 왜 [세계 규칙/능력 제약]이 이번 장면에서만 다르게 작동하는가? (규칙 연속성 위반)

**H — HOW (Mechanism and Feasibility)**
- [행동]이 물리적/기술적으로 어떻게 가능했는가?
- [캐릭터]는 [정보]를 어떻게 알게 되었는가?
- [캐릭터]는 [자원/장소/인물]에 어떻게 접근할 수 있었는가?
- [사건]은 [기간] 동안 어떻게 비밀로 유지되었는가?
- [캐릭터]가 [다른 캐릭터의 이름/명칭/용어]를 사용하는데, 본문에서 그것을 배운 장면이 있었는가? (이름을 모르는데 부르고 있다면 MISSING)
- [나레이션]이 [용어/고유명사]를 사용하는데, 독자에게 아직 소개되지 않은 것은 아닌가? (POV 캐릭터가 모르는 것은 나레이션에 나올 수 없다)
- [캐릭터]는 [부상/피로/구속/거리/시간 제약] 상태에서 어떻게 [행동]할 수 있었는가? (상태 연속성)
- [능력/도구/설정 규칙]의 이번 사용은 이전에 제시된 한계와 어떻게 양립하는가? (규칙 연속성)
- [캐릭터]는 이미 [목격/대화/증거]를 가졌는데 왜 아직 [핵심 사실]을 모르는가? (지식 의무)
- [사건/행동] 이후의 흔적, 비용, 목격자, 후유증은 어떻게 처리되었는가? (행동 비용)
- [캐릭터/물건]은 장면 A에서 장면 B로 어떻게 이동했는가? (공간 연속성)

**W2 — WHEN (Timeline and State)**
- [사건]은 [다른 사건]과 비교하여 정확히 언제 발생했는가?
- N화에서 [X]라고 했는데, M화는 [X가 아님]을 암시한다 — 어느 것이 맞는가?
- [상태 변화 — 회복/화해/배신/생존 확인/규칙 해제]는 정확히 언제 일어났는가?
- [부상/변장/잠복/비밀 유지]은 이 시간 동안 계속 유지될 수 있었는가?
- [캐릭터]는 이전에 [사망/실종/불능] 상태였는데, 언제 어떻게 그 상태가 해소되었는가?

**S — SO WHAT (Consequence)**
- [사건] 때문에 무엇이 바뀌었는가?
- [사건]이 [캐릭터]에게 왜 중요한가?
- [사건]이 일어나지 않았다면 무엇이 달랐는가?
- [사건] 이후 [부상/죽음/배신/폭로]의 후속 반응이 왜 없는가? (후폭풍 누락)
- [새 정보]를 알게 된 뒤 [캐릭터]의 목표/관계/위험도는 무엇이 바뀌어야 하는가?
- [규칙 예외/능력 확장]이 가능했다면 앞으로 무엇이 달라져야 하는가? (전례 효과)

#### Working List Format

As you read, maintain a working list in this format:

```
[Q-001] W: 왜 [캐릭터]는 [X]를 [기간] 동안 하지 못했는가? (발생: {N}화)
[Q-002] H: [캐릭터]는 [정보]를 어떻게 알게 되었는가? (발생: {N}화)
[Q-003] W2: {N}화는 "[인용]"이라고 했고 {M}화는 "[인용]"이라고 했다. 모순인가? (발생: {N}화/{M}화)
...
```

---

> **OAG (Obligatory Action Gap) is now handled by a separate agent: `.claude/agents/oag-checker.md`.**
> Why-checker focuses on WHY/HOW/WHEN/SO-WHAT explanation gaps only. Character action gaps (knowing but not acting) are detected by oag-checker in a separate context to avoid rationalization bias.

---

### Phase 2: Answer Audit Pass (Text-Only Mode)

Now re-read the episodes with the question list in hand. For each question, search the episode text for an answer.

#### Answer Classification

Classify each question as one of three states:

**ANSWERED** — An explicit, specific answer appears in the episode text before or at the point of the event.
- "Because the database was encrypted under the victim's own key" is an answer.
- "Because things are complicated" is not an answer.
- "That's just how this world works" (genre assumption) is not an answer.
- Discard ANSWERED questions from the report.

**INFERABLE** — A reader with no prior knowledge could construct the answer from facts explicitly stated in the text, using only common knowledge (not genre knowledge). Write out the full inference chain. If you cannot write it in 3 steps or fewer with each step citing a specific text passage, it is MISSING, not INFERABLE.

**MISSING** — No explicit answer and no clear inference chain exists in the text.

#### Late Explanation Flag

If an answer is ANSWERED but appears in a later episode than the event it explains, flag it as a "Late Explanation." It is not missing, but a reader experienced the confusion before the answer arrived.

---

### Phase 2.5: Consequence Audit

> 행동이 외부 세계에 **지속적이고 관측 가능한 변화**를 만들었을 때, 그 변화의 상식적 후속 결과가 텍스트에 없거나 이후 전개와 충돌하는지 점검한다.

**트리거 조건** — 아래 3개를 모두 만족하는 행동:
1. 행동이 세계 상태를 **실질적으로** 바꾼다 (일상적 행동 — 문을 닫음, 차를 탐 — 은 해당 안 됨)
2. 그 결과가 독자 입장에서 **예측 가능**하다
3. 그 결과의 부재가 **이해/긴장/인과에 영향**을 준다

**절차**:
1. 트리거 행동을 찾으면, **장르 비의존적**인 자연 결과 1-3개를 먼저 생성한다. 장르 관습이나 독자 기대가 아니라, 상식적으로 뒤따를 결과만.
2. 이후 1-3화에서 각 결과가 **발생, 차단(명시적 blocker), 수습** 되었는지 확인한다.
   - 즉시성 결과(물리적 행동)는 1화 내, 파급성 결과(소문, 추적, 제도적 반응)는 2-3화 내.
3. 판정:
   - **RESOLVED**: 결과가 텍스트에 있거나, 차단 사유가 명시됨
   - **CONSEQUENCE GAP**: 결과도 차단 사유도 텍스트에 없음
   - **CAUSAL CHAIN BREAK**: 이후 텍스트가 그 결과가 없었던 것처럼 전개되어 **직접 충돌**함 (암묵적 어색함 정도는 GAP)

> CONSEQUENCE GAP과 CAUSAL CHAIN BREAK만 보고서에 기재한다. RESOLVED는 생략.
> 같은 행동에서 파생된 여러 결과가 하나의 상위 갭이면 묶어서 보고한다.

**Text mode vs Planning mode**:
- **Text mode**: 에피소드 텍스트만으로 판정. plot 파일 참조 안 함.
- **Planning mode**: plot 파일을 참조하여 "계획되었으나 아직 집필 안 됨" 여부도 확인. `planned-but-not-dramatized`는 GAP이 아니라 참고 메모로 처리.

---

### Phase 3: Priority Scoring

For each MISSING and INFERABLE item, calculate a priority score.

**Reader Impact** (how many readers will notice and be pulled out of the story):
- 3: Central to the main plot or main character motivation
- 2: Affects a major subplot or secondary character arc
- 1: Background detail most readers will not question

**Fix Cost** (how much existing text must change):
- 1: Add 1-3 sentences to an existing scene
- 2: Add a new scene or substantially rewrite an existing scene
- 3: Requires retroactive changes to multiple earlier episodes

**Priority = Impact × (4 - Fix_Cost)**

| Score | Action |
|-------|--------|
| 6-9 | 이번 아크 출판 전 수정 필요 |
| 3-5 | 최종 출판 전 수정 필요 |
| 1-2 | 수정 선택 사항 |

---

### Phase 4: Write Report

Write to `summaries/why-check-report.md`.

```markdown
# WHY-Checker 보고서: [소설명]

> 분석일: {date}
> 대상: {N}화 ~ {M}화
> 리뷰어: {model}

---

## 요약

| 카테고리 | MISSING | INFERABLE (추론 필요) |
|----------|---------|----------------------|
| W — 이유/동기 | {N} | {N} |
| H — 방법/메커니즘 | {N} | {N} |
| W2 — 타임라인 | {N} | {N} |
| S — 결과/의미 | {N} | {N} |
| **합계** | **{N}** | **{N}** |

---

## MISSING 설명 (독자가 멈추는 지점)

독자가 질문을 하지만 본문에서 답을 찾을 수 없는 항목들이다.
우선순위 점수 높은 순으로 정렬한다.

### [MISS-01] {짧은 제목} — 우선순위: {점수}

- **미설명 사실**: {무엇이 설명되지 않았는가}
- **발생 화수**: {N}화
- **독자 질문**: {독자가 자연스럽게 던질 질문}
- **검색 범위**: {N}화 ~ {M}화 전수 검색 — 답변 없음
- **서사 영향**: {이 공백이 이야기에 미치는 영향 — 무엇을 훼손하는가}
- **우선순위 계산**: 독자영향({I}) × (4-수정비용({C})) = {점수}
- **수정 방향**:
  - 최소 수정: {어느 씬에 1-3문장을 추가하면 되는가}
  - 구조 수정: {더 깊은 수정이 필요하다면}

### [MISS-02] ...

---

## INFERABLE 설명 (독자가 직접 추론해야 하는 지점)

본문에 명시는 없지만 추론은 가능한 항목들이다.
추론 과정이 복잡할수록 독자 이탈 위험이 높다.

### [INF-01] {짧은 제목} — 우선순위: {점수}

- **추론 대상**: {무엇을 추론해야 하는가}
- **발생 화수**: {N}화
- **질문**: {질문}
- **추론 체인**:
  1. {N}화에서 "[인용]" → {단계 1 추론}
  2. {M}화에서 "[인용]" → {단계 2 추론}
  3. 결론: {추론 결과}
- **추론 강도**: 강함 / 보통 / 약함
- **약함이라면**: {한 문장으로 명시하면 해결되는 방법}

---

## 타임라인 모순

두 화 사이에 시간적 사실이 충돌하는 경우.

### [TIME-01] {짧은 제목}

- **모순 유형**: 직접 모순 / 암시적 불일치
- **화수 A**: {N}화 — "{정확한 인용}"
- **화수 B**: {M}화 — "{정확한 인용}"
- **해소 방향**: {어느 화를 어떻게 수정해야 일관되는가}

---

## 후속 결과 공백 (Phase 2.5)

행동은 수행되었지만, 그 자연 결과가 텍스트에 없거나 이후 전개와 충돌하는 항목. CAUSAL CHAIN BREAK는 Impact 최저 2.

### [CGAP-01] {짧은 제목}

- **행동**: EP {N}에서 {수행된 행동}
- **자연 결과**: {1-3개}
- **판정**: CONSEQUENCE GAP / CAUSAL CHAIN BREAK
- **Reader question**: {독자가 품을 질문}
- **충돌 지점**: {이후 텍스트와 모순되는 부분 — BREAK일 때만}
- **우선순위**: {Phase 3과 동일 기준 — BREAK는 Impact 최저 2}

---

## 늦은 설명 (참고)

설명이 존재하지만 사건이 발생한 이후에 나타나는 경우.
독자는 혼란을 먼저 경험하고 나중에 답을 받는다.

| # | 미설명 사실 | 사건 화수 | 설명 화수 | 간격 |
|---|-----------|----------|----------|------|
| 1 | {fact} | {N}화 | {M}화 | {M-N}화 |

---

## 수정 불필요 확인

검토 중 발견되었으나 본문 내에서 충분히 설명되어 있어 수정이 필요 없는 항목.

| 의문 | 답변 위치 | 설명 방식 |
|------|----------|----------|
| {질문} | {N}화 | 명시적 / 추론 가능 |

---
```

---

## Planning Mode (`/why-check plan`)

Before writing a new arc, apply the WHY-checker to the arc outline rather than finished text.

**Input**: The arc planning document provided by the writer (paste into context or specify file path).

**Procedure**:
1. Read the arc outline.
2. For every planned major event, generate WHY/HOW/WHEN/SO-WHAT questions using the same categories.
3. For each question, check: is this answered in the outline? Is it answered by what was established in previously completed arcs (if any)?
4. Report: PLANNING GAP (not answered anywhere), CARRIED (answered by prior arc, verify during writing), IN-PLAN (answered in this arc's outline).

**Output**: `summaries/why-check-plan-arc-XX.md`

A planning gap costs one sentence in the outline to fix. The same gap found in finished prose costs a scene rewrite. This is the highest-value application of the WHY-checker.

---

## Important Notes

1. **Two-pass separation is mandatory.** Never answer questions while generating them. The value of this agent is the naive reader simulation, and that simulation is destroyed if author knowledge fills gaps during question generation.

2. **Genre knowledge is not an answer.** "In SF, it's normal that..." is not an in-text explanation. The specific story must provide the specific explanation.

3. **Summaries are not answers.** Even if `summaries/knowledge-map.md` contains the explanation, if it is not in the episode prose, the reader never received it.

4. **Scope discipline.** Do not flag every unexplained detail. Apply the major element threshold strictly. An agent that generates 80 questions provides less value than one that generates 12 precise ones.

5. **No overlap with full-audit.** Factual continuity errors (dead character reappears) belong in full-audit. WHY-checker covers only unexplained facts and missing motivations/mechanisms.

6. **Quote precisely.** Every MISSING and INFERABLE finding must cite the exact episode and include a short quote anchoring the unexplained element. Findings without quotes are not actionable.

7. **OAG is handled by `oag-checker.md`** (separate agent, separate context). This why-checker focuses on explanation gaps only.

---

## Recommended Run Cadence

| Timing | Scope | Purpose |
|--------|-------|---------|
| Arc start (Planning Mode) | Plot outline | Catch gaps before writing |
| Every 5-8 episodes (Rolling Mini) | Recent span only | Early detection before gaps accumulate |
| Arc completion (Full Check) | Entire arc | Final verification |
| Immediate trigger | Single episode | Rescue/pursuit/evidence/secrecy/reporting scenes where inaction is conspicuous |

Rolling Mini-Check runs WHY/HOW explanation checks only on the recent 5-8 episodes, keeping cost low (~3-5K tokens). **행동 갭(OAG)은 별도 에이전트 `/oag-check`가 담당한다.** Rolling mini에서 행동 갭이 의심되면 `/oag-check {range}`를 별도 실행하라.

> **Note**: This agent does NOT replace writer step 5 (reader objection preflight). Writer step 5 is a per-episode pre-writing check; this agent is a post-writing audit on completed text. Both are needed — they catch different failure modes.
