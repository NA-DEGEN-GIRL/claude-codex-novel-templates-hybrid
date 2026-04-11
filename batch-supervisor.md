# Batch Writing Supervisor Prompt (Hybrid)

Claude Code periodically checks a tmux session and automatically supervises a writer instance's novel writing. Two modes supported:

- **codex mode** (`writer_model: codex`): Codex/GPT writes, Claude reviews/fixes/manages. (기존 hybrid)
- **claude mode** (`writer_model: claude`): Claude writes (별도 tmux), Claude reviews/fixes/manages. (writer/reviewer 컨텍스트 분리 유지)

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
- **Writer**: Inside a tmux session, navigate to the novel folder (`no-title-XXX/`) and run `{{WRITER_CMD}}`.
  - Writer가 소설 폴더의 설정 파일을 직접 읽고 본문을 생성한다. 리뷰/summary/commit은 supervisor가 처리.

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
| `CHUNK_SIZE` | Manual context-reset interval (in episodes). **`-1` = auto-compact only** | `10` or `-1` |
| `WRITER_CMD` | Writer launch command | `codex --dangerously-bypass-approvals-and-sandbox` |
| `ARC_MAP` | Arc-to-episode mapping | See below |
| `RUN_NONCE` | Per-prompt unique sentinel token minted by supervisor | `20260407-ep05-a1c9` |

**Context 운영 원칙**:
- 기본 권장은 `CHUNK_SIZE = -1`. 모델의 auto-compact를 우선 사용한다.
- `CHUNK_SIZE > 0` 또는 수동 `/clear`는 반복, 맥락 누수, 세션 꼬임이 실제로 보일 때만 예외적으로 사용한다.
- 로컬 모델이라도 auto-compact가 안정적이면 `/clear`를 습관적으로 강제하지 않는다.

### WRITER_CMD Examples

| Value | Description |
|-------|-------------|
| `codex --dangerously-bypass-approvals-and-sandbox` | **codex mode default**: GPT 5.4 writer, 승인 프롬프트 없이 파일 읽기/쓰기 |
| `claude` | **claude mode default**: Claude Code writer (별도 tmux, writer 전용) |
| `claude --model claude-sonnet-4-6` | claude mode: 특정 모델 지정 |

### Mode-Dependent Defaults

| Setting | codex mode | claude mode |
|---------|-----------|-------------|
| WRITER_CMD | `codex --dangerously-bypass-approvals-and-sandbox` | `claude` |
| Writer send script | `tmux-send-codex` | `tmux-send-claude` |
| Writer role prompt | `.claude/prompts/codex-writer-role.md` | `.claude/prompts/claude-writer-role.md` |
| Writer prompt template | `.claude/prompts/codex-writer.md` | `.claude/prompts/claude-writer.md` |
| Fixer prompt template | `.claude/prompts/codex-fixer.md` | `.claude/prompts/claude-fixer.md` |
| tmux send sleep | 3 sec (Codex Enter quirk) | 0.3 sec (standard) |
| Writer session prefix | — | `unset CLAUDECODE &&` (nested Claude 방지) |
| gpt_feedback 권장값 | false | true |
| Completion sentinel | `WRITER_DONE ... :: run={RUN_NONCE}` | `WRITER_DONE ... :: run={RUN_NONCE}` |
| Fix sentinel | `FIX_DONE ... :: run={RUN_NONCE}` | `FIX_DONE ... :: run={RUN_NONCE}` |

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
- context 관리는 기본적으로 writer의 자동 compact에 맡긴다. 세션을 습관적으로 `/clear`하지 않는다.

**Writer 세션** (Codex 또는 Claude — `writer_model`에 따름 — 집필 + 수정):
- tmux session name: `{{SESSION}}` (예: `write-001`)
- **If session doesn't exist**: Create with `tmux new-session -d -s {{SESSION}} -x 220 -y 50 -c {{NOVEL_DIR}}`, then launch `{{WRITER_CMD}}`
  - claude mode일 때: `unset CLAUDECODE && {{WRITER_CMD}}` (nested Claude 방지)
- **If session exists**: Capture the screen to assess current state and continue
- Writer가 집필과 fix-spec 수정을 모두 같은 세션에서 수행 (writer = fixer).
- Writer 프롬프트 전송: codex mode → `tmux-send-codex`, claude mode → `tmux-send-claude`.
- writer 장문 프롬프트는 pane에 직접 paste하지 말고 `tmp/run-prompts/*.txt`에 저장한 뒤, 세션에는 `그 파일을 읽고 그대로 수행해` 같은 짧은 pointer prompt만 보내는 것을 기본값으로 삼는다.

