# {{NOVEL_TITLE}} - Writing Constitution

> This is the top-level ruleset for the novel "{{NOVEL_TITLE}}".
> All writing, editing, and review operations follow this document.

## Language Contract

- **Instructions** in this file and all settings/ files are in English for token efficiency.
- **All narrative output** (prose, dialogue, summaries, reviews, fixes) MUST be in **Korean**.
- **Korean examples** in this document are normative style targets, not optional references.
- Do NOT translate in-world terms, honorifics (존댓말/반말), or speech-level distinctions.
- When Korean examples conflict with abstract English instructions, **Korean examples win** for surface realization.

---

## 1. Project Overview

- **Title**: {{NOVEL_TITLE}}
- **Subtitle**: {{SUBTITLE}} (delete if none)
- **Genre**: {{GENRE}}
- **Tone & Mood**: {{TONE}}
- **Keywords**: {{KEYWORDS}}
- **Target Audience**: {{TARGET_AUDIENCE}}
- **One-line Summary**: {{ONE_LINE_SUMMARY}}
- **gemini_feedback**: true  <!-- set false to disable Gemini review -->
- **nim_feedback**: true  <!-- set true to enable NIM proofreading -->
- **nim_feedback_model**: "openai/gpt-oss-120b"
- **ollama_feedback**: false  <!-- set true to enable Ollama proofreading -->
- **ollama_feedback_model**: "gpt-oss:120b"
- **gpt_feedback**: false  <!-- hybrid: GPT가 집필하므로 GPT 리뷰 비활성 -->
- **illustration**: false  <!-- set true to generate episode illustrations. Cover is always generated -->

### 1.1 Core Promises

1. {{PROMISE_1}}
2. {{PROMISE_2}}
3. {{PROMISE_3}}

### 1.2 Thematic Statement

> 이 소설이 궁극적으로 무엇에 관한 이야기인지 한두 문장으로 선언한다. 장르 규칙이나 플롯 구조가 아니라, 독자가 마지막 화를 닫으며 남기는 감정/질문/통찰이다.

- **주 주제**: {{MAIN_THEME}} (소설 전체를 관통하는 핵심 질문)
  (예: "상실 후에도 사랑할 수 있는가", "정의는 복수와 어떻게 다른가")
- **부 주제**: {{SUB_THEMES}} (아크별로 다를 수 있는 변주. 1~2개. 없으면 생략)
  (예: "권력은 인간을 어떻게 변형하는가", "기억이 곧 존재인가")

> 매 에피소드는 주 주제 또는 부 주제 중 하나와 연결되어야 한다 — 직접 다루거나, 주제가 작동하는 세계를 구축하거나, 캐릭터의 입장을 변화시키는 방식으로. 어느 주제와도 무관한 에피소드가 3회 이상 연속되면 방향을 재점검한다.

---

## 2. Folder Structure

```
{{NOVEL_ID}}/
├── CLAUDE.md              ← This file (Writing Constitution)
├── EDITOR_FEEDBACK_*.md   ← Editor reviews (gemini/gpt/nim/ollama)
├── settings/              ← Shared novel-craft layer (same authoring rules as lean variants)
│   ├── 01-style-guide.md
│   ├── 02-episode-structure.md
│   ├── 03-characters.md
│   ├── 04-worldbuilding.md
│   ├── 05-continuity.md
│   ├── 06-humor-guide.md       (optional)
│   ├── 07-periodic.md
│   └── 08-illustration.md
├── chapters/              ← Episode manuscripts
├── plot/                  ← Plot / foreshadowing
├── summaries/             ← Per-episode summaries
│   ├── running-context.md
│   ├── episode-log.md
│   ├── character-tracker.md
│   ├── decision-log.md    ← Project-level deviation recording
│   └── (+ promise/knowledge/relationship/feedback logs)
└── .claude/agents/        ← Agents (writer, unified-reviewer, etc.)
```

`settings/`는 hybrid, Claude lean, Codex lean이 공유하는 공통 집필 레이어다. 이 문서와 `batch-supervisor.md`는 hybrid의 런타임 규칙만 정의한다.

---

## 3. Writing Workflow

### 3.1 Preparation (Prep)

