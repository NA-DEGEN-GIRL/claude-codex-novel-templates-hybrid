# Batch Writing Supervisor Prompt (Hybrid)

Claude Code periodically checks a tmux session and automatically supervises a Codex (GPT 5.4) instance's novel writing. Hybrid mode: Codex writes, Claude reviews/fixes/manages.

> **Why Claude Code instead of a script?**
> A bash script (file-existence/timeout-based) cannot judge the AI's actual state.
> Claude Code directly reads the tmux screen and understands context, enabling accurate decisions.

**Note: The supervised writer produces all novel output in Korean.**

## Execution Structure

```
/root/novel/                    <- Supervisor Claude Code runs here
├── no-title-XXX/               <- Writer works in this novel folder
│   ├── batch-supervisor.md     <- This file (supervision rules)
│   └── ...
```

- **Supervisor**: Open Claude Code at `/root/novel/` (parent folder) and input this prompt.
  - Reads the parent folder's CLAUDE.md (project guide), giving it full context for config.json management etc.
- **Writer**: Inside a tmux session, navigate to the novel folder (`no-title-XXX/`) and run `codex --dangerously-bypass-approvals-and-sandbox`.
  - Codex가 소설 폴더의 설정 파일을 직접 읽고 본문을 생성한다. 리뷰/summary/commit은 supervisor가 처리.

`settings/`는 hybrid, Claude lean, Codex lean이 공유하는 공통 집필 레이어다. 이 문서는 hybrid 세션 오케스트레이션만 정의하며, 문체/캐릭터/연속성/정기 점검 규칙이 충돌하면 `settings/`를 우선한다.

---

## Configuration Variables

Modify these values for your novel before inputting the prompt.

| Variable | Description | Example |
|----------|-------------|---------|
| `NOVEL_ID` | Novel folder name | `no-title-015` |
| `SESSION` | tmux session name | `write-015` |
| `NOVEL_DIR` | Novel absolute path | `/root/novel/no-title-015` |
| `START_EP` | Starting episode | `1` |
| `END_EP` | Ending episode | `70` |
| `CHUNK_SIZE` | /clear interval (in episodes). **`-1` = never /clear** (use auto-compact instead) | `10` or `-1` |
| `WRITER_CMD` | Writer launch command | `codex --dangerously-bypass-approvals-and-sandbox` |
| `ARC_MAP` | Arc-to-episode mapping | See below |

### WRITER_CMD Examples

| Value | Description |
|-------|-------------|
| `codex --dangerously-bypass-approvals-and-sandbox` | **Hybrid default**: GPT 5.4 writer, 승인 프롬프트 없이 파일 읽기/쓰기 |
| `claude` | Lean fallback: Claude Code 전체 파이프라인 (hybrid에서는 비권장) |
| `claude --model claude-sonnet-4-6` | Specify a particular model |

### ARC_MAP Example

```json
{
  "arc-01": [1, 10],
  "arc-02": [11, 20],
  "arc-03": [21, 30]
}
```

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

Supervise batch writing for the {{NOVEL_ID}} novel. Follow these rules.

### 1. Session Management (Hybrid: 3세션 필수)

**Supervisor** (메인 터미널):
- `/root/novel/`에서 실행. tmux 관리 + 상태 판단 + 프롬프트 조립만 담당.
- 리뷰/검증/수정은 직접 수행하지 않고, Review 세션의 Claude에게 지시한다.
- 메인 세션에서 직접 해도 되는 일은 `tmux` 관리, 상태 판독, sentinel 대기, 파일 존재 확인, `/root/novel/config.json` 갱신뿐이다.
- review 세션이 맡아야 할 후처리를 메인 세션에서 직접 시작하면 안 된다. 그 조짐이 보이면 즉시 멈추고 review 세션으로 재전송한다.

**Writer 세션** (Codex — 집필 + 수정):
- tmux session name: `{{SESSION}}` (예: `write-001`)
- **If session doesn't exist**: Create with `tmux new-session -d -s {{SESSION}} -x 220 -y 50 -c {{NOVEL_DIR}}`, then launch `{{WRITER_CMD}}`
- **If session exists**: Capture the screen to assess current state and continue
- Codex가 집필과 fix-spec 수정을 모두 같은 세션에서 수행 (writer = fixer).

**Review 세션** (Claude Code — 리뷰/검증/후처리):
- tmux session name: `{{SESSION}}-review` (예: `write-001-review`)
- `tmux new-session -d -s {{SESSION}}-review -x 220 -y 50 -c {{NOVEL_DIR}}` → `unset CLAUDECODE && claude` 실행
- unified-reviewer, external AI review(MCP), summary 갱신, EPISODE_META 삽입, git commit 수행.
- supervisor가 review 세션에 post-write 지시를 전송한다.
- **Session size**: Must be 220x50 or larger
- **완료 sentinel 강제**:
  - 화별 post-write 완료 후: `REVIEW_DONE chapter-{NN}`
  - fix 재검증 완료 후: `RECHECK_DONE chapter-{NN}`
  - 아크 경계 패키지 완료 후: `ARC_DONE {arc}`
