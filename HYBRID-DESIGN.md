# Claude × Codex Hybrid Pipeline — 설계 문서

> README.md는 사용자 가이드, 이 문서는 내부 설계 근거와 기술 세부사항.

---

## 설계 결정

### tmux Interactive > CLI One-shot

| 방식 | 장점 | 단점 |
|------|------|------|
| CLI one-shot (`codex exec`) | 단순, 상태 없음 | 매 화 컨텍스트 리셋, 정보 손실 |
| **tmux interactive** | 컨텍스트 유지, 파일 직접 접근, 기존 패턴 재사용 | writer runtime 상태 감지 필요 |

**선택: tmux interactive.** Writer 세션이 이전 화의 문맥을 이어받을 수 있어 연속성이 보존된다.

### 역할 분리 원칙

- **Writer = prose engine**: 본문 생성만. 프로젝트 상태 관리 안 함. (Codex 또는 Claude, `writer_model`에 따름)
- **Claude = stateful orchestrator**: 나머지 전부. compile_brief, review, fix, summary, META, commit.
- **경계**: Writer는 `chapters/` 파일만 생성. `summaries/`, `EPISODE_META`, `.git`은 Claude supervisor 전담.

### Writer Model Modes

| | codex mode | claude mode |
|---|-----------|-------------|
| Writer | Codex (GPT 5.4) | Claude (별도 tmux) |
| Supervisor | Claude | Claude |
| Review | Claude | Claude |
| 핵심 이점 | 교차 모델 검증 (GPT 쓰고 Claude 검증) | Claude 품질 + 역할 분리 유지 |
| 핵심 위험 | GPT 문체 drift | 같은 모델 맹점 공유 |

### 외부 AI 리뷰

리뷰 구조는 writer_model에 따라 달라짐:

| 소스 | codex mode | claude mode | 이유 |
|------|-----------|-------------|------|
| Claude unified-reviewer | **핵심 검증자** | 핵심 검증자 (same-model 경고 적용) | 교차 검증 vs 동일 모델 |
| Gemini (MCP) | **유지** | **유지** | 제3 모델의 시각 |
| NIM (MCP) | **유지** | **유지** | 맞춤법 전담 |
| GPT prose review | **제거** (집필 모델 동일) | **복원** (교차 검증) | 집필 모델과 다른 모델이 리뷰해야 효과 |
| GPT naturalness | **유지** | **유지** | MCP 별도 세션 = writer와 독립 |

> **codex mode 리뷰 체계**: GPT(집필) → Claude(검증) + Gemini(보조) + NIM(교정)
> **claude mode 리뷰 체계**: Claude(집필) → Claude(검증, same-model 경고 적용) + GPT(교차 검증 복원) + Gemini(보조) + NIM(교정)
>
> CLAUDE.md 변경:
> ```
> gpt_feedback: false (prose review만 비활성)
> gpt_naturalness: 유지 (MCP 별도 세션)
> ```

---

## Native MCP 원칙

> 런타임 기본 경로는 **MCP 직접 호출**이다.
> 이 템플릿은 `compile_brief`, `novel-calc`, `novel-hanja`, `novel-naming`용 shell wrapper를 두지 않는다.
> `scripts/`에는 tmux/session helper와 codex mode 편의 런처만 남긴다.

### Codex MCP 설정

```bash
# 글로벌 등록 (한 번만)
codex mcp add novel-calc -- python3 /root/novel/mcp-novel-calc/calc_server.py
codex mcp add novel-hanja -- python3 /root/novel/mcp-novel-hanja/hanja_server.py
codex mcp add novel-naming -- python3 /root/novel/mcp-novel-naming/naming_server.py
codex mcp add novel-editor -- python3 /root/novel/mcp-novel-editor/editor_server.py

# 확인
codex mcp list
```

설정 파일: `~/.codex/config.toml`에 저장됨.

### Writer/Review MCP 분담

| MCP 도구 | Writer | Review (Claude) | 비고 |
|---------|--------|-----------------|------|
| `compile_brief` | ✅ 집필 전 필수 | ✅ 검증용 | 양쪽 다 사용 |
| `char_count` | ✅ 초안 후 필수 | ✅ 재확인 | 이중 안전망 |
| `hanja_lookup` | ✅ 병기 시 | ✅ 보정 | Writer가 못 쓰면 Review 보정 |
| `review_episode` | ❌ | ✅ 전담 | 외부 AI 리뷰는 Review만 |
| `naming_check` | ❌ | ✅ 전담 | periodic/아크 경계 |
| summaries/META/git | ❌ | ✅ 전담 | 메타데이터는 Review만 |

> **이중 안전망**: Writer가 MCP를 쓰면 좋고, 안 써도 Review가 동일 검증을 수행한다. 단, 경로는 항상 native MCP여야 한다.

---

## Writer tmux 상호작용 패턴

### 시작

#### codex mode
```bash
tmux new-session -d -s {{SESSION}} -x 220 -y 50 -c {{NOVEL_DIR}}
tmux send-keys -t {{SESSION}} 'codex --dangerously-bypass-approvals-and-sandbox' Enter
```
- Trust 프롬프트 생략됨 (`--dangerously-bypass-approvals-and-sandbox`)