**Review 세션** (Claude Code — 리뷰/검증/후처리):
- tmux session name: `{{SESSION}}-review` (예: `write-001-review`)
- `tmux new-session -d -s {{SESSION}}-review -x 220 -y 50 -c {{NOVEL_DIR}}` → `unset CLAUDECODE && claude` 실행
- unified-reviewer, external AI review(MCP), summary 갱신, EPISODE_META 삽입, git commit 수행.
- supervisor가 review 세션에 post-write 지시를 전송한다.
- **Session size**: Must be 220x50 or larger
- **완료 sentinel 강제**:
  - 화별 post-write 완료 후: `REVIEW_DONE chapter-{NN} :: run={RUN_NONCE}`
  - fix 재검증 완료 후: `RECHECK_DONE chapter-{NN} :: run={RUN_NONCE}`
  - 아크 경계 패키지 완료 후: `ARC_DONE {arc} :: run={RUN_NONCE}`
- review 세션 프롬프트도 기본적으로 `tmp/run-prompts/*.txt`에 장문을 저장하고, `bash {{NOVEL_DIR}}/scripts/tmux-send-claude {{SESSION}}-review '...' 2 80` 또는 codex mode일 때 `tmux-send-codex`로 짧은 pointer prompt만 보낸다.

> **3세션 필수**: supervisor는 tmux 관리에 집중하고, 리뷰/후처리는 반드시 Review 세션에서 수행한다. context 분리로 안정적 운영을 보장.

> **화별 사이클은 직렬이다**: 한 화의 전체 사이클(Writer 집필 → Review 리뷰/fix → summary → META → REVIEW_DONE)이 완료된 후에만 다음 화 Writer 프롬프트를 전송한다. Writer와 Review를 병렬로 돌리지 않는다.

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
if N is first episode of a new arc       → review_floor = full
elif N is last episode of current arc    → review_floor = standard + arc transition package
elif periodic_due (settings/07-periodic) → review_floor = standard
    # 기본 7화 간격, 최대 8화. 조기 drift trigger 시 앞당김 가능.
    # N % 5 == 0 고정 주기 아님. 07-periodic.md Trigger 섹션 참조.
else                                     → review_floor = continuity
```

**Risk-axis override**: `CLAUDE.md` Project Overview의 `prose_risk` 또는 `emotion_risk`가 `high`이면, 새 아크 첫 3화와 감정 전환 화수는 `continuity`가 기본이어도 최소 `standard` 후보로 검토한다. 이 필드는 override 근거이지 writer prompt에 직접 넣는 규칙이 아니다.

**Open HOLD preflight**: 각 화 집필 프롬프트를 보내기 전에 `python3 {{NOVEL_DIR}}/scripts/check-open-holds.py --novel-dir {{NOVEL_DIR}} --current-episode {N} --fail-on-blocker`를 실행한다.
- blocker HOLD가 있으면 현재 화 집필을 멈추고 사용자 또는 plot repair 경로로 보낸다.
- overdue HOLD는 경고를 action-log와 running-context에 반영하고, 같은 화에서 자연 해소 불가능하면 `plot-repair` 또는 `user-escalation` 재분류를 검토한다.

**Specialist trigger determination** (continuity review 완료 후):

```
# 1. plot에서 risk tag 읽기 (writer brief에는 포함하지 않음)
# 형식: plot 파일 에피소드 항목에 "- risk: oag, why" (쉼표 구분)
# 대상 파일: plot/{arc}.md (arc-01, prologue, epilogue, interlude 등 ARC_MAP의 arc명에 대응)
# 허용 값: oag | why | pov-era | scene-logic (이 4개만. repetition은 제외)
# 필드 없으면 empty set. 필드가 optional이므로 대부분 화에는 없음.
risk_tags = extract "risk:" field from plot/{arc}.md for episode N

# 2. continuity review 출력에서 ESCALATE_* flag 읽기
# "Specialist Escalation" 섹션이 없으면 empty set
escalation_flags = extract ESCALATE_* from continuity review output

# 3. 판정
for each specialist in [oag, why, pov_era, scene_logic]:
  if tag AND flag   → 즉시 review 세션에 specialist 실행 지시
  elif flag only    → 실행 (emergent risk)
  elif tag only     → watch 등록 (review-log.md에 "WATCH {specialist}: {tag 근거}" 1줄 append). 본문 증거가 붙거나 periodic due 시 승격
  else              → skip