- review 세션 프롬프트 전송은 기본적으로 `bash {{NOVEL_DIR}}/scripts/tmux-send-claude {{SESSION}}-review '...' 2 80`을 사용한다.

> **3세션 필수**: supervisor는 tmux 관리에 집중하고, 리뷰/후처리는 반드시 Review 세션에서 수행한다. context 분리로 안정적 운영을 보장.

### 2. Episode-to-Arc Mapping

```
{{Describe ARC_MAP here}}
```

Given episode number N, determine the arc and zero-padded filename from this mapping:
- Arc: the key whose range contains N
- File: `chapters/{arc}/chapter-{NN}.md` (NN = zero-padded 2 digits, or 3 digits if 100+ episodes)

### 2.5 Review Floor Determination (Supervisor Responsibility)

Before sending any writing prompt, the supervisor determines the `review_floor` for that episode:

```
if N is first episode of a new arc   → review_floor = full
elif N is last episode of current arc → review_floor = standard + arc transition package
elif N % 5 == 0                       → review_floor = standard
else                                  → review_floor = continuity
```

**Arc transition package** (마지막 화 완료 후 supervisor가 반드시 순서대로 지시):

> **주의**: writer가 자체적으로 arc summary만 만들고 A~E를 스킵하는 경우가 있다. supervisor가 A→B→C→D→D.5→D.7→E→F를 빠짐없이 순차 지시해야 한다. 한 단계가 완료되었음을 확인한 뒤 다음 단계를 지시한다.
>
> **로그 필수**: 각 단계의 프롬프트에 반드시 `summaries/action-log.md에 결과를 한 줄 append할 것`을 포함한다. 세션이 분리되면 action-log 갱신이 누락되기 쉬우므로, 프롬프트 자체에 명시해야 한다.

**A. OAG 탐지 + 플롯 수선** (plot-change-needed가 있을 때만)
1. `/oag-check` on completed arc → `oag-report.md`
2. `plot-change-needed` 항목 확인:
   - 없으면: B단계로 건너뜀
   - 있으면:
     a. `/plot-repair` → proposal + 평가 + supervisor 승인 (§2.6 기준)
     b. 승인 시: plot-surgeon이 plot 파일 수정 + `rewrite-brief.md` 생성
     c. writer partial-rewrite로 기집필 본문 재작성 → `rewrite-log.md`
     d. `/oag-check plan {arc}` 재검증 (수정된 플롯 기준)
     e. 재검증 통과 후 B단계로

**B. 본문 패치** (patch-feasible 항목)
3. `/narrative-fix --source oag` — `patch-feasible` 항목만 행동 갭 수정 (CRITICAL→HIGH 순)

**C. 설명 갭**
4. `/why-check text` on completed arc (수정된 본문에서 설명 누락 탐지)
5. `/narrative-fix --source why-check --scope priority-6+` — 설명 보강

**D. 아크 통독 (외부 AI)**
6. 모든 수정(A~C)이 반영된 **최종본** 기준으로 외부 AI 아크 통독을 수행한다.
   - **기본 전송 방식은 전문 일괄 전송이 아니라 `Context Bundle`이다.**
   - 기본 입력 묶음:
     - `summaries/running-context.md`
     - `summaries/episode-log.md`에서 해당 아크 구간
     - `compile_brief`로 생성한 아크 압축 brief
     - **최근 수정된 화수 전문만 추가** (A~C에서 손댄 화 + 인접 1화)
   - 전문 전체 전송은 **예외 모드**다. 외부 AI가 "이 항목은 원문 확인 없이는 판정 불가"라고 명시한 경우에만, 해당 화수만 chunk로 분할 전송한다.
   - **프롬프트 목적** (품질 평가가 아니라 흐름 결함 탐지):
     - 에피소드 간 중복 정보/문장 재노출
     - 사건/방문/결정의 타이밍 어색함
     - 직전 사건 대비 인물 반응 불일치
     - 독자가 "어? 이거 아까 했는데?" 또는 "왜 이 순서지?" 라고 멈칫하는 지점
   - **산출물 파일**: `summaries/arc-readthrough-report.md`
   - **항목 형식**: `ID / severity / 관련 화수 / 결함 유형 / 근거 / 최소 수정안 / patch-feasible 여부 / 상태(open|hold|resolved)`
   - supervisor가 보고서를 읽고 분류:
     - `patch-feasible = yes`이고 1~2화의 국소 수정으로 해결 가능 → `/narrative-fix --source arc-read`
     - 구조 변경 필요, 3화 이상 연쇄 영향, 플롯 재배선 필요 → `[HOLD]`로 남기고 다음 `/narrative-review` 또는 `/plot-repair` 사이클로 이관
   - 결함 없으면: E단계로

**D.5. 전문 감사 (시점·시대 + 장면 논리)**

