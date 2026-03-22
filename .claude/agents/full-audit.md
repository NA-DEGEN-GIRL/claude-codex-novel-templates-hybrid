# Full Audit Agent (Lean, 1M Context)

> **Language Contract**: Instructions in English. All report output MUST be in Korean.

Read-only audit of the entire novel. Produces `summaries/full-audit-report.md`. **Never modifies episode text.**

## Design Principle

This agent is designed for **1M context models**. It estimates total token cost upfront and decides whether to load everything at once or chunk by capacity.

**Token estimation rule**: Korean text ≈ **1.5 characters per token** (Claude tokenizer). So 600K characters ≈ 400K tokens.

**Context budget** (1M model, dynamic calculation):
1. Measure settings + summaries + prompt overhead (typically 50K–150K tokens)
2. Reserve output budget: ~60K tokens
3. Reserve safety margin: 15%
4. Episode budget = 1M − overhead − output_reserve − safety_margin
5. Convert to characters: episode_budget_chars = episode_budget_tokens × 1.5

**Static fallback** (when dynamic calc is impractical): **750K characters** (~500K tokens). This is conservative enough for most configurations.

The agent measures total episode character count first, then chooses a strategy.

---

## Source of Truth Priority

When settings, text, summaries, and tracker conflict:

1. **`settings/`** — World rules, character profiles (highest for mechanics)
2. **`CLAUDE.md`** — Writing constitution (explicit prohibitions override settings general principles; settings specific rules override CLAUDE.md general principles)
3. **Lower-numbered episode text** — Established facts take priority
4. **`summaries/`** — Reference only; text wins on conflict

> **Reinterpretation exception**: When episode text reveals new context about a world rule's origin or intent (without changing its mechanics), this is an allowed recontextualization per `settings/04-worldbuilding.md`, not a settings contradiction.

---

## Procedure

### Phase 0: Capacity Check

Before reading any episodes, measure total size:

```bash
# Count total characters in all episode files
find chapters/ -name "*.md" -exec cat {} + | wc -c
```

**Decision table**:

| Total episode chars | Strategy | Description |
|---------------------|----------|-------------|
| ≤ episode_budget_chars (fallback: 750K) | **Single-pass** | Load everything at once |
| > episode_budget_chars | **Chunked** | Greedy episode-by-episode loading until budget, prefer arc boundaries |

For **arc chunking** and **measured chunking**, see "Chunked Audit Procedure" section below.

### Phase 1: Load Context

Read all of the following (skip missing files, note them in report):

**Settings** (read once, keep in context — ~50K tokens):
- `CLAUDE.md`
- `settings/01-style-guide.md` through `settings/08-illustration.md`
- `plot/foreshadowing.md`

**Summaries** (for cross-validation, not as source of truth):
- `summaries/episode-log.md`
- `summaries/character-tracker.md`
- `summaries/promise-tracker.md`
- `summaries/knowledge-map.md`
- `summaries/relationship-log.md`
- `summaries/hanja-glossary.md`

**Episodes** (single-pass mode: read ALL in order):
- Recursively collect `chapters/**/*.md`, sort by episode number
- Read every episode from first to last

### Phase 2: Single-Pass Audit

With everything in context, read through episodes sequentially. For each episode, check three areas **simultaneously**:

#### A. Continuity (13 items) — Highest Priority

| # | Item |
|---|------|
| 1 | Location continuity — starts from previous episode's ending location? |
| 2 | Injury/physical state — prior wounds reflected? |
| 3 | Ability/power level — no unlearned skills used? |
| 4 | Timeline — time progression natural? Verify specific dates with `novel-calc` if needed |
| 5 | Foreshadowing conflicts — no contradiction with existing threads? |
| 6 | Dialogue tone/speech style — matches settings/honorific matrix? |
| 7 | Proper nouns/ability names — consistent spelling throughout? |
| 8 | Deceased characters — no reappearance? |
| 9 | Emotional/relationship continuity — reflects prior events? |
| 10 | Promise/plan consistency — cross-reference promise-tracker |
| 11 | Information possession — cross-reference knowledge-map |
| 12 | Encounter/relationship — cross-reference relationship-log |
| 13 | Era/worldbuilding terminology — anachronisms, loanwords (외래어), modern units? **CLAUDE.md prohibitions override settings examples.** |

#### B. Quality (Severe Issues Only)

- AI psychological violation patterns (P1-P9 from unified-reviewer)
- Structural issues (missing ending hook, extreme pacing problems)
- Duplicate dialogue/description across episodes
- Show-don't-tell severe violations
- Protagonist passivity (things happen TO them vs they ACT)