```

> repetition은 plot risk tag 대상이 아님. periodic/watchlist 트리거만 사용.
> 이미 열린 forward-fix/HOLD와 같은 리스크면 중복 finding으로 찍지 않고 기존 항목에 연결.

**Prose drift override**: 아래 중 하나라도 보이면 해당 화의 review_floor를 최소 `standard`로 올린다.
- 첫 문단이나 장면 전환 첫 문장이 지나치게 문학적 압축에 기대어 뜻을 한 번 더 해석하게 만듦
- 분위기는 있으나 한국어 결합이 어색한 문장(주어-서술어, 명사-동사, 추상명사-행위 결합)이 눈에 띔
- review 세션이 "보이스일 수 있음"과 "어색한 한국어" 사이에서 애매하다고 판단함

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

**Hybrid**: `review_floor`은 Writer 프롬프트에 넣지 않는다. supervisor가 3b-post에서 직접 해당 모드로 unified-reviewer를 실행한다.

**Arc boundary detection**: Check ARC_MAP:
- **First episode** of any arc → `full` (보이스/설정/톤 진입 제어)
- **Last episode** of any arc → `standard` + arc transition package (why-check + 요약 리셋)
- Both checks apply to prologue, all arcs, and epilogue.

**Periodic check alignment**: When `review_floor = standard` because `periodic_due` or an early drift trigger fired, also add periodic check instruction to the prompt.

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

#### 3a. Chunk Start Prompt — Writer (first episode or new session)

> **정본**: `writer_model`에 따라 `.claude/prompts/codex-writer.md` 또는 `.claude/prompts/claude-writer.md`의 **Chunk Start Prompt**.
> supervisor가 아래 변수를 채워 tmux로 전송한다. **이 문서에 인라인 복사본을 두지 않는다** — 동기화 드리프트 방지.

**채울 변수**: `{N}`, `{arc}`, `{NN}`, `{MIN}`, `{MAX}`, `{RUN_NONCE}`, `{{NOVEL_DIR}}`

**공통 집필 레이어**: writer는 `settings/01-style-guide.md`, `settings/03-characters.md`, `settings/05-continuity.md`, `settings/07-periodic.md`를 shared authoring layer로 취급한다. 이 문서는 세션 역할과 순서만 정의한다.

**전송 순서**:
1. writer_model에 맞는 writer prompt 파일의 Chunk Start 코드 블록을 읽는다
2. 변수를 치환한다
3. 장문 prompt는 먼저 `tmp/run-prompts/*.txt`에 저장한다.
4. writer_model에 맞는 send helper를 사용한다. codex mode는 `bash {{NOVEL_DIR}}/scripts/tmux-send-codex {{SESSION}} "\`{{NOVEL_DIR}}/tmp/run-prompts/ep-{NN}-writer.txt\`를 읽고 그대로 수행해. sentinel은 파일에 적힌 exact 문자열만 마지막 줄에 출력해." 2 60`, claude mode는 `bash {{NOVEL_DIR}}/scripts/tmux-send-claude {{SESSION}} "\`{{NOVEL_DIR}}/tmp/run-prompts/ep-{NN}-writer.txt\`를 읽고 그대로 수행해. sentinel은 파일에 적힌 exact 문자열만 마지막 줄에 출력해." 2 80`을 기본으로 쓴다.
5. **send helper 성공 신호를 먼저 확인한다.** `WORKING_CONFIRMED*`, `RESPONSE_CONFIRMED*`, `PROMPT_DISAPPEARED*` 중 하나가 나와야 "전송 성공"으로 본다.
6. 그 다음에만 `bash {{NOVEL_DIR}}/scripts/tmux-wait-sentinel {{SESSION}} "WRITER_DONE chapter-{NN}.md :: run={RUN_NONCE}" 420 2 500 0 "{{NOVEL_DIR}}/tmp/sentinels/chapter-{NN}.done"`로 들어간다.
   - 장시간 고정 `sleep`으로 먼저 기다리지 않는다.
   - `tmux capture-pane` 수동 확인은 **send helper가 `NO_START_SIGNAL`을 낸 경우**와 **sentinel timeout 이후 fallback**에서만 쓴다.
   - **중요**: `tmux-wait-sentinel` 대기에 들어갔다고 해서 writer가 시작된 것은 아니다. 시작 확인은 send helper가 담당한다.
   - writer는 chapter 저장 후 exact sentinel을 `tmp/sentinels/chapter-{NN}.done`에도 남긴다. pane delta와 sentinel file 둘 다 fallback으로 사용한다.

#### 3b. Continuation Prompt — Writer (previous episode context loaded)

> **정본**: `writer_model`에 따라 `.claude/prompts/codex-writer.md` 또는 `.claude/prompts/claude-writer.md`의 **Continuation Prompt**.
> 변수 치환 + §3d 전송 프로토콜 동일.

**채울 변수**: `{N}`, `{arc}`, `{NN}`, `{RUN_NONCE}`, `{{NOVEL_DIR}}`

#### 3b-post. Supervisor Post-Write Pipeline (Writer 완료 후 Claude가 수행)

> Writer가 `WRITER_DONE`을 출력하면, supervisor(Claude Code)가 아래를 순서대로 수행한다.

1. **chapter 파일 확인**: `ls {{NOVEL_DIR}}/chapters/{arc}/chapter-{NN}.md`
2. **review 세션으로 post-write 지시 전송**: 기본은 `tmux-send-claude`로 보낸다. 아래 작업을 review 세션이 수행하게 한다.
3. **외부 AI 리뷰**: `review_episode` MCP 호출 (sources="auto") — review 세션 수행
4. **unified-reviewer**: review_floor에 맞는 모드로 실행. EDITOR_FEEDBACK 반영 — review 세션 수행
   - narration opening, scene-transition first line, paragraph-ending sentence 중 하나라도 어색한 결합이 의심되면 현재 화에 한해 `/naturalness {N}`를 추가 실행하고 결과를 fix routing에 합친다.
5. **문제 발견 시 — fix routing**:
   a. 모든 발견 항목을 **patch_class**로 분류:
      - `micro`: 사실관계 1-3문장 → **Writer fixer**
      - `local`: 문단 내 수정 → **Writer fixer**
      - `rewrite`: 장면 수준 재작성 → **Writer fixer**
      - `hold`: 구조 변경 필요 → **HOLD Transfer Routing** (아래 §5g 참조)
   b. `micro`/`local`/`rewrite` 항목을 에피소드 단위로 번들: Claude가 `tmp/fix-specs/chapter-{NN}.md` 생성
   c. Writer 세션에 전송 (writer = fixer, 같은 세션):
      ```
      tmp/fix-specs/chapter-{NN}.md 를 읽고 해당 에피소드를 수정해줘.
      fix-spec의 수정 목표와 제약만 따른다. 범위 밖 변경 금지.
      완료 후: FIX_DONE chapter-{NN} :: run={RUN_NONCE}
      ```
   e. `FIX_DONE chapter-{NN} :: run={RUN_NONCE}` 확인 후 Claude가 수정 결과 검증 (unified-reviewer continuity 모드)
   f. **재수정 상한**: Writer fixer 호출은 **1회 한정**. 재검증에서 추가 문제 발견 시 다음 정기 점검으로 이관. 무한 ping-pong 금지.
   g. **resolution_threshold**:
      - `resolved`: 재검증에서 `❌` 0건 + `HIGH` 0건
      - `accepted_with_residuals`: `❌`는 사라졌고 `medium/low`만 남음 → action-log에 residual 기록 후 진행
      - `escalate_hold`: `hold` 항목이 남았거나, 같은 결함이 1회 수정 후에도 반복되거나, `HIGH` 2건 이상 잔존 → 두 번째 fixer 호출 금지. 즉시 `hold_route` 분류
6. **summary 갱신** — review 세션 수행. 아래 Required는 매화 갱신, Conditional+Logged는 해당 시에만 갱신하되 **판단 기록(updated/skipped)은 필수**.
   - **Required**: `running-context.md`, `episode-log.md`, `character-tracker.md`
     - `running-context.md`에는 반드시 `Immediate Carry-Forward` 또는 `직전 화 직결 상태` 섹션을 유지한다. 3~7개 bullet로 현재 위치/시간, 부상·자원 상태, 공개 정보와 비공개 정보, 이미 처리된 일과 아직 안 된 일을 기록한다.
   - **Conditional+Logged** (각 항목마다 action-log에 `{파일}: updated N건` 또는 `{파일}: skipped (사유)` 기록):
     - `dialogue-log.md`: 주요 캐릭터 대사 있으면 role-only 행 기록. 앵커 이탈 시 이탈 행. 대사 없으면 skipped.
     - `foreshadowing.md`: 복선의 설치/암시/해소가 있을 때. 없으면 skipped.
     - `promise-tracker.md`: 약속/복선의 설치/진행/해소가 있을 때. 없으면 skipped.
     - `knowledge-map.md`: 캐릭터가 새 정보를 획득/전달/오해할 때, 또는 보고/경고/허락/소문/비밀 공유가 실제로 성립했거나 불발되어 다음 화 오프닝에 영향을 줄 때. 없으면 skipped.
     - `relationship-log.md`: 첫 만남, 관계 변화, 호칭 변경이 있을 때. 없으면 skipped.
     - `decision-log.md`: 프로젝트 수준 규칙 이탈이 있을 때. 없으면 skipped.
     - `desire-state.md`: 독자가 기다리는 것/불안해하는 것/이번 화에서 건드릴 것이 변했을 때. 없으면 skipped.
     - `signature-moves.md`: 잘 먹힌 장면 운용 패턴 또는 과사용 패턴을 올릴 가치가 있을 때. 없으면 skipped.
     - `term-onboarding.md` (해당 프로젝트에 존재 시): 새 용어의 첫 등장/설명이 있을 때. 없으면 skipped.
     - `hanja-glossary.md` (한자 사용 프로젝트만): 한글(漢字) 첫 표기가 있을 때. 없으면 skipped.
     - `style-lexicon.md`: 어휘 치환이 채택됐을 때. 없으면 skipped.
   - **`REVIEW_DONE` 게이트**: Required 3종 갱신 완료 + Conditional+Logged 전 항목의 updated/skipped 기록이 action-log에 있어야 한다. `python3 {{NOVEL_DIR}}/scripts/verify-review-done.py --novel-dir {{NOVEL_DIR}} --episode {N}`가 통과하지 않으면 REVIEW_DONE 불가.
7. **summary fact-check**: 본문 ↔ 요약 대조 — review 세션 수행
8. **EPISODE_META 삽입**: chapter 파일 끝에 append — review 세션 수행
9. **action-log 갱신** — review 세션 수행
10. **git add + REVIEW_DONE helper**: review 세션이 chapter + summaries + EDITOR_FEEDBACK를 stage한 뒤 `python3 {{NOVEL_DIR}}/scripts/verify-review-done.py --novel-dir {{NOVEL_DIR}} --episode {N}`를 실행한다. 실패 시 commit 금지.
11. **git commit**: helper 통과 후에만 수행 — review 세션 수행
12. **완료 신호 출력**: review 세션은 마지막 줄에 반드시 `REVIEW_DONE chapter-{NN} :: run={RUN_NONCE}` 출력
13. **review 세션 context reset** (선택): `REVIEW_DONE chapter-{NN} :: run={RUN_NONCE}` 후 review 세션의 auto-compact가 불안정하거나 컨텍스트 오염이 확인될 때만 `/clear`를 전송한다. 기본값은 auto-compact 우선.
14. **config.json 업데이트**: `REVIEW_DONE chapter-{NN} :: run={RUN_NONCE}` 확인 후 supervisor가 직접 수행

#### 3c. Plot Generation Prompt (when the arc's plot file doesn't exist)

```
{arc}의 플롯 파일이 없다. plot/{arc}.md를 먼저 작성해줘.
- plot/master-outline.md와 plot/foreshadowing.md를 참조한다.
- 이전 아크의 plot 파일 형식을 따른다.
- 완료 후 {N}화 집필을 이어서 진행한다.
```

#### 3d. Command Send Protocol (Important)

Do not rely on a single long paste into the pane. `Enter` may occasionally fail to register, leaving the command text pasted but not executed.

**기본 원칙**:
- 장문 writer/review/fix prompt는 `tmp/run-prompts/*.txt`에 저장한다.
- 세션에는 그 파일을 읽고 수행하라고 지시하는 **짧은 pointer prompt**만 전송한다.
- codex mode에서는 `tmux-send-codex`가 pointer prompt 제출 뒤 입력창에 텍스트가 남아 있으면 3초 간격으로 최대 4회까지 `Enter`를 더 보낸다.

Always send commands in this order:

```bash
tmux send-keys -t {{SESSION}} -l 'short pointer prompt'
sleep 3          # Codex: 즉시 Enter = 줄바꿈, 3초 후 Enter = 메시지 전송
tmux send-keys -t {{SESSION}} Enter
```

> **Codex 특이사항**: 텍스트 입력 직후 Enter를 누르면 줄바꿈만 된다. 3초 이상 대기 후 Enter를 눌러야 메시지가 전송된다. 긴 프롬프트는 `sleep 5`도 고려.
>
> **Claude mode**: `sleep 0.3`이면 충분하다. Claude Code는 Codex와 달리 즉시 Enter가 전송을 트리거하므로 긴 대기가 불필요하다.

**Codex 전용 권장 방식**:

```bash
bash {{NOVEL_DIR}}/scripts/tmux-send-codex {{SESSION}} "\`{{NOVEL_DIR}}/tmp/run-prompts/ep-{NN}-writer.txt\`를 읽고 그대로 수행해. sentinel은 파일에 적힌 exact 문자열만 마지막 줄에 출력해." 2 60
```

이 명령이 `WORKING_CONFIRMED*`, `RESPONSE_CONFIRMED*`, `PROMPT_DISAPPEARED*` 중 하나를 반환해야만 "프롬프트가 실제 제출되었다"고 본다. `NO_START_SIGNAL`이면 아직 시작되지 않은 것으로 본다.

Then verify shortly after sending:

```bash
sleep 2
tmux capture-pane -t {{SESSION}} -p -S -20
```

Interpretation:

- **Started correctly**: Codex — `Working`이 보이거나 새 응답 블록(`• ...`)이 붙는다. Claude — `⏺` 스피너 또는 `Reading`/`Editing` 등 진행 표시가 보인다
- **Enter likely failed**: 진행 표시가 2초 안에 보이지 않는다

> **금지 오판**: `WRITER_DONE ...` sentinel을 기다리기 시작했다는 이유만으로 "Writer가 작업을 시작했다"라고 말하지 않는다. sentinel wait는 완료 감시일 뿐이고, 시작 여부는 send helper 결과와 pane 하단 prompt 상태로 판정한다.

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
- Codex tmux 전송 확인은 `Working` 또는 새 응답 블록만 기준으로 본다. `Explored`, `Edited`, `Ran`은 화면 윗부분의 이전 작업 로그일 수 있다. Claude는 `⏺` 스피너 출현으로 판단한다.
- `NO_START_SIGNAL` 또는 `NO_CLAUDE_START_SIGNAL` 이후에는 pane 전체가 아니라 **마지막 입력 프롬프트 줄이 현재 pane 바닥에 실제로 남아 있는지**를 먼저 본다. 오래된 prompt echo만 남아 있으면 추가 Enter를 보내지 않는다.
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
| **Working** | Codex: `• Working (Ns)`, `• Explored`, `• Edited`, `• Ran` 등 진행 표시. Claude: `⏺` 스피너, `Reading`, `Editing`, `Running` 등 진행 표시 | Re-check after 2 minutes |
| **Completed (WRITER_DONE)** | `WRITER_DONE chapter-{NN}.md :: run={RUN_NONCE}` 출력 + 프롬프트 대기 (Codex: `›`, Claude: `>`) | **Post-write pipeline (3b-post) 시작** |
| **Prompt ready without sentinel** | Codex: `›` 프롬프트 + `gpt-5.4` 표시. Claude: `>` 프롬프트 (`WRITER_DONE ... :: run=...` 없이) | **완료로 즉시 간주하지 않는다.** timeout 이후 fallback 점검 대상으로만 본다 |
| **Trust prompt** | `Do you trust the contents` + `Press enter to continue` (Codex 전용) | Enter 전송 |
| **Error occurred** | `Error`, `FATAL`, `Permission denied` etc. | 분석 후 복구 |
| **Infinite loop** | 같은 파일 반복 편집, 10분+ 진전 없음 | Esc로 중단 후 재지시 |
| **Abnormal exit** | writer 종료, bash `$` 프롬프트만 표시 | `{{WRITER_CMD}}` 재시작 |

#### 4c. Completion Verification

To accurately determine "completed" state, verify all of the following:

1. **WRITER_DONE sentinel**: send 직후 곧바로 `bash {{NOVEL_DIR}}/scripts/tmux-wait-sentinel {{SESSION}} "WRITER_DONE chapter-{NN}.md :: run={RUN_NONCE}" 420 2 500 0 "{{NOVEL_DIR}}/tmp/sentinels/chapter-{NN}.done"`으로 감시한다.
   - 전제 조건: 직전에 사용한 send helper가 성공 신호를 반환했어야 한다.
   - `NO_START_SIGNAL` 직후 곧바로 sentinel wait만 걸고 "시작됨"으로 간주하면 안 된다.
   - 이 단계가 기본 경로다. 중간에 `sleep 300 && tmux capture-pane ...` 같은 장시간 대기는 넣지 않는다.
   - timeout일 때만 `tmux capture-pane` + `›` 프롬프트 + chapter 파일 + sentinel file 존재를 함께 확인한다.
2. **Work artifact exists**: Chapter file exists (`ls {{NOVEL_DIR}}/chapters/{arc}/chapter-{NN}.md`)
3. **Progress log 기록**: supervisor가 직접 `echo "EP {N} DONE $(date +%H:%M)" >> {{NOVEL_DIR}}/summaries/batch-progress.log` 실행.

> **batch-progress.log 관리**: supervisor가 3b-post 완료(commit까지 끝난 후)마다 기록한다. Writer가 아닌 supervisor의 책임.

All conditions met → 3b-post(review + fix + summary + META) 진행. 파일 없으면 Writer 재지시.

> **화별 사이클은 반드시 직렬이다.** 다음 화 Writer 프롬프트는 현재 화의 `REVIEW_DONE chapter-{NN} :: run={RUN_NONCE}` 확인 이후에만 전송한다. Writer와 Review를 병렬로 돌리면 fix 결과가 반영되지 않은 채 다음 화가 진행될 수 있다.
`›` 프롬프트만 보였다는 이유로는 완료 처리하지 않는다. sentinel 없이 prompt ready면 fallback 조사 후에만 post-write로 넘어간다.

#### 4c-2. Review Session Completion Verification

review 세션도 writer와 마찬가지로 sentinel 기반으로 완료를 판정한다.

- 화별 post-write: `bash {{NOVEL_DIR}}/scripts/tmux-wait-sentinel {{SESSION}}-review "REVIEW_DONE chapter-{NN} :: run={RUN_NONCE}" 300 2 200 1`
- fix 재검증: `bash {{NOVEL_DIR}}/scripts/tmux-wait-sentinel {{SESSION}}-review "RECHECK_DONE chapter-{NN} :: run={RUN_NONCE}" 300 2 200 1`
- 아크 경계 패키지: `bash {{NOVEL_DIR}}/scripts/tmux-wait-sentinel {{SESSION}}-review "ARC_DONE {arc} :: run={RUN_NONCE}" 3600 3 260 1`

> **ALLOW_EXISTING=1 필수**: review/recheck/arc sentinel은 supervisor가 wait 명령을 실행하기 전에 이미 출력됐을 수 있다. 마지막 인자 `1`을 빠뜨리면 이미 완료된 sentinel을 놓치고 false timeout에 빠진다.

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

> **When to use CHUNK_SIZE = -1 (recommended)**: auto-compact가 안정적으로 작동하는 모델. 기본값.
> **When to use CHUNK_SIZE = 1**: auto-compact가 실제로 실패하거나, 화별 강제 리셋이 더 안정적이라는 근거가 있을 때만.
> **When to use CHUNK_SIZE > 0**: auto-compact가 약하거나 컨텍스트 창이 작아 주기적 리셋이 필요한 모델.

#### 5b. Arc Transition (Review 세션에 지시)

> **3세션 원칙 유지**: 아크 전환 A~F도 supervisor가 직접 실행하지 않고 **review 세션에 지시**한다.
> `/oag-check`, `/why-check`, `/narrative-fix` 등은 review 세션의 Claude가 실행한다.
> 텍스트 수정이 필요하면: review 세션이 fix-spec 생성 → Writer 세션에서 수정 (fix routing 적용).

When the episode number enters a new arc range:

1. Confirm completion of the last episode of the previous arc
2. **A. OAG 탐지** — review 세션에 `/oag-check` 지시:
   - `.claude/agents/oag-checker.md` Text Mode
   - 대상: {start}~{end}화
   - 산출물: `summaries/oag-report.md`
   - `plot-change-needed` → review 세션이 `/plot-repair` 실행 (supervisor 판단 후 지시)
   - `patch-feasible` → review 세션이 fix-spec 생성 → Writer 세션 수정
3. **B. 본문 패치** — fix routing 적용 (3b-post 동일)
4. **C. 설명 갭** — review 세션에 `/why-check text` 지시
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
     - `patch-feasible: yes` → fix routing → Writer 세션에서 수정
     - wider structural issue → `[HOLD]` + **§5g HOLD Transfer Routing** 수행
5. **D.5. 전문 감사** — review 세션에 지시:
   - `/pov-era-check` + `/scene-logic-check` 병렬
   - 수정: fix routing 적용
6. **D.7. 반복 감사** — review 세션에 지시:
   - `/repetition-check` → HIGH 항목 fix routing
7. **E. 자연스러움** — review 세션에 지시:
   - `/naturalness` (Claude + GPT MCP) → `/naturalness-fix`
8. **E.5. 개발편집** — review 세션에 지시:
   - `/narrative-review` 실행 → 서사 품질 거시 진단 (10기둥 분석)
   - "이 아크가 좋은 소설로 작동하는가" 판정: 주인공 수동화, 스케일 인플레이션, 주제 표류 감지
   - HIGH 이상 항목 → fix routing (Writer 세션)
   - 사용자 판단이 필요한 구조적 제안 → 사용자에게 보고
9. **F. 아크 마감** — review 세션에 지시:
   - Arc summary + character state reset
   - Unresolved thread triage
   - **Voice Profile Freshness handoff**: unified-reviewer full 결과에 `Voice Profile Freshness` 경고가 있으면 `settings/01-style-guide.md` §0.3 대표 문단을 현재 아크의 실제 문단으로 교체하거나, 교체가 애매하면 `review-log.md`에 HOLD로 남기고 다음 아크 첫 화 전에 처리
10. **새 아크 준비** — review 세션에 지시:
    - `plot/{arc}.md` 존재 확인 → 없으면 3c로 생성
    - `/oag-check plan` + `/why-check plan` → review 세션에서 실행
    - 새 아크 컨셉이 장기 연재에서 지속 가능한지 검토 (story-consultant 참조 가능)
    - 정기 점검 트리거: 첫 화 프롬프트에 `※ 아크 전환 시점` 포함

#### 5g. HOLD Transfer Routing

> `patch_class = hold` 항목은 단순 fix-spec으로 해결 불가. supervisor가 즉시 `hold_route`를 분류한다.

**분류 기준:**

| hold_route | 조건 | 행동 |
|------------|------|------|
| `retro-fix` | 이미 쓴 장면이 **사실적으로 거짓**이 됨 (독자가 이미 읽은 내용과 충돌) | 해당 화 수정 — Writer fixer (rewrite급 fix-spec) |
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
3. **`plot/{arc}.md`** (삽입): 해당 화수에 `[FORWARD-FIX: HOLD-{NNN}]` 마커 삽입

**만기 관리:**
- `latest-safe-resolution` 설정 상한: **현재 화수 + 10화** 또는 **현재 아크 종료 전** (짧은 쪽 적용)
- 매 화 집필 전, supervisor가 `python3 {{NOVEL_DIR}}/scripts/check-open-holds.py --novel-dir {{NOVEL_DIR}} --current-episode {N}`로 open HOLD를 확인
- `latest-safe-resolution` 화수를 넘기면 자동 승격:
  - `forward-fix` → `plot-repair` 또는 `user-escalation`
- `blocker=yes`인 HOLD가 있으면 해당 아크 집필을 중단
- blocker 기준: `retro-fix`/`plot-repair` = blocker:yes, `forward-fix` = blocker:no, `user-escalation` = blocker:yes

**완료 게이트:**
- HOLD가 해소되면 `status: resolved` + 아래 3곳 동기화:
  1. `review-log.md`: status → resolved, 해소 화수/방법 기록
  2. `running-context.md`: HOLD 경고 행 제거
  3. `plot/{arc}.md`: 마커에 `[RESOLVED: {N}화]` 태그 추가 (삭제가 아니라 이력 보존)
- 아크 마감(F단계) 게이트:
  - `scope: current-arc`인 open HOLD → **F 완료 불가** (해결 필수)
  - `scope: next-arc`인 open HOLD → **이관 확인(carry-forward) 후 F 통과 가능** (다음 아크에서 해결)

**forward-fix scope:**
- forward-fix 기록 시 `scope: current-arc | next-arc` 필드 필수
- `scope: next-arc`는 F단계에서 carry-forward로 처리 — 다음 아크 A단계에서 재확인

---

#### 5c. Periodic Check (Hybrid: Review 세션 위임)

> **Hybrid**: 정기 점검은 Writer 세션에 보내지 않는다. 그러나 메인 supervisor가 직접 수행하는 것도 금지한다.
> 정기 점검은 반드시 review 세션 Claude에게 지시해서 수행한다.

Trigger: 6~8화 단위 (기본 7화 간격, 최대 8화 초과 금지). 조기 drift trigger 시 앞당김 가능. 상세: `settings/07-periodic.md`.

Supervisor가 할 일:
1. review 세션에 periodic 프롬프트 전송 (`tmux-send-claude` 기본)
2. `PERIODIC_DONE {start}-{end}` sentinel 대기
3. 산출물과 action-log 확인

Review 세션이 수행:
1. `settings/07-periodic.md`의 periodic 점검 항목
2. 외부 AI 일괄 리뷰(프로젝트가 활성화한 경우만)
3. Claude 전용 checker 및 관련 MCP 점검

After the periodic check, supervisor continues with next episode prompt to Writer.

> **주의**: `/pov-era-check`, `/narrative-fix` 등은 Claude 커맨드이므로 **Writer 세션에 보내지 않는다** (codex/claude 모두 동일 — writer는 집필 전용). 그러나 메인 supervisor가 직접 실행하는 것도 금지한다. 항상 review 세션으로 보낸다.

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
