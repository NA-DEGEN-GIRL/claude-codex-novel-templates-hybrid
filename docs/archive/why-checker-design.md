# WHY-Checker: Missing Explanation Detector
## Game Design Analysis & Agent Specification

---

## Part 1: The Game Design Diagnosis

### Why AI reviewers fail to find missing explanations

The failure is not stupidity — it is a known cognitive trap that game designers call **"designer blindness."**

A game designer who built a level knows why every door is locked. When they playtest their own level, they walk past the confusing lock without noticing because their brain auto-fills the explanation from design memory. The player, who has no design memory, stops dead and asks "wait, why is this locked?"

An AI writer has the same problem, amplified. When it writes "Jay Lee couldn't find his daughter's data for 37 years," it has a vague internal model of why — budget constraints, legal red tape, plot necessity. It never writes the explanation because it already "knows" it. When it reviews, it reads that sentence and the internal model fires again, filling the gap. The gap is invisible to the author-reviewer.

**The human reader had none of that internal model. Every unexplained fact is a locked door with no sign.**

---

## Part 2: Game Design Frameworks That Solve This

### 2.1 Information Gap Theory (from puzzle and RPG design)

In game design, every piece of information a player needs falls into one of three buckets:

| Bucket | Definition | Narrative Equivalent |
|--------|------------|---------------------|
| **Known** | Player has been explicitly told | Reader was shown/told in text |
| **Inferable** | Player can derive from known facts | Reader can logically conclude |
| **Assumed** | Designer thinks player knows but never told them | Author "knows" but never wrote |

The third bucket is where all missing explanations live. The designer (author) does not experience it as a gap because they put it there. The player (reader) hits it as a wall.

**The WHY-checker's job is to audit the third bucket — systematically finding what the author assumed but never delivered.**

### 2.2 Playtesting as a System, Not an Event

A professional playtesting protocol does not ask "did you enjoy it?" It uses **structured observation**:

1. Watch the player, do not explain anything
2. Every time the player pauses, looks confused, or asks a question — mark it
3. Do not answer their questions during the session
4. After: categorize every pause/question by type (navigation, mechanics, story)

The resulting map is not subjective feedback ("I didn't like the boss"). It is an **information delivery failure map** ("the player did not know they needed the key before reaching the door").

A narrative WHY-checker is the same instrument applied to story: read the text as someone who has never seen the author's notes, stop at every unexplained fact, and record the question.

### 2.3 The SETUP → EVENT → CONSEQUENCE Spine

Every major plot event in any narrative medium (games, novels, film) requires three legs:

```
SETUP:       WHY could this happen? (preconditions, backstory, motivation)
EVENT:        WHAT happened? (the scene itself)
CONSEQUENCE: SO WHAT? (what changed because of it)
```

Missing any leg produces a specific failure mode:

| Missing Leg | Reader Experience | Example from SF Novel |
|-------------|------------------|-----------------------|
| No SETUP | "This came out of nowhere" / "Why?" | CEO couldn't find daughter's data for 37 years — no explanation why |
| No EVENT | "Nothing happened" / "What did they actually do?" | Villain hides for 37 years — event implied, never shown |
| No CONSEQUENCE | "So what?" / "Why does this matter?" | Timeline contradiction (ep49 vs ep50) — no reconciliation |

The WHY-checker must test all three legs for every major plot event, not just check for factual continuity.

### 2.4 The "Naive Player" Technique

In game design, after internal playtesting is exhausted, studios bring in **naive playtesters** — people with zero prior knowledge of the game. They are the gold standard because they have no designer blindness.

The AI WHY-checker simulates a naive reader by operating under a strict constraint: **it is only allowed to use information that appears explicitly in the text.** It cannot use:
- The author's planning documents
- Prior AI-generated summaries (which were written by the same author-brain)
- Inference from "what usually happens in this genre"

This constraint is what makes it structurally different from existing review agents.

---

## Part 3: Why the Existing Agents Miss This

Examining the current pipeline in `/root/novel/no-title-015/.claude/agents/`:

**`full-audit.md`** checks: continuity facts, Korean proofreading, proper nouns, deceased character reappearance. It asks "is the stated fact consistent with prior stated facts?" It does NOT ask "was this fact ever explained?"

**`narrative-reviewer.md`** P7 asks: "Is scene-to-scene cause/effect legible?" and "Are character motivations convincing?" This is adjacent but it evaluates what was written, not what was omitted. An agent reading a well-written scene that rests on an unexplained foundation will rate the scene as good — because the scene IS good. The missing foundation is off-page.

The WTF Test in Phase 1.5 comes closest: "list every moment where you thought 'wait, what?'" But this is a free-form instruction buried in a 9-pillar structured analysis. The attention budget goes to the structured pillars. The WTF test gets a paragraph; the structured analysis gets pages.

**The gap**: neither agent is specifically tasked with generating WHY/HOW questions about every major story fact and then checking whether the answer exists in the text.

---

## Part 4: The WHY-Checker Agent Specification

### 4.1 Core Operating Principle

The agent reads the story twice:

**Pass 1 — Question Generation (Naive Reader Mode)**
Read as if you have never read any planning document, summary, or prior context. At every major story fact, generate the question a curious reader would ask. Do not answer these questions yet. Do not use your knowledge of the story. Just accumulate the questions.

**Pass 2 — Answer Audit (Text-Only Mode)**
For each question generated in Pass 1, search the episode text (not summaries, not planning docs) for an explicit or clearly inferable answer. Mark each as: ANSWERED / INFERABLE / MISSING.

Only MISSING items are reported. INFERABLE items are noted with the inference chain. ANSWERED items are discarded.

### 4.2 Question Generation Rules

Questions are generated in four categories. Each major story element must be interrogated against all applicable categories.

**Category W — WHY (Motivation & Cause)**
- Why did [character] do [action]?
- Why did [event] happen?
- Why did [character] not do [obvious alternative action]?
- Why did [situation] persist for [duration]?

**Category H — HOW (Mechanism & Feasibility)**
- How was [action] physically/technically possible?
- How did [character] know [information]?
- How did [character] get access to [resource/location/person]?
- How did [event] remain secret for [duration]?

**Category W2 — WHEN (Timeline Integrity)**
- When exactly did [event] happen relative to [other event]?
- If [character] said [X] in episode N, but [episode M] implies [not-X], which is true and why?

**Category S — SO WHAT (Consequence)**
- What changed because of [event]?
- Why does [event] matter to [character]?
- What would be different if [event] had not happened?

### 4.3 Major Story Element Identification

Not every sentence needs WHY-checking. The agent identifies major story elements using this threshold:

A story element requires WHY-checking if it meets any of the following:
- A character makes a decision that changes the plot direction
- A character has an ability, resource, or knowledge not previously shown
- A situation has persisted for more than a story-day without explanation
- A character fails to take an obvious action
- Two episodes state contradictory facts about the same situation
- A new character is introduced who affects the plot within their introduction episode
- A plot-critical secret is revealed (explanation of how the secret was kept is required)

### 4.4 The Explanation Sufficiency Standard

An explanation is ANSWERED only if it appears in the episode text and meets both:
1. **Specificity**: "because of plot reasons" or vague gestures at genre convention are not answers
2. **Placement**: the answer must appear before or concurrent with the event it explains, not after (retroactive explains are noted separately as "late explanation" — not missing, but flagged)

An explanation is INFERABLE if a reader with no prior knowledge of the story could construct the answer from facts stated within the text, using only common knowledge (not genre knowledge). The inference chain must be written out explicitly.

### 4.5 Report Format