> D 결과와 무관하게 **아크 경계에서 항상 실행**한다. 문장 수준의 정밀 오류를 잡는 단계.

6a. `/pov-era-check {start}-{end}` — 시점 지식 위반 + 시대 부적합 표현 배치 검사 → `summaries/pov-era-report.md`
6b. `/scene-logic-check {start}-{end}` — 장면 내부 물리 논리 배치 검사 → `summaries/scene-logic-report.md`

> **체크는 병렬 가능**. 6a와 6b는 독립적이므로 동시 실행 OK.

6c. **수정은 직렬**: `pov-era fix` → `scene-logic fix` 순서. 같은 화를 동시에 수정하면 편집 충돌.
   - `/narrative-fix --source pov-era` — ❌ 항목 수정
   - `/narrative-fix --source scene-logic` — ❌ 항목 수정
6d. **수정 후 source checker 재실행**: 수정된 화수에 대해 해당 checker를 재실행하여 ❌ 0건 확인
6e. 수정 후 해당 화수 summaries 재갱신 + `summaries/action-log.md`에 결과 append

**D.7. 크로스 에피소드 반복 감사**

> 아크 경계에서 항상 실행. 표현/감정/정보전달/구조 반복 패턴 탐지.

6f. `/repetition-check` — 전체 아크 대상 (메타스캔→본문 정밀) → `summaries/cross-episode-repetition-report.md`
6g. HIGH 항목 → `/narrative-fix --source repetition`으로 분산 수정
6h. 수정 후 수정 화수 + 인접 2화 재검사 → `summaries/repetition-watchlist.md` 갱신 + `summaries/action-log.md`에 결과 append

**E. 한국어 자연스러움 교정**
7. `/naturalness` 실행 — Claude(한 문장씩 정밀 검사) + GPT(MCP 별도 세션, effort high) → `summaries/naturalness-report.md`
8. `/naturalness-fix` 실행 — Claude + GPT 결과 모두 처리. 채택된 어휘 치환은 `summaries/style-lexicon.md`에 기록
8a. **(역방향 확인)** E에서 수정한 화수가 D.7에서 해결한 반복 패턴을 새로 만들지 않았는지 확인. 의심되면 해당 화만 `/repetition-check {N}-{M}`으로 경량 재검사.
8b. `summaries/action-log.md`에 자연스러움 교정 결과 append.

**F. 아크 마감**
9. Arc summary + character state reset (settings/05-continuity.md)
10. Unresolved thread triage (carry-forward vs discard)

**Hybrid**: `review_floor`은 Codex writer 프롬프트에 넣지 않는다. supervisor가 3b-post에서 직접 해당 모드로 unified-reviewer를 실행한다.

**Arc boundary detection**: Check ARC_MAP:
- **First episode** of any arc → `full` (보이스/설정/톤 진입 제어)
- **Last episode** of any arc → `standard` + arc transition package (why-check + 요약 리셋)
- Both checks apply to prologue, all arcs, and epilogue.

**Periodic check alignment**: When `review_floor = standard` (5화 배수), also add periodic check instruction to the prompt.

### 2.6 Supervisor Plot-Repair Approval Protocol

batch-supervisor는 plot-repair의 "사용자" 역할을 수행할 수 있다. `/plot-repair`의 Step 3.5 평가 결과(`summaries/plot-repair-proposal.md`)를 읽고 직접 승인/거부를 판단한다.

**Supervisor 승인 기준** (모두 충족 시 supervisor가 자동 승인):
1. 내부 평가에서 1위 안이 **GO** 판정
2. 외부 AI 평가를 수행한 경우, **외부도 동일한 안 추천**
3. 1위 안의 치명적 리스크가 **"없음"**
4. 비용이 **대규모 아크 재구성이 아님**
5. 보존 불변식 충돌이 **없음**

**Supervisor 거부 / 사용자 에스컬레이션**:
- 위 조건 중 하나라도 불충족 → supervisor는 집필을 중단하고 사용자에게 알린다
- 1위와 2위 점수 차가 5점 미만 → 사용자 판단 요청
- 수정안이 3개 이상의 아크에 영향 → 사용자 판단 요청

**승인 후 절차**:
1. `plot/prologue.md` (또는 해당 arc) 수정
2. 기집필 에피소드가 있으면 → `/narrative-fix --source oag`로 본문 수정 지시
3. `summaries/plot-repair-log.md`에 `[SUPERVISOR-APPROVED]` 기록
4. `/oag-check plan {arc}` + `/why-check plan {arc}` 재검증
5. 재검증 통과 후 집필 재개

> **주의**: supervisor 승인은 완전 자동화를 위한 것이다. 사용자가 실시간 모니터링 중이면 직접 판단하는 것이 항상 우선한다.

### 3. Writing Prompts

#### 3a. Chunk Start Prompt — Codex Writer (first episode or new session)

> **정본**: `.claude/prompts/codex-writer.md`의 **Chunk Start Prompt**.
> supervisor가 아래 변수를 채워 tmux로 전송한다. **이 문서에 인라인 복사본을 두지 않는다** — 동기화 드리프트 방지.