1. **Call `compile_brief` MCP tool**: Generates a compressed brief (~4-15KB) from project files (~300KB+). compile_brief를 우선 사용하되, 불가능하면 아래 fallback으로 전환.
   - Fallback if unavailable: `summaries/running-context.md` → relevant arc plot → `plot/foreshadowing.md` → `summaries/character-tracker.md`.
2. **Read last 2-3 paragraphs of previous episode**: Verify hook connection + prevent same ending hook type consecutively.
3. **Check character anchors**: Read `settings/03-characters.md` for the episode's key characters before drafting dialogue.
4. **Check continuity anchors when needed**: If this episode depends on dates, ages, travel time, injuries, carry-forward promises, or other invariants, read `settings/05-continuity.md` directly instead of relying on memory alone.
5. **Check editor feedback**: Reference `EDITOR_FEEDBACK_*.md` if unprocessed feedback exists.

### 3.2 Writing (Write)

1. Follow `settings/02-episode-structure.md`.
2. Follow `settings/01-style-guide.md`.
3. Target length: {{TARGET_LENGTH}}
4. **`novel-calc` MCP is for narrative verification only. Calculations must NOT drive the narrative.**
   - Write prose naturally first. Then verify numerical consistency with calc only if needed.
   - Calc results allowed in: (1) unified-reviewer evidence, (2) summaries/ updates, (3) in-world UI/popup/display numbers. NEVER insert calc results into narration, dialogue, or inner monologue.
   - **Characters do mental math like humans, not computers.** Exact tool outputs are for author/model reasoning only. Do NOT copy exact results into character dialogue, monologue, or close-POV narration. Convert to human estimates, rounded quantities, sensory scale, or emotional interpretation.
     - ❌ "잔여 공간이 구 할 삼 푼" → ✅ "일 할도 남지 않았다"
     - ❌ "사흘 뒤면 정확히 삼백 이십 리" → ✅ "사흘이면 닿겠지"
     - ❌ "58,110원 남았네" → ✅ "6만 원도 안 남았나"
     - **Approximation guide** (default human scale):
       - Money: 천/만 단위 반올림 ("한 5만 원쯤", "~도 안 된다")
       - Distance: 한참/사나흘 거리/반나절 (pre-modern: 몇 리/하루길)
       - Ratio/remaining: 거의 없다/일 할도/절반쯤/얼마 안 남았다
       - Time: 두어 시간/사나흘/열흘 남짓 (pre-modern: 한 시진 남짓)
       - Count: 서넛/대여섯/열댓/스무 남짓
     - **Emotional state affects precision**: 평온→정돈된 어림, 긴장→단순화, 공황→수치 대신 감각("미쳤다", "또 나갔다")
     - **Character expertise exception**: 회계사/상인/수학자/천재 등 수치에 밝은 캐릭터는 더 촘촘한 어림이 허용되나, 그래도 "계산기 출력 복사"가 아닌 **"더 좋은 어림"**이다. settings/03-characters.md에 해당 캐릭터의 수치 정밀도를 명시할 것.
     - **When exact numbers ARE natural** (do NOT force approximation here):
       - Reading a price tag, receipt, menu, scoreboard, clock, calendar ("1,990원입니다")
       - Repeating a number someone just told them ("삼백 냥이라고?")
       - Quoting official data, addresses, phone numbers, test scores
       - In-world displays, documents, system readouts, ledgers, instruments (exact values OK, but pre-modern settings still require 한글 수사 — §3.2.9 numeral rules apply even inside display/readout brackets)
     - **When approximation IS natural** (this is the rule's main target):
       - Mental arithmetic ("내 돈이 얼마 남았더라...")
       - Estimating distance, time, quantity from memory
       - Emotional reactions to numbers (even after reading exact display)
     - **Key distinction**: "읽거나 듣는 것" = exact OK. "머릿속으로 계산/추정하는 것" = human approximation. "읽은 뒤 해석/판단하는 것" = approximation.
     - **Edge case**: 여러 가격을 보고 합산 → 개별 가격은 정확, 합계는 어림 ("대충 한 5만 원어치 샀나"). 캐릭터가 평소 외우고 있는 숫자(월세, 비밀번호, 시험 등급)는 정확 허용.
   - **Use calc when**: dates are plot-critical, travel distance/time may cause contradiction, economy/supply is core conflict, checking word count.
   - **Skip calc when**: vague time expressions, atmospheric approximations, mundane travel/trade, combat distances/speeds.
   - Tools: dates(`date_calc`/`weekday`/`d_plus`/`date_diff`) | arithmetic(`calculate`) | travel(`speed_distance_time`/`travel_estimate`) | units(`unit_convert`/`convert_time`) | economy(`currency_calc`/`supply_calc`/`growth_calc`) | length(`char_count`)
5. **When the novel uses Hanja naming** (martial arts, historical, Sino-Korean fantasy), **use `novel-hanja` MCP**. Never assemble Hanja via LLM inference. For modern/SF settings where names don't require Hanja etymology, this step may be skipped.
   - `hanja_lookup`, `hanja_search`, `hanja_meaning`, `hanja_verify`
6. **Hanja notation**: Show reading + Hanja only on first appearance (e.g., 내공(內功), 대사헌(大司憲) — genre-dependent). Korean-only thereafter. Ref: `summaries/hanja-glossary.md`. Exception: re-appearance after 30+ episodes, homophone disambiguation.
7. **Use `novel-naming` MCP** for spelling variants, title consistency, faction/skill naming drift, and alias normalization when proper nouns start proliferating.
8. **Dialogue anchor rule**: `settings/03-characters.md`의 대표 대사는 복붙용 문장이 아니다. 어휘 선택, 높낮이, 위계감, 판단 방식을 읽고, 실제 장면에 맞게 변주한다.
9. **Use era-appropriate units and terminology.** Refer to `settings/04-worldbuilding.md` for your novel's setting.
   - Modern/SF: Modern units, loanwords, and Arabic numerals are natural. No conversion needed.
   - Pre-modern/historical: metric → traditional units, loanwords → Sino-Korean/native Korean. Use `unit_convert`.
   - **Pre-modern numeral rules (Korean output)** — (Apply only when settings specify a pre-modern or historical era. For modern/SF, Arabic numerals and modern counting are natural.):
     - 아라비아 숫자 금지 in prose. Use 한글 수사.
     - No decimal notation: `1.5장` → `일 장 반`
     - `100명` → `백 명`, `3일` → `사흘`, `7일` → `이레`, `10일` → `열흘`, `15일` → `보름`
     - Exception: EPISODE_META, plot/, summaries/ (meta areas)
10. **Footnotes**: Use `[^N]` format. `\[N\]` or `[N]` formats forbidden.

### 3.3 Unified Review

Per `.claude/agents/unified-reviewer.md`. Continuity + narrative quality + Korean proofreading + external feedback in a single pass.

**Modes** (periodic + change-based triggers):
- `continuity` (every episode): 14 continuity items + critical Korean errors(❌) + 반복표현/번역투/호응오류
- `standard` (as triggered by `settings/07-periodic.md`): continuity + 7 narrative items + full Korean proofing + configured external feedback
- `full` (arc boundary / setting change / long-term foreshadowing payoff): all items + detailed analysis + direct settings reference, especially `01/03/05/07`

**Review anchor**:
- review 시 주요 인물 대사가 `settings/03-characters.md`의 운용 앵커와 어긋나는지 확인한다.
- 대표 대사를 그대로 반복한 문장은 drift 위험으로 본다.

**External feedback sources** (per CLAUDE.md flags):
1. **Gemini** (`gemini_feedback: true`): continuity/worldbuilding → `EDITOR_FEEDBACK_gemini.md`
2. **GPT** (`gpt_feedback: false`): ~~prose/dialogue/emotion~~ — hybrid에서 비활성 (집필 모델과 동일)
3. **NIM** (`nim_feedback: true`): spelling/grammar → `EDITOR_FEEDBACK_nim.md`
4. **Ollama** (`ollama_feedback: true`): spelling/grammar → `EDITOR_FEEDBACK_ollama.md`

> All sources false → skip external review. Individual source failure → skip that source only, log it.

### 3.4 Post-Processing (Hybrid: Supervisor가 수행)

> **Hybrid 파이프라인**: Codex writer는 본문 생성만 담당. 아래 후처리는 **Claude supervisor가 직접 수행**한다.

1. **Summary update**: Supervisor가 chapter 파일을 읽고 직접 갱신.
   - Required (every ep): `running-context.md`, `episode-log.md`, `character-tracker.md`
   - Conditional (only if relevant change): `promise-tracker.md`, `knowledge-map.md`, `relationship-log.md`, `foreshadowing.md`, `decision-log.md`
2. **Insert EPISODE_META**: Supervisor가 chapter 파일 끝에 append. Set `date` to today `"YYYY-MM-DD"`.
3. **Update feedback log**: Record 3.3 results in `editor-feedback-log.md`.
4. **Git commit**: After episode completion (manuscript + summaries). Message: `{소설명} {N}~{M}화 집필`. Push only on user request.
5. **Action log**: 주요 작업 완료 시 `summaries/action-log.md`에 한 줄 append. 형식: `| {시각} | {에이전트} | {행동} | {대상} | {상태} | {비고} |`. 운영 로그이므로 compile_brief에 포함하지 않는다.
6. **Style lexicon**: 어휘 치환이 채택되면 `summaries/style-lexicon.md`에 즉시 기록. compile_brief에 자동 포함.

Arc boundary principle:
- 아크 경계에서 나온 항목은 `patch-feasible`과 `HOLD`로 분리한다.
- `forward-fix`는 `review-log.md`, `running-context.md`, 다음 아크 plot 파일에 동시에 기록한다.

### 3.5 Parallel Writing & Periodic Checks

→ See `settings/07-periodic.md`.

**Why-checker** (`/why-check`): Runs at arc boundaries (text mode), arc starts (plan mode), and optionally every 5-8 episodes (rolling mini-check). See `.claude/agents/why-checker.md`.

**OAG-checker** (`/oag-check`): Detects Obligatory Action Gaps — characters knowing information but failing to act on it. Runs at arc transitions (text mode) and before writing new arcs (plan mode). See `.claude/agents/oag-checker.md`.

**POV-Era-checker** (`/pov-era-check`): POV 인물의 지식 범위를 벗어난 명칭/정보 + 시대/세계관에 부적합한 표현 전담 감사. 5화 단위 periodic check + 아크 경계 배치 실행. See `.claude/agents/pov-era-checker.md`.

**Scene-Logic-checker** (`/scene-logic-check`): 장면 내부의 동작/시선/방향/자세 논리 모순 전담 감사. 아크 경계 배치 실행. See `.claude/agents/scene-logic-checker.md`.

**Repetition-checker** (`/repetition-check`): 크로스 에피소드 반복 패턴(표현, 감정 처리, 정보 전달 구조, 에피소드 아키타입) 전담 감사. 5화 단위 정기 + 아크 경계 배치 실행. See `.claude/agents/repetition-checker.md`. 산출물: `summaries/cross-episode-repetition-report.md` + `summaries/repetition-watchlist.md`.

---

## 4. File Reference Priority

1. **This file (CLAUDE.md)** — highest priority
2. **settings/ folder** — detailed rules
3. **Previous episode text** — established facts
4. **summaries/** — reference only, episode text takes precedence

> Note: `settings/` is the shared literary/continuity layer across template variants. When `settings/` files provide more detailed or updated rules than this document's general principles, the settings file's specific rule takes precedence; this document only governs hybrid runtime behavior.

---

## 5. Prohibitions

> The following rules are NEVER violated under any circumstances.

1. **No sudden character personality changes**: Only gradual change allowed. Abrupt shifts require a convincing preceding event.
2. **No deus ex machina**: Crisis resolution only via previously established abilities/resources/characters.
3. **No setting contradictions**: Established worldbuilding rules' mechanics cannot be changed without modifying settings files first. Reveals that recontextualize a rule's origin or intent (without changing how it works) are allowed per settings/04-worldbuilding.md.
4. **No extreme length violations**: Stay within ±30% of target length (70~130%). Deviations beyond ±20% require recording in EPISODE_META intentional_deviations.
5. **No meta expressions**: 금지 표현 예시: "소설에서처럼", "독자 여러분" — no 4th wall breaking.
6. **No renaming proper nouns**: Names defined in settings files cannot be arbitrarily changed.
7. **No episode structure meta-references in prose**: 금지: "3화에서", "프롤로그에서", "에필로그에서", "1부에서" in narration/dialogue. Reference past events by date/place/event name. Meta areas (EPISODE_META, plot/, summaries/) are exempt. 의도적 메타픽션 장르에서는 CLAUDE.md §5.1에 등록하여 허용 가능.
8. **No POV switch spoilers**: 금지: `[시점 전환: 세르반]` meta tags in prose. Use `***` scene break then shift naturally via tone/setting/senses.
9. **No unearned emotional escalation**: 감정적 클라이맥스(죽음, 고백, 배신, 재회)는 해당 관계나 갈등이 독자가 체감할 수 있을 만큼 사전에 전개된 후에만 허용한다. 화수 제한은 없으나, 축적이 부족하면 독자가 설득되지 않는다.
10. **No costless victories**: 주요 성과를 "무상 보상"처럼 처리하지 말 것. 희생·트레이드오프·후속 부담은 같은 화에 드러날 수도 있고, 복선으로 유예되었다가 이후 큰 대가로 회수될 수도 있다. 어떤 경우에도 성과가 장기적으로 긴장과 균형을 깨는 순이익으로만 남아서는 안 된다.
11. **No finale overload**: 마지막 아크에서 설명, 감정 결산, 클라이맥스 액션을 한 화에 과밀하게 압축하지 않는다. 독자가 전개를 따라가고 감정과 사건을 각각 소화할 여백을 확보한다. 적정 분량은 전체 길이·장르·리듬에 맞게 조정. 스릴러 등 압축이 미덕인 장르에서는 의도된 고밀도 전개를 허용한다.

### 5.1 Intentional Mysteries (의도적 비밀)

> `/why-check` 실행 시 아래 항목은 "설명 누락"이 아니라 **의도적 미스터리**로 간주한다.
> 독자에게 숨기는 것이 서사적 목적이 있는 경우에만 기록한다.

| 비밀 | 공개 예정 시점 | 왜 숨기는가 |
|------|-------------|-----------|
| {{MYSTERY_1}} | {{아크/화수}} | {{서사적 이유}} |

> 이 목록에 없는 설명 누락은 실수로 간주한다.

### 5.2 AI Execution Guardrails (Process Constraints)

> AI 집필 시 반복적으로 발생하는 실패 패턴에 대한 사전 방어. 장르와 소설에 맞게 3개 이상을 정의한다. 빈 섹션으로 남기지 않는다.

| # | 가드레일 | 위반 예시 | 올바른 접근 |
|---|---------|----------|-----------|
| G1 | {{GUARDRAIL_1}} | {{위반 예시}} | {{올바른 접근}} |
| G2 | {{GUARDRAIL_2}} | {{위반 예시}} | {{올바른 접근}} |
| G3 | {{GUARDRAIL_3}} | {{위반 예시}} | {{올바른 접근}} |

> 가드레일은 금지(§5)와 다르다. 금지는 "절대 하지 않는 것", 가드레일은 "AI가 습관적으로 빠지는 패턴을 사전에 방지하는 것"이다. 예: 수동적 정보 수령 2연속 금지, 유머 회피 3연속 금지, 수련 전용 에피소드 금지 등.

---

## 6. Episode Metadata (EPISODE_META)

Append this format at the end of each episode file. (Auto-removed by reader)

```markdown
---

### EPISODE_META
```yaml
episode: {{NUMBER}}
title: "{{TITLE}}"
summary: "{{SUMMARY}}"
date: "{{DATE}}"
pov: "{{POV_CHARACTER}}"
location: "{{LOCATION}}"
timeline: "{{TIMELINE_POSITION}}"
characters_appeared:
  - {{CHARACTER_1}}
  - {{CHARACTER_2}}
new_elements:
  - "{{NEW_ELEMENT}}"
unresolved:
  - "{{UNRESOLVED_THREAD}}"
next_episode_hook: "{{HOOK}}"
thematic_function: "{{이번 화의 주제적 역할}}"  # from planning gate step 4(f)
review_mode: "{{continuity|standard|full}}"  # actual mode used
review_floor: "{{continuity|standard|full}}"  # floor specified by supervisor
external_review: "{{GPT:ok, NIM:ok, Gemini:fail}}"  # per-source result
intentional_deviations:  # (optional) record deliberate rule deviations for THIS episode
  - rule: "ending-hook"  # use kebab-case rule ID for consistency
    detail: "여운형 결말로 마무리"
    reason: "아크 종결 화, 감정 정리 우선"
# For recurring deviations, record once in summaries/decision-log.md instead of repeating per episode.
```
```

---

## 7. Cover Image & Illustrations

→ See `settings/08-illustration.md`.

- **Cover**: Auto-generate via `generate_image` if `cover.png` doesn't exist at first episode. Save prompt to `cover-prompt.txt`.
- **Episode illustrations**: Only when `illustration: true`. Use `generate_illustration` tool, insert as blockquote.
- **`character-prompts.md`**: Manage per-character image prompts. Maintained for cover use even when `illustration: false`.

---

## 8. 대화 관계 규칙 (Dialogue Relationship Rules)

> This section stays in Korean as it defines Korean-specific honorific/speech-level rules.

### 8.1 호칭/어투 매트릭스

"행의 화자가 열의 청자에게 말할 때"의 존댓말/반말/호칭 규칙. 자주 대화하는 쌍만 기록.

| 화자 → 청자 | {{CHAR_A}} | {{CHAR_B}} | {{CHAR_C}} |
|-------------|-----------|-----------|-----------|
| **{{CHAR_A}}** | — | {{존/반+호칭}} | {{존/반+호칭}} |
| **{{CHAR_B}}** | {{존/반+호칭}} | — | {{존/반+호칭}} |
| **{{CHAR_C}}** | {{존/반+호칭}} | {{존/반+호칭}} | — |

> 미등록 조합 기본값: {{DEFAULT_RULE}}

### 8.2 상황별 어투 전환

| 캐릭터 | 상황 A | 상황 B |
|--------|--------|--------|
| {{CHAR}} | {{공적 석상: ~합니다}} | {{사적 대화: 반말}} |

### 8.3 어투 변화 이력

| 화수 | 화자 → 청자 | 변화 내용 | 사유 |
|------|------------|----------|------|
| {{N}}화 | {{A}} → {{B}} | 존댓말 → 반말 | {{사건 설명}} |

### 8.4 어투 원칙

1. **어투 변화는 사건에 의해서만 발생**: 설명 없는 갑작스러운 전환 금지.
2. **감정 극단 시 일시적 이탈 허용**: 장면 종료 후 원래로 복귀.
3. **공적/사적 구분**: 같은 쌍이라도 상황에 따라 다를 수 있다.
4. **어투 역행 금지**: 반말→존댓말 전환은 특수 사건(배신, 관계 단절 등) 필요.
5. **대화는 정보 전달만을 위해 존재하지 않는다**: 대부분의 대화 교환은 정보 전달 외에 최소 하나의 기능(캐릭터 성격 노출, 관계 변화, 서브텍스트, 유머)을 수행해야 한다. 일상적 정보 전달(가격, 길 안내 등)은 예외.

---

## 9. Customization Guide

After copying this template, fill in `{{PLACEHOLDER}}` values and:

> `settings/` files are intentionally shared with the lean variants. If a change is about prose, characters, continuity, or periodic checks, prefer editing the settings file. If it is about hybrid orchestration, edit this file or `batch-supervisor.md`.

1. `settings/01-style-guide.md` — prose style rules
2. `settings/02-episode-structure.md` — episode structure
3. `settings/03-characters.md` — character sheets (include 대표 대사 2~3종)
4. `settings/04-worldbuilding.md` — worldbuilding
5. `settings/05-continuity.md` — timeline baseline, continuity settings
6. `settings/07-periodic.md` — periodic check settings (adjust trigger frequency)
7. `settings/08-illustration.md` — cover/illustration rules
8. `cover-prompt.txt` — cover image prompt
9. Optional: `settings/06-humor-guide.md`
10. Section 8 — fill in the honorific/speech-level matrix
11. `settings/01-style-guide.md` §0 — **Voice Profile** (서술 온도, 보이스 우선순위, 대표 문단). 이것이 소설의 목소리다.
12. Section 1.2 — **Thematic Statement** (주 주제 + 부 주제). 이것이 소설의 영혼이다.
13. `summaries/decision-log.md` — initialize if project-wide deviations are planned

---