#### claude mode
```bash
tmux new-session -d -s {{SESSION}} -x 220 -y 50 -c {{NOVEL_DIR}}
tmux send-keys -t {{SESSION}} 'unset CLAUDECODE && claude' Enter
```
- nested Claude 방지를 위해 `unset CLAUDECODE &&` prefix 사용

### 프롬프트 전송

#### codex mode
```bash
tmux send-keys -t {{SESSION}} -l '프롬프트 내용'
sleep 3          # ← 3초 대기 필수! 즉시 Enter = 줄바꿈, 3초 후 Enter = 메시지 전송
tmux send-keys -t {{SESSION}} Enter
```

> **중요**: Codex에서 Enter의 동작이 타이밍에 따라 다르다.
> - 텍스트 입력 직후 Enter → **줄바꿈** (메시지 전송 아님)
> - 3초 이상 대기 후 Enter → **메시지 전송**
> - 따라서 `sleep 3`은 안전한 최소값. 긴 프롬프트는 `sleep 5`도 고려.

#### claude mode
```bash
tmux send-keys -t {{SESSION}} -l '프롬프트 내용'
sleep 1
tmux send-keys -t {{SESSION}} Enter
```

- 실제 운영에서는 `tmux-send-claude` 사용을 기본으로 한다.

### 상태 감지

| 상태 | 패턴 | 조치 |
|------|------|------|
| 작업 중 | Codex: `• Working (Ns)` / Claude: `⏺`, `Reading`, `Editing` | 대기 |
| 완료 | `WRITER_DONE chapter-{NN}.md` + `›` 프롬프트 | Post-write pipeline |
| 완료 (sentinel 없음) | 세션 프롬프트만 보임 | chapter 파일 확인 후 진행 |
| 오류 | `Error`, `Permission denied` | 분석 후 복구 |
| 종료 | bash `$` 프롬프트 | writer runtime 재시작 |

### 완료 후 검증
```bash
# 1. sentinel 확인
tmux capture-pane -t {{SESSION}} -p -S -5 | grep WRITER_DONE

# 2. 파일 존재 확인
ls {{NOVEL_DIR}}/chapters/{arc}/chapter-{NN}.md

# 3. 분량 확인 (supervisor/review가 native MCP로 재확인)
# novel-calc MCP의 char_count 사용
```

---

## 수정 라우팅 (Fix Routing)

> **원칙: Claude는 무엇을 고칠지 결정하고, Writer 세션이 모든 텍스트 수정을 수행한다.**
> 문체 일관성을 위해 micro-patch 포함 모든 텍스트 수정은 같은 writer 세션이 담당한다.

### 수정 프로세스

```
1. Claude fix-spec generator
   - 문제 유형, 위치, 원인
   - 수정 목표 + patch_class (micro/local/rewrite)
   - 반드시 유지할 요소 (톤/리듬/캐릭터)
   - 출력: tmp/fix-specs/chapter-{NN}.md

2. 모든 fix-spec을 에피소드 단위로 번들
   - micro + local + rewrite를 하나의 fix-spec 파일에 통합
   - hold만 제외 (다음 사이클 이관)

3. 같은 Writer 세션(writer=fixer)에 전달
   - fix-spec 기반으로 해당 구간 수정
   - 앞뒤 문맥 유지, 기존 문체/리듬 보존
   - FIX_DONE sentinel 출력

4. Claude 재검증 (unified-reviewer continuity, 1회)
```

> **Claude가 직접 수정하는 유일한 영역**: summaries/, EPISODE_META, action-log — 즉 메타데이터만.

### fix-spec 공통 스키마

모든 checker의 발견을 정규화:

```yaml
source: "why-check"          # checker 출처
target_file: "chapters/arc-01/chapter-18.md"
line_start: 142
line_end: 176
severity: "HIGH"
patch_class: "rewrite"       # micro | local | rewrite | hold
diagnosis: "침묵 선택 이유가 독자에게 전달되지 않음"
rewrite_goal: "행동/지각으로 이유를 드러낸다"
must_keep:
  - "냉정하고 눌린 톤"
  - "엔딩 훅 연결"
must_avoid:
  - "새 설정 추가"
  - "해설적 설명"
```

### 라우팅

```
patch_class = micro   → Writer fixer (1-3문장 사실관계)
patch_class = local   → Writer fixer (문단 내 수정)
patch_class = rewrite → Writer fixer (장면 수준 재작성)
patch_class = hold    → HOLD Transfer Routing (retro-fix / forward-fix / plot-repair / user-escalation)
```

> **모든 텍스트 수정은 Writer 세션이 수행.** Claude는 메타데이터(summaries/META/log)만 직접 수정.

### 운영 방식

- 진단은 배치: 모든 checker를 먼저 돌려 fix-spec들을 수집
- 수정은 번들: 한 화의 모든 fix-spec을 모아 writer 세션에 한 번에 전달
- tmux는 작업 큐 트리거만: 긴 프롬프트 대신 `fix-spec 파일 경로`를 전달
- 집필 세션 = 수정 세션 (writer=fixer, 같은 tmux). 문체 일관성 보장