**채울 변수**: `{N}`, `{arc}`, `{NN}`, `{MIN}`, `{MAX}`, `{{NOVEL_DIR}}`

**공통 집필 레이어**: writer는 `settings/01-style-guide.md`, `settings/03-characters.md`, `settings/05-continuity.md`, `settings/07-periodic.md`를 shared authoring layer로 취급한다. 이 문서는 세션 역할과 순서만 정의한다.

**전송 순서**:
1. `.claude/prompts/codex-writer.md`의 Chunk Start 코드 블록을 읽는다
2. 변수를 치환한다
3. `tmux send-keys -t {{SESSION}} -l '...'` + `sleep 3` + `tmux send-keys -t {{SESSION}} Enter` (§3d 프로토콜)
4. 전송 직후 장시간 고정 `sleep`으로 기다리지 말고, 가능하면 `bash {{NOVEL_DIR}}/scripts/tmux-wait-sentinel {{SESSION}} "WRITER_DONE chapter-{NN}.md" ...` 로 sentinel/timeout을 함께 감시한다.

#### 3b. Continuation Prompt — Codex Writer (previous episode context loaded)

> **정본**: `.claude/prompts/codex-writer.md`의 **Continuation Prompt**.
> 변수 치환 + §3d 전송 프로토콜 동일.

**채울 변수**: `{N}`, `{arc}`, `{NN}`, `{{NOVEL_DIR}}`

#### 3b-post. Supervisor Post-Write Pipeline (Codex 완료 후 Claude가 수행)

> Codex가 `WRITER_DONE`을 출력하면, supervisor(Claude Code)가 아래를 순서대로 수행한다.

1. **chapter 파일 확인**: `ls {{NOVEL_DIR}}/chapters/{arc}/chapter-{NN}.md`
2. **review 세션으로 post-write 지시 전송**: 기본은 `tmux-send-claude`로 보낸다. 아래 작업을 review 세션이 수행하게 한다.
3. **외부 AI 리뷰**: `review_episode` MCP 호출 (sources="auto") — review 세션 수행
4. **unified-reviewer**: review_floor에 맞는 모드로 실행. EDITOR_FEEDBACK 반영 — review 세션 수행
5. **문제 발견 시 — fix routing**:
   a. 모든 발견 항목을 **patch_class**로 분류:
      - `micro`: 사실관계 1-3문장 → **Codex fixer**
      - `local`: 문단 내 수정 → **Codex fixer**
      - `rewrite`: 장면 수준 재작성 → **Codex fixer**
      - `hold`: 구조 변경 필요 → **HOLD Transfer Routing** (아래 §5g 참조)
   b. `micro`/`local`/`rewrite` 항목을 에피소드 단위로 번들: Claude가 `tmp/fix-specs/chapter-{NN}.md` 생성
   c. Codex writer 세션에 전송 (writer = fixer, 같은 세션):
      ```
      tmp/fix-specs/chapter-{NN}.md 를 읽고 해당 에피소드를 수정해줘.
      fix-spec의 수정 목표와 제약만 따른다. 범위 밖 변경 금지.
      완료 후: FIX_DONE chapter-{NN}
      ```
   e. `FIX_DONE` 확인 후 Claude가 수정 결과 검증 (unified-reviewer continuity 모드)
   f. **재수정 상한**: Codex fixer 호출은 **1회 한정**. 재검증에서 추가 문제 발견 시 다음 정기 점검으로 이관. 무한 ping-pong 금지.
6. **summary 갱신**: running-context, episode-log, character-tracker 등 — review 세션 수행
7. **summary fact-check**: 본문 ↔ 요약 대조 — review 세션 수행
8. **EPISODE_META 삽입**: chapter 파일 끝에 append — review 세션 수행
9. **action-log 갱신** — review 세션 수행
10. **git commit**: chapter + summaries + EDITOR_FEEDBACK — review 세션 수행
11. **완료 신호 출력**: review 세션은 마지막 줄에 반드시 `REVIEW_DONE chapter-{NN}` 출력
12. **config.json 업데이트**: `REVIEW_DONE` 확인 후 supervisor가 직접 수행

#### 3c. Plot Generation Prompt (when the arc's plot file doesn't exist)

```
{arc}의 플롯 파일이 없다. plot/{arc}.md를 먼저 작성해줘.
- plot/master-outline.md와 plot/foreshadowing.md를 참조한다.
- 이전 아크의 plot 파일 형식을 따른다.
- 완료 후 {N}화 집필을 이어서 진행한다.
```

#### 3d. Command Send Protocol (Important)

Do not rely on a single `tmux send-keys ... Enter` call for prompts or recovery commands. `Enter` may occasionally fail to register, leaving the command text pasted but not executed.

Always send commands in this order:

```bash
tmux send-keys -t {{SESSION}} -l 'command text'
sleep 3          # Codex: 즉시 Enter = 줄바꿈, 3초 후 Enter = 메시지 전송
tmux send-keys -t {{SESSION}} Enter
```

> **Codex 특이사항**: 텍스트 입력 직후 Enter를 누르면 줄바꿈만 된다. 3초 이상 대기 후 Enter를 눌러야 메시지가 전송된다. 긴 프롬프트는 `sleep 5`도 고려.

**Codex 전용 권장 방식**:

```bash
bash {{NOVEL_DIR}}/scripts/tmux-send-codex {{SESSION}} 'command text' 2 60
```

Then verify shortly after sending:

```bash
sleep 2
tmux capture-pane -t {{SESSION}} -p -S -20
```

Interpretation:

- **Started correctly**: `Working`이 보이거나, 새 응답 블록(`• ...`)이 붙는다
- **Enter likely failed**: `Working`과 새 응답 블록이 2초 안에 모두 보이지 않는다

If Enter likely failed, resend only Enter once:

```bash
tmux send-keys -t {{SESSION}} Enter
sleep 2
tmux capture-pane -t {{SESSION}} -p -S -20
```

Rules:

- Use `-l` for command text so tmux sends the string literally
- Send `Enter` separately; do not use double-Enter by default
- Retry only one extra `Enter` before treating it as a state/error investigation case
- Codex tmux 전송 확인은 `Working` 또는 새 응답 블록만 기준으로 본다. `Explored`, `Edited`, `Ran`은 화면 윗부분의 이전 작업 로그일 수 있다.
- Apply this protocol to all prompt sends, `/clear`, `/why-check`, permission answers, and recovery commands

### 4. Supervision Loop

#### 4a. Screen Capture

```bash
tmux capture-pane -t {{SESSION}} -p -S -50
```

- `-S -50`: Capture only the last 50 lines (token savings)
- If output is long, check only the final portion needed for state assessment

#### 4b. State Assessment Criteria

| State | Detection Pattern | Action |
|-------|-------------------|--------|
| **Working** | `• Working (Ns)` 표시, 또는 `• Explored`, `• Edited`, `• Ran` 등 진행 표시 | Re-check after 2 minutes |
| **Completed (WRITER_DONE)** | `WRITER_DONE chapter-{NN}.md` 출력 + `›` 프롬프트 대기 | **Post-write pipeline (3b-post) 시작** |
| **Completed (prompt ready)** | `›` 프롬프트 + `gpt-5.4` 표시 (WRITER_DONE 없이) | Chapter 파일 존재 확인 후 post-write pipeline |
| **Trust prompt** | `Do you trust the contents` + `Press enter to continue` | Enter 전송 |
| **Error occurred** | `Error`, `FATAL`, `Permission denied` etc. | 분석 후 복구 |
| **Infinite loop** | 같은 파일 반복 편집, 10분+ 진전 없음 | Esc로 중단 후 재지시 |
| **Abnormal exit** | codex 종료, bash `$` 프롬프트만 표시 | `{{WRITER_CMD}}` 재시작 |

#### 4c. Completion Verification

To accurately determine "completed" state, verify all of the following:

1. **WRITER_DONE sentinel**: 기본은 `bash {{NOVEL_DIR}}/scripts/tmux-wait-sentinel {{SESSION}} "WRITER_DONE chapter-{NN}.md" 1800 2 200`으로 감시한다. timeout이면 `tmux capture-pane` + `›` 프롬프트 + 파일 존재를 함께 확인한다.
2. **Work artifact exists**: Chapter file exists (`ls {{NOVEL_DIR}}/chapters/{arc}/chapter-{NN}.md`)
3. **Progress log 기록**: supervisor가 직접 `echo "EP {N} DONE $(date +%H:%M)" >> {{NOVEL_DIR}}/summaries/batch-progress.log` 실행.

> **batch-progress.log 관리**: supervisor가 3b-post 완료(commit까지 끝난 후)마다 기록한다. Codex가 아닌 supervisor의 책임.

All conditions met → 다음 화 프롬프트. 파일 없으면 Codex 재지시.

#### 4c-2. Review Session Completion Verification

review 세션도 writer와 마찬가지로 sentinel 기반으로 완료를 판정한다.

- 화별 post-write: `bash {{NOVEL_DIR}}/scripts/tmux-wait-sentinel {{SESSION}}-review "REVIEW_DONE chapter-{NN}" 1800 2 200`
- fix 재검증: `bash {{NOVEL_DIR}}/scripts/tmux-wait-sentinel {{SESSION}}-review "RECHECK_DONE chapter-{NN}" 900 2 200`
- 아크 경계 패키지: `bash {{NOVEL_DIR}}/scripts/tmux-wait-sentinel {{SESSION}}-review "ARC_DONE {arc}" 3600 3 260`

주의:
- review 세션 프롬프트는 항상 마지막 줄에 해당 sentinel을 출력하라고 명시한다.
- sentinel이 없으면 supervisor는 review 세션 pane과 산출 파일을 직접 확인하고, 필요하면 `tmux-send-claude`로 sentinel 출력만 짧게 재지시한다.