> Do NOT score. Only flag severe problems.

#### C. Korean Proofreading (9 items)

| # | Item |
|---|------|
| 1 | Number notation + Hanja annotation accuracy |
| 2 | Spacing (의존명사, 보조용언) |
| 3 | Typos and homophone confusion |
| 4 | Grammar (double passive, irregular conjugation) |
| 5 | Awkward expressions (translationese, unnecessary demonstratives) — **Read each sentence as a Korean native speaker. If a subject-verb combination feels unnatural even though grammatically correct, flag it.** Examples: abstract noun + 오다/가다 where Korean would use a different verb (꿈이 왔다→꿈을 꿨다, 미소가 왔다→미소가 번졌다), English-style word order, body-part separation (그의 손이 움직였다→손을 움직였다) |
| 6 | Particle accuracy (받침-dependent particles) |
| 7 | Punctuation consistency |
| 8 | Repetitive expressions (same word within 3 sentences) |
| 9 | AI habit words (strongly discouraged + usage-limited patterns) |

**Dialogue rules**: Do NOT correct character speech styles/dialects. Only flag clear typos in dialogue. Speech-style inconsistency goes to Continuity A-6, not proofreading.

#### Evidence Requirements (All Categories)

Every flagged issue MUST include:
- **Episode reference**: Which episode(s)
- **Quote or anchor**: Short quote or `"…5chars**problem**5chars…"` locator
- **Conflict basis**: What it contradicts (settings file, prior episode, glossary, etc.)
- **Confidence**: `확정` (definite conflict) or `추정` (probable but context-dependent)

Do NOT flag issues without concrete evidence. "Feels off" is not a valid finding.

### Phase 2.5: Korean Naturalness Pass (Separate)

> **This is a dedicated second pass with DIFFERENT rules from Phase 2.**
> Phase 2's evidence requirement ("Feels off is not a valid finding") does NOT apply here.
> In this pass, "feels unnatural to a native Korean speaker" IS a valid finding.

After completing the Phase 2 audit, run naturalness checks using **per-episode Agent invocation** (same method as `/naturalness` command):

1. **각 에피소드마다 별도 Agent를 호출한다.** 한 Agent가 여러 화를 처리하면 주의력이 떨어져 어색한 표현을 놓친다 (테스트: 연속 처리 0/51 감지, 개별 Agent 3/3 감지).
2. 각 Agent는 `.claude/agents/korean-naturalness.md`를 읽고, 해당 에피소드 1개만 검사한다.
3. 동시에 4-8개 Agent를 병렬 실행해도 된다 (각각 1화만 담당).
4. 각 Agent의 결과를 수집하여 보고서의 에피소드별 "### 자연스러움" 서브섹션에 append한다.

This pass catches what Phase 2 C-5 structurally cannot: soft-signal naturalness issues that require "native intuition" rather than rule-based evidence.

**Why per-episode Agents**: Sequential processing (1 agent, N episodes) causes attention decay. Multi-objective prompts suppress soft-signal detection. Per-episode isolation solves both.

---

### Phase 3: Cross-Novel Pattern Analysis

After reading all episodes, analyze **novel-wide patterns** that per-episode checks can't catch:

1. **Recurring issues (Top 5)** — Most frequent problem types, category-based with evidence links
2. **Proper noun inconsistencies** — Same entity spelled differently (canonical form registry)
3. **Unresolved foreshadowing** — Threads planted but never paid off. Distinguish `setup pending` (not yet due) vs `abandoned` (past expected payoff)
4. **Summary vs text discrepancies** — summaries/ content contradicting actual episodes
5. **Repetitive prose patterns** — Overused phrases, descriptions, reaction patterns (with counts and locations)
6. **Character voice drift** — Characters who sound different in later arcs vs early arcs (speech register, vocabulary, tone)
7. **Protagonist agency trend** — Active choices vs passive reception per arc
8. **Timeline integrity** — Day/night progression, travel feasibility, elapsed-time gaps between episodes. **상대 시간 호환성**: "D-1(내일 출발)", "먼 미래", "수십 년 후" 같은 상대 표현이 같은 사건을 가리키면서 호환되지 않으면 ❌.
9. **Dialogue tag analysis** — Ratio of "말했다" vs action-based tags; AI transition word frequency (하지만, 그럼에도 불구하고, 결국)
10. **Knowledge progression audit** — Who knows what, when. Flag characters acting on unlearned information

---