```
Claude: "tmp/fix-specs/chapter-018.md 를 읽고 수정해줘. 완료 후 FIX_DONE"
Writer: 파일 읽기 → 수정 → FIX_DONE chapter-018
```

---

## Native MCP 체크리스트

새 환경에서 hybrid를 처음 설정할 때:

- [ ] `codex mcp add novel-calc -- python3 /root/novel/mcp-novel-calc/calc_server.py`
- [ ] `codex mcp add novel-hanja -- python3 /root/novel/mcp-novel-hanja/hanja_server.py`
- [ ] `codex mcp add novel-naming -- python3 /root/novel/mcp-novel-naming/naming_server.py`
- [ ] `codex mcp add novel-editor -- python3 /root/novel/mcp-novel-editor/editor_server.py`
- [ ] `codex mcp list`로 4개 enabled 확인
- [ ] 설정 파일 위치: `~/.codex/config.toml`

> Codex 쪽 MCP 등록은 글로벌이므로 한 번만 하면 모든 소설 프로젝트에서 사용 가능.
> `claude mode`를 쓸 때는 Claude Code 쪽에도 동일한 MCP 서버 구성이 필요하다.
> 이 템플릿은 MCP wrapper scripts를 두지 않는다.

---

## 핵심 파일

| 파일 | 역할 | 변경 여부 |
|------|------|----------|
| `.claude/prompts/codex-writer-role.md` | Codex 창작 역할 + 문체 원칙 | **신규** |
| `.claude/prompts/codex-writer.md` | Codex 집필 프롬프트 템플릿 (정본) | **신규** |
| `.claude/prompts/codex-fixer.md` | Codex 수정 프롬프트 템플릿 | **신규** |
| `.claude/prompts/claude-writer-role.md` | Claude 창작 역할 + Session Boundary | **신규** |
| `.claude/prompts/claude-writer.md` | Claude 집필 프롬프트 템플릿 (정본) | **신규** |
| `.claude/prompts/claude-fixer.md` | Claude 수정 프롬프트 템플릿 | **신규** |
| `batch-supervisor.md` | Supervisor 규칙 (hybrid용) | **수정** |
| `scripts/*` | tmux/session helper + codex mode 편의 런처 | 유지 |
| ~~`.claude/agents/writer.md`~~ | 삭제됨. `.claude/prompts/` 하위 writer 파일이 정본 | 삭제 |
| 나머지 agents/commands | 그대로 | 변경 없음 |

---

## Checker → fix-spec 변환 (Supervisor 책임)

각 checker의 출력 형식이 다르므로, supervisor가 fix-spec 공통 스키마로 변환한다.

| Checker 출력 | patch_class 기본값 | 비고 |
|-------------|-------------------|------|
| unified-reviewer ❌ | `micro` (사실관계) 또는 `local` (prose) | 항목 유형으로 판단 |
| oag-checker `patch-feasible` | `local` (A1~A3 전략) | 1-3문장이면 `micro` |
| why-checker `MISSING` | `local` (E1~E4 전략) | |
| why-checker `CGAP/BREAK` | `hold` | 구조 변경 필요 |
| arc-readthrough | `local` (R1~R4) | |
| pov-era-checker ❌ | `micro` (단어 치환) | |
| scene-logic-checker ❌ | `micro` (동작 1문장 추가) | ⚠️면 `local` |
| repetition-checker HIGH | `local` (분산 변주) | |
| korean-naturalness | `local` (표현 교체) | |

> `micro`/`local` 경계: **"정답이 하나"면 micro, "표현 선택이 중요"하면 local.**

---

## 구현 상태

- [x] HYBRID-DESIGN.md 설계
- [x] `.claude/prompts/codex-writer-role.md` 창작 역할 + 문체 원칙
- [x] `.claude/prompts/codex-writer.md` 프롬프트 템플릿 (정본, batch-supervisor에서 참조)
- [x] `.claude/prompts/claude-writer-role.md` 창작 역할 + Session Boundary
- [x] `.claude/prompts/claude-writer.md` 프롬프트 템플릿 (정본, batch-supervisor에서 참조)
- [x] `batch-supervisor.md` hybrid용 수정 (3a/3b/3b-post/상태 판별)
- [x] `scripts/` tmux/session helper 정리
- [x] README.md hybrid용 작성
- [x] Codex tmux 상호작용 테스트 (1화 집필 성공)
- [x] fix-spec 공통 스키마 정의
- [x] Codex fixer 프롬프트 템플릿 (`.claude/prompts/codex-fixer.md`)
- [x] Claude fixer 프롬프트 템플릿 (`.claude/prompts/claude-fixer.md`)
- [x] Supervisor fix routing 로직 (batch-supervisor 3b-post)
- [x] Checker→fix-spec 변환 매핑 테이블
- [ ] 001-hybrid 전체 프롤로그 테스트 (supervisor 자동)
- [ ] 아크 전환 A→F 테스트