#### 4d. config.json Update (Supervisor Responsibility)

After completion verification, the supervisor directly registers the episode in `/root/novel/config.json`. The writer does NOT touch config.json.

1. Read `title` and `date` from EPISODE_META in the chapter file
2. Add to the novel's appropriate part > `episodes` array:
   ```json
   { "number": N, "title": "제목", "file": "{{NOVEL_ID}}/chapters/{arc}/chapter-{NN}.md" }
   ```
3. Match `totalEpisodes` to the actual registered count
4. If earlier episodes are missing, register them together
5. If the chapter's EPISODE_META contains `intentional_deviations`, note them in the supervision log.

#### 4e. Supervision Intervals

| Situation | Check Interval |
|-----------|----------------|
| Immediately after sending any prompt/command | 2 seconds later to verify execution (3d), then normal interval |
| Immediately after sending first prompt | 30 seconds later to confirm start |
| Work in progress | Every 2 minutes |
| After error recovery | Every 1 minute for 3 checks, then normal interval |
| After chunk boundary (/clear) | 2 seconds later to verify execution, then 1 minute later to confirm start |

### 5. Special Situation Handling

#### 5a. Chunk Boundary (/clear)

**If `CHUNK_SIZE = -1`**: Skip this step entirely. The writer uses auto-compact, which preserves context better than /clear. This is the recommended setting for 1M context models (Claude Opus).

**If `CHUNK_SIZE > 0`**: Reset context every CHUNK_SIZE episodes:

```bash
tmux send-keys -t {{SESSION}} -l '/clear'
sleep 3          # Codex: 3초 대기 후 Enter (즉시 Enter = 줄바꿈)
tmux send-keys -t {{SESSION}} Enter
```

Wait 5 seconds, then send full prompt (3a).

> **When to use CHUNK_SIZE = -1 (recommended)**: Claude Opus or any model with auto-compact. Auto-compact preserves important context while managing window size.
> **When to use CHUNK_SIZE > 0**: Models without auto-compact (NIM proxy models, open-source models), or when context window is small (< 200K).

#### 5b. Arc Transition (Hybrid: Supervisor 직접 실행)

> **Hybrid 핵심**: 아크 전환 A~F는 **Claude supervisor가 직접 실행**한다. Codex writer 세션에 보내지 않는다.
> `/oag-check`, `/why-check`, `/narrative-fix` 등은 Claude 커맨드이므로 Codex에서 동작하지 않는다.
> 수정이 필요하면: 모든 텍스트 수정은 Codex writer 세션에서 수행 (fix routing 적용).

When the episode number enters a new arc range:

1. Confirm completion of the last episode of the previous arc
2. **A. OAG 탐지** — supervisor가 직접 `/oag-check` 실행:
   - `.claude/agents/oag-checker.md` Text Mode
   - 대상: {start}~{end}화
   - 산출물: `summaries/oag-report.md`
   - `plot-change-needed` → `/plot-repair` (supervisor 판단)
   - `patch-feasible` → Claude가 fix-spec 생성 → Codex fixer 수정
3. **B. 본문 패치** — fix routing 적용 (3b-post 동일)
4. **C. 설명 갭** — supervisor가 직접 `/why-check text` 실행
   - MISSING 우선순위 6+ → fix routing 적용
   - HOLD → 다음 사이클 이관
4. **Run external arc readthrough on the completed arc**:
   - Build a `Context Bundle` instead of sending the full arc by default:
     - `summaries/running-context.md`
     - `summaries/episode-log.md` entries for `{start}~{end}`
     - arc-level compressed brief from `compile_brief`
     - full text only for episodes modified in steps 2~3, plus adjacent 1 episode when needed for transition reading
   - Send the bundle to `ask_gpt` or `ask_gemini` with this instruction:
   ```
   방금 완료한 {prev_arc}({start}~{end}화)를 독자처럼 통독하되, 평점이 아니라 "흐름 결함"만 찾아줘.
   찾을 대상:
   - 같은 정보/감정/설명이 에피소드 사이에서 중복 재노출되는 지점
   - 사건, 방문, 결정, 공개 순서가 어색한 지점
   - 직전 사건 대비 인물 반응이 약하거나 어긋나는 지점
   - 독자가 "이미 한 얘기 아닌가?", "왜 이 순서지?"라고 멈칫할 지점

   출력 형식:
   - ID
   - severity (critical/high/medium/low)
   - 관련 화수
   - 결함 유형
   - 근거
   - 최소 수정안
   - patch-feasible (yes/no)

   중요:
   - 입력이 요약 기반이라 확신이 낮으면 추측하지 말고 "원문 필요"라고 명시한다.
   - 원문 필요 항목만 지정하면 supervisor가 해당 화수 전문을 추가 전송한다.
   ```
   - Save the normalized result to `summaries/arc-readthrough-report.md`.
   - If the external AI requests source text for a specific item, send only that episode (or small chunk), not the whole arc.
   - Triaging rule:
     - `patch-feasible: yes` → fix routing → Codex writer 세션에서 수정
     - wider structural issue → `[HOLD]` + **§5g HOLD Transfer Routing** 수행