```markdown
# WHY-Checker Report: [Novel Name]
> Analysis date: {date}
> Episode range: {N}화 ~ {M}화
> Reviewer: {model}

---

## Summary

| Category | MISSING | INFERABLE (weak) | ANSWERED |
|----------|---------|-----------------|----------|
| W — Why | {N} | {N} | (not reported) |
| H — How | {N} | {N} | (not reported) |
| W2 — When | {N} | {N} | (not reported) |
| S — So What | {N} | {N} | (not reported) |
| **TOTAL** | **{N}** | **{N}** | — |

---

## MISSING Explanations (Priority: Critical)

These are the doors with no signs. A reader will stop here and not continue unless they decide to accept the story as arbitrary.

### [MISS-01] {Short title}
- **Element**: {What story fact is unexplained}
- **Episode**: {N}화
- **Question**: {Exact question a reader would ask}
- **Text searched**: Episodes {range} — no answer found
- **Impact**: {Why this gap matters to the story — what it breaks}
- **Fix options**:
  - Option A: {Minimal fix — add 1-2 sentences where}
  - Option B: {Structural fix — if the explanation requires story changes}

### [MISS-02] ...

---

## INFERABLE Explanations (Priority: Warning)

These can be inferred, but require the reader to do work that the author should have done. Weakly inferable explanations will be missed by casual readers and skimmed readers.

### [INF-01] {Short title}
- **Element**: {What story fact requires inference}
- **Episode**: {N}화
- **Question**: {The question}
- **Inference chain**: {Step-by-step reasoning required} — {Inference strength: Weak/Moderate}
- **Fix**: {One sentence that would make this explicit}

---

## Timeline Contradictions (Priority: Critical if contradictory, Warning if ambiguous)

### [TIME-01] {Short title}
- **Contradiction**: Episode {N}화 states {X}. Episode {M}화 states or implies {not-X}.
- **Quote A**: "{exact text from episode N}"
- **Quote B**: "{exact text from episode M}"
- **Resolution needed**: {What the story needs to clarify}

---

## Late Explanations (Priority: Note)

These are explained, but the explanation comes after the event. The reader experiences the confusion first, then the answer. Consider moving the explanation earlier.

| # | Element | Event Episode | Explanation Episode | Gap |
|---|---------|--------------|--------------------|----|
| 1 | {fact} | {N}화 | {M}화 | {M-N} episodes |

---
```

### 4.6 Operating Constraints

1. **Text-only rule**: The agent reads only the episode markdown files. It does NOT read `summaries/`, `plot/`, or `settings/`. Those documents contain the author's model of the story, not the reader's experience of the story.

2. **No genre filling**: If a fact could be explained by "that's how this genre works," that is not an answer. Only explicit in-text explanations count.

3. **No hallucinated answers**: If the agent is unsure whether a passage answers a question, it must quote the passage and mark it as INFERABLE with the inference chain written out. It cannot assume.

4. **Scope discipline**: Only major story elements are checked. The agent must resist flagging every small unexplained detail. The threshold in section 4.3 is the gate.

5. **No overlap with full-audit**: Factual continuity errors (character X was dead but appears) go to `full-audit`. Timeline contradictions go to WHY-checker only when the contradiction involves an unexplained discrepancy that a reader would find confusing, not a clear authorial error.

---

## Part 5: Integration Into the Writing Pipeline

### 5.1 Where WHY-Checker Fits

The existing pipeline in `no-title-015/CLAUDE.md` section 3 is:

```
3.1 Prep → 3.2 Write → 3.3 Review (unified-reviewer + external AI) → 3.4 Continuity Check → 3.5 Post-Process
```

WHY-checker is NOT a per-episode tool. Running it after every episode would be noisy and miss cross-episode gaps. It belongs at two points:

**Point A: Arc completion (every 10 episodes)**
After completing an arc, run WHY-checker on the full arc. This catches gaps that accumulate across episodes — the "37 years without explanation" type that was introduced in episode 2 and never addressed by episode 51.

**Point B: Novel completion (before final publish)**
Full-novel pass. This is when the CEO/daughter/37-years type problem becomes visible — a thread introduced early that was never resolved.

**Point C: Planning stage (before writing — see section 5.2)**

### 5.2 Pre-Writing WHY-Checker (Planning Stage Integration)

This is where the game design analogy to playtesting is strongest. In game design, the best time to fix a confusing level is before it is built, not after.

Before writing an arc, the writer creates an arc plan. The WHY-checker can be applied to the PLAN, not the finished text:

**Planning WHY-Checker prompt:**
> Read the arc outline below. For every major planned event, generate the WHY/HOW/WHEN/SO-WHAT questions a reader will ask. For each question, identify: is this answered in the plan? If not, is it answered by what was established in previous arcs? If not, it is a planning gap that must be addressed before writing begins.

This catches missing explanations at zero cost — before words are written. A gap found in planning takes one sentence in the outline to fix. The same gap found after 10 episodes of prose may require restructuring.

### 5.3 Mathematical Model for Gap Priority

Not all missing explanations are equal. Priority is determined by two axes:

**Axis 1: Reader impact** — How many readers will notice and be pulled out of the story?
- Score 3: Central to the main plot (the CEO's 37-year failure is the central mystery)
- Score 2: Affects a major character or subplot
- Score 1: Background detail that most readers will not question

**Axis 2: Fix cost** — How much does fixing it require changing existing text?
- Score 1: Add 1-3 sentences to an existing scene
- Score 2: Add a new scene or substantially rewrite an existing scene
- Score 3: Requires retroactive changes to multiple earlier episodes

**Priority score = Impact × (4 - Fix_cost)**

| Priority Score | Action |
|---------------|--------|
| 6-9 | Fix before publishing this arc |
| 3-5 | Fix before publishing the novel |
| 1-2 | Optional — note for revision |

This prevents the agent from generating 50 equally-weighted findings that paralyze the writer. The 37-year CEO gap scores 3 × 3 = 9 (central plot, can be fixed with one flashback sentence). The timeline contradiction between episodes 49 and 50 scores 3 × 2 = 6 (central plot, requires rewriting one scene). Both are fix-now. A background character's unstated motive for a minor action might score 1 × 3 = 3 — noted but not urgent.

---

## Part 6: Practical Implementation as an Agent File

The WHY-checker agent would be added to the `.claude/agents/` folder as `why-checker.md`. The key implementation decisions:

**When invoked**: `/why-check` command (arc range or full novel)

**Input**: Episode files only — never summaries or planning docs

**Output file**: `summaries/why-check-report.md`

**Invocation examples**:
```
/why-check arc-05          # Check episodes 41-50
/why-check 41-51           # Check specific episode range
/why-check full            # Full novel pass
/why-check plan arc-06     # Planning mode — apply to arc outline, not finished text
```

**Critical design constraint in the agent prompt**: The agent must be instructed to begin Pass 1 (question generation) completely before starting Pass 2 (answer audit). If question generation and answer search are interleaved, the agent will unconsciously search for answers as it generates questions, biasing toward ANSWERED findings and missing MISSING ones. The two passes must be structurally separated.

This separation mirrors the game design principle: you must run a naive playtest session (Pass 1, no help allowed) before the debrief session (Pass 2, answers provided). Mixing them destroys the naive signal.

---

## Part 7: Why This Is Different From What Exists

| Dimension | full-audit | narrative-reviewer P7 | WHY-checker |
|-----------|------------|----------------------|-------------|
| Question asked | "Is stated fact consistent with prior stated fact?" | "Is causality legible in the prose?" | "Is the explanation present in the text at all?" |
| Blindspot | Cannot find what was never written | Evaluates quality of what exists | Specifically targets what does not exist |
| Source of truth | episode text + summaries | episode text + style guide | episode text ONLY |
| Runs when | Every episode or arc | Arc/novel completion | Arc/novel completion + planning |
| Output | Factual errors, typos | Artistic quality diagnosis | Missing explanation inventory |
| Reader simulation | None — author-brain checks author-brain | Partial — structured analysis | Strong — naive reader simulation enforced by text-only constraint |

The WHY-checker does not replace the existing agents. It fills the specific gap that neither of them is architecturally capable of filling: detecting the absence of information rather than evaluating the quality of information that is present.

The human reader who found the four problems in the 51-episode SF novel was not doing something the existing agents cannot do in principle. They were doing it in practice, automatically, because they had no author's model to fill the gaps with. The WHY-checker replicates that advantage by structurally forbidding the agent from using the author's model.
