# Batch Audit Supervisor Prompt (Lean)

Claude Code periodically checks a tmux session and automatically supervises another AI instance's full novel audit.

> **Why N-episode batching is needed:**
> Claude Code has auto-compact, so it can run the full audit at once (`N=-1`).
> However, models without auto-compact (GLM-5, Qwen, etc.) need to audit in N-episode batches with `/clear` between batches to prevent context overflow.

**Note: The audited novel content and all audit output are in Korean.**

## Execution Structure

```
/root/novel/                    <- Supervisor Claude Code runs here
├── no-title-XXX/               <- Auditor works in this novel folder
│   ├── batch-supervisor-audit.md  <- This file (supervision rules)
│   └── ...
```

- **Supervisor**: Open Claude Code at `/root/novel/` (parent folder) and input this prompt.
- **Auditor**: Inside a tmux session, navigate to the novel folder and run the AI.

---

## Variable Auto-Inference

Since this file resides inside the novel folder, the supervisor **auto-infers** the following variables from the file path. No manual setup needed.

| Variable | Inference Rule | Example |
|----------|---------------|---------|
| `NOVEL_ID` | Folder name containing this file | `no-title-013` |
| `SESSION` | `audit-{numeric part}` | `audit-013` |
| `NOVEL_DIR` | Absolute path of this file minus filename | `/root/novel/no-title-013` |

User-specified values in the prompt:

| Variable | Description | Example |
|----------|-------------|---------|
| `BATCH_SIZE` (= N) | Episodes per batch | `10` |
| `START_EP` | Starting episode (optional, default 1) | `1` |
| `END_EP` | Ending episode (optional, default last) | `100` |

### BATCH_SIZE Configuration Guide

| Value | Meaning | Suitable Models |
|-------|---------|----------------|
| `-1` | Audit all at once (uses auto-compact) | Claude Code |
| `10` | Audit 10 eps + /clear, repeat | GLM-5, Qwen, etc. (128K context) |
| `5` | 5 eps per batch (conservative) | Models with small context, novels with long episodes |
| `20` | 20 eps per batch (aggressive) | Models with ample context |

> Model/endpoint is configured in the novel folder's `.claude/settings.local.json` `env` section. The supervisor always runs `claude` only.

---

## Usage

```bash
# Supervisor runs from the parent folder
cd /root/novel
claude
```

Input the following prompt into Claude Code:

---

## Prompt

Infer NOVEL_ID, SESSION, and NOVEL_DIR from this file's path, then supervise a batch audit. Follow these rules.

### 0. Variable Inference

Determine variables from this file's path:
- **NOVEL_ID**: Folder name containing this file (e.g., `no-title-013`)
- **SESSION**: `audit-{numeric part}` (e.g., `no-title-013` -> `audit-013`)
- **NOVEL_DIR**: Absolute path of this file minus the filename (e.g., `/root/novel/no-title-013`)

**Ignore other novels' sessions (audit-001, etc.) if they already exist. Always use only the SESSION inferred above.**

### 1. Session Management

- tmux session name: the `SESSION` inferred above
- **If session doesn't exist**: Create with `tmux new-session -d -s {{SESSION}} -x 220 -y 50`, then launch the auditor using the command send protocol below.
- **If session exists**: Capture the screen to assess current state and continue
- **Session size**: Must be 220x50 or larger to prevent capture-pane truncation

#### Command Send Protocol

Do not rely on a single `tmux send-keys ... Enter` call. `Enter` may occasionally fail to register.

Always send commands in this order:

```bash
tmux send-keys -t {{SESSION}} -l 'command text'
sleep 0.3
tmux send-keys -t {{SESSION}} Enter
```

Then verify shortly after:

```bash
sleep 2
tmux capture-pane -t {{SESSION}} -p -S -20
```

If Enter likely failed (command visible but still at `> ` prompt), resend only Enter once. Apply this protocol to all prompt sends, `/clear`, and recovery commands.

### 2. Batch Planning