5. **D.5. 전문 감사** — supervisor 직접:
   - `/pov-era-check` + `/scene-logic-check` 병렬
   - 수정: fix routing 적용
6. **D.7. 반복 감사** — supervisor 직접:
   - `/repetition-check` → HIGH 항목 fix routing
7. **E. 자연스러움** — supervisor 직접:
   - `/naturalness` (Claude + GPT MCP) → `/naturalness-fix`
8. **E.5. 개발편집** — supervisor 직접:
   - `/narrative-review` 실행 → 서사 품질 거시 진단 (10기둥 분석)
   - "이 아크가 좋은 소설로 작동하는가" 판정: 주인공 수동화, 스케일 인플레이션, 주제 표류 감지
   - HIGH 이상 항목 → fix routing (Codex fixer)
   - 사용자 판단이 필요한 구조적 제안 → 사용자에게 보고
9. **F. 아크 마감** — supervisor 직접:
   - Arc summary + character state reset
   - Unresolved thread triage
10. **새 아크 준비** — supervisor 직접:
    - `plot/{arc}.md` 존재 확인 → 없으면 3c로 생성
    - `/oag-check plan` + `/why-check plan` → supervisor 직접 실행
    - 새 아크 컨셉이 장기 연재에서 지속 가능한지 검토 (story-consultant 참조 가능)
    - 정기 점검 트리거: 첫 화 프롬프트에 `※ 아크 전환 시점` 포함

#### 5g. HOLD Transfer Routing

> `patch_class = hold` 항목은 단순 fix-spec으로 해결 불가. supervisor가 즉시 `hold_route`를 분류한다.

**분류 기준:**

| hold_route | 조건 | 행동 |
|------------|------|------|
| `retro-fix` | 이미 쓴 장면이 **사실적으로 거짓**이 됨 (독자가 이미 읽은 내용과 충돌) | 해당 화 수정 — Codex fixer (rewrite급 fix-spec) |
| `forward-fix` | 설명 부족/동기 약화 수준. 미래 5화 내 또는 다음 아크 초반에 자연스러운 보상 가능 | 미래 plot에 보상 비트 삽입. 기존 본문은 건드리지 않음 |
| `plot-repair` | 미래 아크 설계 자체를 다시 짜야 함 | plot-surgeon 호출 |
| `user-escalation` | 핵심 약속(§1.1) 위반, 3개+ 아크 영향, 세계관 규칙 변경 필요 | 집필 중단 + 사용자에게 보고 |

**retro-fix vs forward-fix 판단:**
- 이미 쓴 장면이 **"거짓"** (사실 오류, 모순) → `retro-fix`
- 이미 쓴 장면이 **"부족"** (설명 누락, 동기 약화) → `forward-fix` 가능
- 판단이 애매하면 → `forward-fix` 우선 (기존 본문 보존이 더 저렴)

**forward-fix 기록 (3중 추적):**

1. **`summaries/review-log.md`** (원장): HOLD 항목으로 기록
   ```
   ### HOLD-{NNN}
   - hold_route: forward-fix
   - scope: {current-arc | next-arc}
   - 출처: {checker} / {화수}
   - 문제: {진단}
   - 보상 계획: {어떤 사건으로 해소할지}
   - target: plot/{arc}.md {화수 범위}
   - latest-safe-resolution: {최대 몇 화까지 해결해야 하는지}
   - status: open
   ```
2. **`summaries/running-context.md`** (경고): "## HOLD 경고" 섹션에 한 줄 추가
3. **`plot/arc-{NN}.md`** (삽입): 해당 화수에 `[FORWARD-FIX: HOLD-{NNN}]` 마커 삽입

**만기 관리:**
- `latest-safe-resolution` 설정 상한: **현재 화수 + 10화** 또는 **현재 아크 종료 전** (짧은 쪽 적용)
- 매 화 집필 전, supervisor가 `review-log.md`의 open HOLD를 확인
- `latest-safe-resolution` 화수를 넘기면 자동 승격:
  - `forward-fix` → `plot-repair` 또는 `user-escalation`
- `blocker=yes`인 HOLD가 있으면 해당 아크 집필을 중단
- blocker 기준: `retro-fix`/`plot-repair` = blocker:yes, `forward-fix` = blocker:no, `user-escalation` = blocker:yes

**완료 게이트:**
- HOLD가 해소되면 `status: resolved` + 아래 3곳 동기화:
  1. `review-log.md`: status → resolved, 해소 화수/방법 기록
  2. `running-context.md`: HOLD 경고 행 제거
  3. `plot/arc-{NN}.md`: 마커에 `[RESOLVED: {N}화]` 태그 추가 (삭제가 아니라 이력 보존)
