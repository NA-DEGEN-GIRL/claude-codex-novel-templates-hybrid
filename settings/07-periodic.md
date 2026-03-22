# Parallel Writing & Periodic Checks

> Defines consistency checks after parallel writing and periodic checks (default every 5 episodes, flexible up to 8).

**Language Contract: All narrative output, summaries, and review text MUST be in Korean.**

---

## 1. Post-Parallel-Writing Consistency Check

When episodes are written in parallel, the following procedure MUST be performed **after writing is complete**.

### Parallel Writing Criteria

Any of the following qualifies as "parallel writing":
- Multiple agents writing different episodes simultaneously
- Consecutive episodes exist where summary files were not updated
- User explicitly states parallel writing is in progress

### Per-Agent Rules

- Steps 3.1-3.3 proceed as normal (context loading, writing, self-review)
- Step 3.4 continuity verification: perform only within own assigned range
- Step 3.5 post-processing: **defer summary updates** (to prevent conflicts)
- EPISODE_META insertion: perform as normal

### Post-Completion Reconciliation

1. **Cross-continuity verification**: Run `unified-reviewer` in `continuity` mode to check inter-episode connections
2. **Conflict resolution**: Adjust higher-numbered episodes to match lower-numbered ones
3. **Batch summary update**: Update all summary files in episode-number order

---

## 2. Periodic Checks

> Prevents **cumulative drift** that per-episode pipelines cannot catch.

### Trigger

- 5화 단위를 기본으로 하되, 아크 전환·드리프트 징후·작가 판단에 따라 앞당기거나 늦출 수 있다. 단, 최대 8화를 넘기지 않는다.
- Arc transition points (perform even if fewer than 5 episodes)

### Check Items

> Core 항목(P1, P3, P6, P9, P10)은 매 점검 시 필수. Optional 항목(P2, P4, P5, P7, P8)은 해당 소설에 관련이 있을 때만 수행.

| # | Item | Method |
|---|------|--------|
| P1 | Summary consistency | `unified-reviewer` in `standard` mode — verify summary accuracy (S1-S6) for episodes since last check |
| P2 | Foreshadowing deadlines | Check `plot/foreshadowing.md` for threads past their expected resolution point |
| P3 | Character state freshness | Verify `summaries/character-tracker.md` current state matches **latest episode end state** |
| P4 | Unfulfilled promises | Check `summaries/promise-tracker.md` for overdue or neglected promises |
| P5 | running-context | Verify `summaries/running-context.md` is under 200 lines and accurately reflects current state |
| P6 | Personality drift vs growth | 캐릭터 변화가 문서화된 사건에 의한 것인지 확인. 비선형적 변화(일시적 퇴행, 갈등 속 동요)도 의도적이라면 허용. (a) 사건 근거 없이 확립된 상태에 반하는 행동 → ❌. (b) `character-tracker.md`에 사건 근거가 있는 변화 → ✅ intentional. (c) 일시적 퇴행·동요가 서사적으로 의도된 경우 → ✅ (사유 기록) |
| P7 | External AI batch review | Call `mcp__novel_editor__batch_review` for episodes since last check. If `batch_review` is unavailable, call `review_episode` individually for each episode. Only target active sources per CLAUDE.md §1 feedback flags (gemini/gpt/nim/ollama). Prioritize episodes with `❌ 실패` records in `editor-feedback-log.md` |
| P8 | Korean quality check | Only for episodes where P7 produced text modifications — re-check via `unified-reviewer` continuity mode (includes Korean proofreading) |
| P9 | Meta-reference prohibition | Full scan for in-prose references like "X화에서", "프롤로그에서", "1부에서" (episode number/structure name references) |
| P10 | Thematic progress | Review EPISODE_META `thematic_function` entries for the last 5 episodes. Is the novel's thematic statement (CLAUDE.md §1.2) being advanced? If 3+ consecutive episodes have no thematic connection, flag for review. |

### Post-Check Actions

1. 치명/중대 이슈는 즉시 수정. 경미 이슈는 누적 기록 후 다음 집필 사이클에서 정리.
2. Update `running-context.md` to current state.
3. Include check results in commit: `{소설명} {N}~{M}화 정기 점검 완료`

---