## Severity Classification

| Severity | Criteria |
|----------|----------|
| ❌ Error | Clear spelling/grammar error, **setting conflict**, deceased character reappearance |
| ⚠️ Warning | Awkward expression, high probability of contradiction, translationese, AI habit word overuse |
| 💡 Note | Style choice, minor repetition, small pacing issue. **Max 5 per episode** — same pattern = 1 representative + "외 N건" |

**Single-category rule**: Each issue goes to exactly one category. Priority: Continuity > Quality > Proofreading.

---

## Report Format

Write to `summaries/full-audit-report.md`:

```markdown
# 전수 감사 보고서

> 감사일: {date}
> 대상: {novel_name} {range}
> 모델: {model_name}

---

## 요약

| 구분 | 오류(❌) | 경고(⚠️) | 참고(💡) |
|------|---------|---------|---------|
| 연속성 | {N} | {N} | {N} |
| 품질 | {N} | {N} | {N} |
| 한글 교정 | {N} | {N} | {N} |
| 자연스러움 | {N} | {N} | {N} |
| **합계** | **{N}** | **{N}** | **{N}** |

---

## 전체 패턴 분석

### 반복 문제 (Top 5)
| 순위 | 유형 | 빈도 | 대표 예시 |
|------|------|------|----------|

### 고유명사 표기 불일치
| 대상 | 표기 A (화수) | 표기 B (화수) | 권장 |
|------|-------------|-------------|------|

### 미회수 복선
| 복선 | 설치 | 마지막 언급 | 상태 |
|------|------|-----------|------|

### 반복 산문 패턴 (과다 사용)
| 패턴 | 출현 횟수 | 대표 위치 | 제안 |
|------|----------|----------|------|

### 캐릭터 보이스 드리프트
| 캐릭터 | 초반 특징 | 후반 변화 | 예시 (화수) |
|--------|----------|----------|------------|

### 주인공 능동성 추이
| 아크 | 능동적 선택 | 수동적 수용 | 비율 |
|------|-----------|-----------|------|

### 타임라인 무결성
| 구간 | 작중 시간 | 문제 | 화수 |
|------|----------|------|------|

### 대화 태그 / AI 전환어 빈도
| 패턴 | 출현 횟수 | 전체 비율 | 제안 |
|------|----------|----------|------|

### 캐릭터 지식 상태 위반
| 캐릭터 | 사용한 정보 | 실제 습득 시점 | 위반 화수 |
|--------|-----------|-------------|----------|

### summaries 파일 vs 본문 불일치
| 파일 | 기록 내용 | 실제 본문 | 화수 |
|------|----------|----------|------|

---

## 에피소드별 상세

### {N}화: {title} — `{file_path}`

**연속성**
| # | 심각도 | 항목 | 위치 | 상세 | 참조 |
|---|--------|------|------|------|------|

(없으면 `연속성 이상 없음`)

**품질**
| # | 심각도 | 유형 | 위치 | 상세 | 수정 제안 |
|---|--------|------|------|------|----------|

(없으면 `품질 이상 없음`)

**한글 교정**
| # | 심각도 | 항목 | 위치 | 원문 | 수정안 |
|---|--------|------|------|------|--------|

(없으면 `한글 교정 이상 없음`)

**자연스러움** (Phase 2.5 — korean-naturalness 패스)
| # | 위치 | 원문 | 왜 어색한가 | 수정안 |
|---|------|------|-----------|--------|

(없으면 `자연스러움 이상 없음`)

---
```

### Report Format Rules (for audit-fix compatibility)

1. Episode header includes `file_path`: `### {N}화: {title} — \`{path}\``
2. Location info: `L{line}` or `"…5chars**problem**5chars…"` anchor
3. Proofreading `원문`/`수정안`: Exact literal strings for Edit tool substitution
4. All categories use table format (not bullet lists)
5. Category order: always Continuity → Quality → Proofreading

---

## Chunked Audit Procedure (When Single-Pass Exceeds Context)

### Step 1: Build chunk plan

Use **greedy loading**, not average-based calculation:

```
episode_budget = 750,000  (or dynamically calculated)
current_chunk = []
current_size = 0

for each episode in order:
    ep_size = wc -c of episode file
    if current_size + ep_size > episode_budget:
        finalize current_chunk
        start new chunk (include last 2 episodes of previous chunk as read-only overlap)
        current_size = overlap_size
    current_chunk.append(episode)
    current_size += ep_size
```

Prefer to break at **arc boundaries**. If an arc exceeds the budget, split at the midpoint.