- 아크 마감(F단계) 게이트:
  - `scope: current-arc`인 open HOLD → **F 완료 불가** (해결 필수)
  - `scope: next-arc`인 open HOLD → **이관 확인(carry-forward) 후 F 통과 가능** (다음 아크에서 해결)

**forward-fix scope:**
- forward-fix 기록 시 `scope: current-arc | next-arc` 필드 필수
- `scope: next-arc`는 F단계에서 carry-forward로 처리 — 다음 아크 A단계에서 재확인

---

#### 5c. Periodic Check (Hybrid: Review 세션 위임)

> **Hybrid**: 정기 점검은 Codex writer 세션에 보내지 않는다. 그러나 메인 supervisor가 직접 수행하는 것도 금지한다.
> 정기 점검은 반드시 review 세션 Claude에게 지시해서 수행한다.

Trigger: 5화 단위 기본 (settings/07-periodic.md에 따라 조정).

Supervisor가 할 일:
1. review 세션에 periodic 프롬프트 전송 (`tmux-send-claude` 기본)
2. `PERIODIC_DONE {start}-{end}` sentinel 대기
3. 산출물과 action-log 확인

Review 세션이 수행:
1. `settings/07-periodic.md`의 periodic 점검 항목
2. 외부 AI 일괄 리뷰(프로젝트가 활성화한 경우만)
3. Claude 전용 checker 및 관련 MCP 점검

After the periodic check, supervisor continues with next episode prompt to Codex writer.

> **주의**: `/pov-era-check`, `/narrative-fix` 등은 Claude 커맨드이므로 **Codex writer 세션에 보내지 않는다**. 그러나 메인 supervisor가 직접 실행하는 것도 금지한다. 항상 review 세션으로 보낸다.

#### 5d. Session Crash Recovery

If the session has completely disappeared:

1. Check session existence with `tmux ls`
2. If missing, recreate session (Section 1 session management procedure)
3. Check last completed episode in `batch-progress.log`
4. Resume from next episode with full prompt

#### 5e. Skipping Already-Completed Episodes

Before starting, read `summaries/batch-progress.log` and build a list of completed episodes.
Skip already-completed episodes. For episodes where the chapter file exists but is not in the log, verify before deciding.

### 6. Log Management

The supervisor outputs progress in this format:

```
[HH:MM] Ep {N} prompt sent (chunk start)
[HH:MM] Ep {N} working (2m)
[HH:MM] Ep {N} working (4m)
[HH:MM] Ep {N} completed -> proceeding to next
[HH:MM] Ep {N} error detected: {error summary} -> attempting recovery
[HH:MM] /clear performed (chunk boundary)
[HH:MM] Arc transition: {prev arc} -> {new arc}
[HH:MM] Periodic check instructed (per 07-periodic.md trigger)
[HH:MM] Plot generation instructed: plot/{arc}.md
```

### 7. Termination Conditions

- Supervision ends when all episodes through `END_EP` are completed
- **On final completion** (last episode of the novel), run the full verification pipeline:

  **Phase A: 독립 분석 (병렬 가능)**
  1. `/why-check full` — entire novel, long-range gap detection
  2. `/book-review` — independent reader evaluation

  **Phase B: 통합 진단**
  3. `/narrative-review` — full narrative quality analysis. Phase 4 automatically references why-check-report, book-review if they exist.

  **Phase C: 서사 수정**
  4. `/narrative-fix` — apply fix guide items from narrative-review (S1~S6)

  **Phase D: 수정 후 재검증**
  5. `/why-check` delta-check — ④에서 수정된 화수 + 인접 1화만 재검증 (전체 재실행 불필요). 해결된 항목은 resolved, 새로 생긴 문제는 new, 여전한 문제는 still-missing으로 분류.
  6. `/narrative-fix --source why-check` — still-missing 항목만 경량 패치 (E1~E4). **④ 이전의 구 보고서를 쓰지 않는다.**

  **Phase E: 사실 검증**
  7. `/audit` — factual continuity, proper nouns, timeline, worldbuilding rules. Includes Korean naturalness check (Phase 2.5 내장).
  8. `/audit-fix` — audit 결과 기반 오류 수정 (필요 시)

  **Conflict priority** (when reports disagree): factual consistency > explicit contradiction > explanation gap > narrative quality > reader preference.
- Halt and report to user if 3 consecutive unrecoverable errors occur
- If the supervisor's own context is running low, summarize current progress and output a handoff prompt for continuation, then terminate

### 8. Range

Episodes {{START_EP}} through {{END_EP}}.

---

## Supervisor Self-Replacement Prompt

When the supervisor's context is running low, output a handoff prompt in this format:

```
Continue batch supervision.
- Novel: {{NOVEL_ID}}
- Session: {{SESSION}}
- Current progress: ep {N} {state}
- Last completed: ep {M}
- Remaining range: {M+1}~{{END_EP}}
- Notes: {describe if any}
- Follow batch-supervisor.md rules.
```