#### BATCH_SIZE = -1 (Full Audit)

1. Send `/audit` or `/audit {{START_EP}}-{{END_EP}}` prompt to the auditor.
2. Supervise until completion. Do not `/clear` (rely on auto-compact).

#### BATCH_SIZE = N (N-Episode Batches)

Split the start-to-end range into N-episode batches:

```
Example: START_EP=1, END_EP=35, BATCH_SIZE=10
-> Batch 1: 1-10
-> Batch 2: 11-20 (--resume 20)
-> Batch 3: 21-30 (--resume 30)
-> Batch 4: 31-35 (--resume 35)
```

- First batch: `/audit {{START_EP}}-{first batch end}`
- Subsequent batches: `/audit {next batch start}-{batch end}` (tracker in `full-audit-carry.md` tracks progress)
- Last batch: proceed even if remaining episodes < N

### 3. Audit Prompts

#### 3a. First Batch Prompt

```
/audit {{START_EP}}-{{BATCH_END}}
```

#### 3b. Subsequent Batch Prompt (after /clear)

```
/audit {{NEXT_BATCH_START}}-{{BATCH_END}}
```

#### 3c. Full Audit Prompt (BATCH_SIZE = -1)

```
/audit
```

Or with range:

```
/audit {{START_EP}}-{{END_EP}}
```

### 4. Supervision Loop

#### 4a. Screen Capture

```bash
tmux capture-pane -t {{SESSION}} -p -S -50
```

- `-S -50`: Capture only the last 50 lines (token savings)

#### 4b. State Assessment Criteria

| State | Detection Pattern | Action |
|-------|-------------------|--------|
| **Working** | No `> ` prompt visible, text being output. Or `Working`, `Thinking`, `Simmering` etc. | Re-check after 2 minutes |
| **Auto-compact triggered** | `Auto-compact` or `Compacting conversation` message | Normal (expected for BATCH_SIZE=-1). Re-check after 2 minutes |
| **Stuck asking question** | Line ending with `?` followed by `> ` prompt | Send appropriate answer |
| **Permission request** | `Allow`, `Deny`, `permission` etc. with input wait | `tmux send-keys -t {{SESSION}} 'y' Enter` |
| **Error occurred** | `Error`, `error`, `FATAL`, `Traceback` etc. | Analyze error cause, send recovery command |
| **MCP connection failure** | `MCP`, `connection`, `timeout`, `ECONNREFUSED` etc. | Try reconnecting with `/mcp`. If repeated failure, restart session |
| **Infinite loop** | Same operation repeated 3+ times, or no progress on same episode for 15+ minutes | `/clear` then restart with `--resume` prompt |
| **Completed** | `> ` prompt appears, preceding output contains report completion messages | Proceed to next batch or finish |
| **Abnormal exit** | No AI process, only bash prompt (`$`) visible | Restart with `unset CLAUDECODE && claude` |
| **Context overflow** | `context`, `token limit`, `too long` etc. | `/clear` then restart with `--resume` prompt. BATCH_SIZE was too large — reduce for subsequent batches |

#### 4c. Completion Verification

To determine batch completion, verify all of the following:

1. **Prompt waiting**: `> ` or `>` prompt on the last line of the screen
2. **Report updated**: `summaries/full-audit-report.md` exists and includes the batch's last episode
3. **Tracker updated**: `summaries/full-audit-carry.md` records the batch's last episode

```bash
# Check last audited episode in report
grep -oP '### \K\d+(?=화)' {{NOVEL_DIR}}/summaries/full-audit-report.md | tail -1

# Check last completed episode in tracker (YAML format)
grep 'last_episode_audited' {{NOVEL_DIR}}/summaries/full-audit-carry.md
# Note: carry file is deleted on full completion. If missing, audit is done.
```

#### 4d. Batch Transition Procedure (BATCH_SIZE > 0)

When a batch completes:

1. **Verify report**: Confirm tracker's last completed episode matches batch end
2. **Send `/clear`**: `tmux send-keys -t {{SESSION}} '/clear' Enter`
3. **Wait 3 seconds**: `sleep 3`
4. **Send next batch prompt**: `/audit --resume {next batch end}`
5. Repeat until last batch

#### 4e. Supervision Intervals

| Situation | Check Interval |
|-----------|----------------|
| Immediately after sending prompt | 30 seconds later to confirm start |
| Work in progress | Every 2 minutes |
| After error recovery | Every 1 minute for 3 checks, then normal interval |
| After `/clear` | 10 seconds later, then send prompt |

### 5. Special Situation Handling

#### 5a. Context Overflow Response

When context overflow occurs mid-batch on a model without auto-compact:

1. Current batch was interrupted — run `/clear`
2. Check actual last completed episode from tracker
3. Retry next batch with BATCH_SIZE **reduced by 2**
4. If still failing, reduce further (minimum 3 episodes)
5. Log the adjusted batch size in supervisor output

#### 5b. Report Integrity Check

After the full audit is complete:

1. Verify `full-audit-report.md` includes all episodes in the START_EP~END_EP range
2. If episodes are missing, run supplemental audit for that range only: `/audit {missing range}`
3. Verify the **summary table** at the top of the report reflects the full range
   - Batch-based resumption may cause the summary to only reflect the last batch
   - In that case, ask the auditor to recalculate the summary:
     ```
     summaries/full-audit-report.md의 상단 요약 테이블과 전체 패턴 분석을 전 범위({{START_EP}}~{{END_EP}}화)로 재계산해줘. 본문 내용은 수정하지 말고 요약 통계만 갱신.
     ```

#### 5c. Session Crash Recovery

If the session has completely disappeared:

1. Check session existence with `tmux ls`
2. If missing, recreate session (Section 1 session management procedure)
3. Check last completed episode from tracker
4. Resume from next batch with `--resume` prompt

### 6. Log Management

The supervisor outputs progress in this format:

```
[HH:MM] Batch audit start: {{NOVEL_ID}} eps {{START_EP}}~{{END_EP}}, BATCH_SIZE={{BATCH_SIZE}}
[HH:MM] Batch 1/N: eps {S}-{E} prompt sent
[HH:MM] Audit in progress (2m)
[HH:MM] Batch 1/N completed (results: ❌{n} ⚠️{n} 💡{n})
[HH:MM] /clear performed
[HH:MM] Batch 2/N: --resume {E} prompt sent
[HH:MM] Error detected: {error summary} -> attempting recovery
[HH:MM] Context overflow -> BATCH_SIZE 10->8 adjusted
[HH:MM] Full audit completed: ❌{n} ⚠️{n} 💡{n}
[HH:MM] Report integrity check completed
```

### 7. Termination Conditions

- Supervision ends when all batches through END_EP are completed
- After report integrity check, output final summary:
  ```
  -- Batch audit completed --
  Novel: {{NOVEL_ID}}
  Range: eps {{START_EP}}~{{END_EP}}
  Batches: {N}
  Total items: ❌ {n}, ⚠️ {n}, 💡 {n}
  Report: summaries/full-audit-report.md
  ```
- Halt and report to user if 3 consecutive unrecoverable errors occur
- If the supervisor's own context is running low, summarize current progress and output a handoff prompt for continuation, then terminate

### 8. Range

Episodes {{START_EP}} through {{END_EP}}, BATCH_SIZE={{BATCH_SIZE}}.

---

## Supervisor Self-Replacement Prompt

When the supervisor's context is running low, output a handoff prompt in this format:

```
Continue batch audit supervision.
- Novel: {{NOVEL_ID}}
- Session: {{SESSION}}
- Full range: eps {{START_EP}}~{{END_EP}}
- BATCH_SIZE: {{BATCH_SIZE}}
- Current batch: {K}/{N} (eps {S}-{E}, {state})
- Last completed: ep {M}
- Remaining range: {M+1}~{{END_EP}}
- Notes: {describe if any}
- Follow batch-supervisor-audit.md rules.
```