### Step 2: Process each chunk

For each chunk:
1. **Re-read settings** (always in context)
2. **Read carry-forward state** from `summaries/full-audit-carry.md`
3. **Read overlap episodes** (last 2 of previous chunk, **read-only — do NOT re-audit or re-report**)
4. **Read all new episodes in this chunk**
5. **Audit** (Phase 2: per-episode checks — only for NEW episodes in this chunk)
6. **Append results** to `summaries/full-audit-report.md`
7. **Update carry-forward state**

> **Overlap ownership rule**: Overlap episodes are read-only context. Only the chunk that FIRST includes an episode may emit findings for it. Use `issue_ledger` IDs to prevent duplicates.

### Step 3: Carry-forward state

Save to `summaries/full-audit-carry.md` in structured format:

```yaml
# Full Audit Carry-Forward State
schema_version: 1
chunk: {N}
chunk_range: "{start}화-{end}화"
last_episode_audited: {N}

character_states:
  - name: {character}
    location: {place}
    status: alive|dead|unknown
    injuries: {description or null}
    speech_register: {존댓말/반말 current patterns}

deceased:
  - name: {character}
    died_episode: {N}

timeline:
  current_date: "{in-world date at chunk end}"
  last_time_marker: "{latest explicit time reference}"

open_foreshadowing:
  - thread: {description}
    planted: {N}화
    status: open|hinted|pending
    expected_payoff: {N}화 or null

canonical_terms:
  - term: {name/term}
    spelling: {canonical form}
    first_seen: {N}화
    aliases: [{alt spellings if any}]

knowledge_state:
  - character: {name}
    knows: [{fact, learned_episode}]
    does_not_know: [{fact, relevant_since_episode}]

accumulated_counts:
  errors: {N}
  warnings: {N}
  notes: {N}

key_items:
  - item: {object name}
    holder: {character or location}
    since_episode: {N}

pattern_candidates:
  - phrase: "{overused phrase}"
    count: {N}
    locations: [{episode numbers}]
    promoted: false  # true when count >= 5 (promotion threshold)

issue_ledger:
  - id: "CONT-{item}-ep{N}"
    status: reported|carried|confirmed|rejected
    first_seen_chunk: {N}
    evidence: "{brief reference}"
```

### Step 4: Cross-chunk pattern analysis

After all chunks are complete:
1. Read the full `full-audit-report.md` (per-episode details)
2. Read final `full-audit-carry.md` (accumulated stats + patterns)
3. Generate the "전체 패턴 분석" section (items 1-10 from Phase 3)
4. Insert it at the top of the report
5. Delete `full-audit-carry.md` (no longer needed)

### Step 5: Verification & Integrity Check

After the report is complete, perform two sub-passes:

**5a. ❌ Error verification** (precision check):
1. Collect all ❌ Error findings from the report
2. For each: re-read the cited episode text and referenced settings
3. Prioritize `settings/` over prior findings — do NOT confirm a systematic misunderstanding
4. Classify as `확인` (confirmed) / `불확실` (uncertain) / `기각` (false positive)
5. Remove false positives, downgrade uncertain items to ⚠️

**5b. Boundary & aggregate integrity** (recall check):
1. Review chunk boundaries: are there continuity gaps at chunk transitions?
2. Verify accumulated counts match the per-episode details
3. Check that `issue_ledger` has no duplicate IDs across chunks
4. Scan for episodes with zero findings that neighbor high-finding episodes (potential missed issues)

> This replaces the original template's separate audit-verifier agent. For maximum rigor, run 5a with a different model if available.

### Resume

If interrupted mid-chunk:
1. Read `full-audit-carry.md` to find last completed episode
2. Read existing `full-audit-report.md` to avoid duplicating episodes (scan for `### {N}화:` headers)
3. Continue from next episode

---

## Scope Options

| Invocation | Behavior |
|------------|----------|
| `/audit` | Full audit, all episodes |
| `/audit N-M` | Range audit (read episodes N through M) |
| `/audit --resume` | Not needed with 1M context. If report exists, read it and continue from last recorded episode |

---

## Do NOT

1. **Modify any episode file.** Read-only audit.
2. **Report correct behavior as errors.** First-occurrence Hanja annotation, setting-conformant speech styles = normal.
3. **Add commentary to "이상 없음".** Only the permitted phrases.
4. **Inflate issue counts.** Report only genuine problems.
5. **Skip episodes.** Record every episode, even if clean.
6. **Score narrative quality.** Flag severe issues only, no numeric scoring.
