# Claude × Codex Hybrid Pipeline Design

## Architecture

```
Claude Code (Supervisor + Reviewer)     Codex / GPT 5.4 (Writer)
────────────────────────────────────     ────────────────────────
runs at /root/novel/                     runs in tmux session
                                         at /root/novel/no-title-XXX/

  compile_brief → 결과 확인
  plot/settings 상태 확인
  review_floor 결정
  집필 프롬프트 생성
       │
       └──── tmux send-keys ────→  프롬프트 수신
                                    파일 직접 읽기 (settings, plot, prev ep)
                                    본문 생성 + 파일 저장
                                    (codex가 자체적으로 파일 read/write)
       ←──── tmux capture-pane ──  완료 확인
       │
  unified-reviewer (Claude)
  external AI review (MCP)
  narrative-fixer (Claude)
  summary update (Claude)
  checkers (Claude)
  git commit (Claude or codex)
```

## Key Insight: tmux Interactive > CLI One-shot

- **연속성**: Codex가 대화 내에서 이전 화 컨텍스트 유지
- **파일 접근**: Codex가 소설 폴더에서 직접 파일 읽기/쓰기 가능
- **기존 패턴 재사용**: Claude→Claude tmux supervision과 동일한 구조
- **새 MCP 도구 불필요**: batch-supervisor.md 프롬프트만 변경

## 변경 범위 (lean 대비)

### 변경 필요
1. **batch-supervisor.md** — `claude` → `codex` 세션 관리, 프롬프트 템플릿 조정
2. **writer.md** → **GPT_WRITER.md** — Codex용 집필 지침 (settings 직접 읽기 방식)
3. **.claude/agents/writer.md** — Claude의 역할을 "집필 지시+검증"으로 축소

### 변경 불필요 (그대로 유지)
- compile_brief.py
- unified-reviewer.md, narrative-fixer.md
- all checkers (oag, why, pov-era, scene-logic, repetition)
- korean-naturalness.md
- CLAUDE.md (소설 헌법)
- settings/, summaries/, plot/

## 세션 구조

### Supervisor (Claude Code)
```bash
# /root/novel/ 에서 실행
claude
```

### Writer (Codex)
```bash
# tmux 세션에서 소설 폴더로 이동 후 실행
tmux new-session -d -s write-001 -x 220 -y 50 -c /root/novel/no-title-001
tmux send-keys -t write-001 'codex' Enter
```

## 프롬프트 설계

### Chunk Start (첫 화 또는 /clear 후)

```
{N}화를 집필해줘.

[지침]
- 이 소설의 집필 헌법: CLAUDE.md를 먼저 읽어라.
- settings/ 폴더의 01-style-guide.md (특히 §0 Voice Profile), 03-characters.md, 04-worldbuilding.md, 05-continuity.md (특히 Continuity Invariants 표)를 읽어라.
- plot/{arc}.md를 확인하여 이번 화의 아크 역할을 파악하라.
- 직전 화(chapters/{arc}/chapter-{NN-1}.md) 마지막 2~3문단을 확인하여 오프닝 연결.
- 본문만 한국어로 출력. EPISODE_META, 요약, 리뷰는 생성하지 마라 — 감독자가 처리.
- 파일명: chapters/{arc}/chapter-{NN}.md

[분량]
- 목표: 4,000~6,000자 (한글, 공백 포함)
- 허용: 3,000~7,000자

[핵심 규칙]
- 시점: 3인칭 제한 시점 ({POV 인물명} 고정)
- 비현대 배경: 외래어/아라비아 숫자 금지 (한자어/한글 수사 사용)
- 전생 비교문: 화당 2회 이하
- 메타 표현 금지: "N화에서", "독자 여러분"
- settings/05-continuity.md의 불변 조건 표를 반드시 대조하라

[자율 실행]
- 질문하지 말고 자율 완료하라.
- 완료 후 대기.
```

### Continuation (이전 화 컨텍스트 유지 중)

```
이어서 {N}화를 집필해줘.
- 직전 화 컨텍스트를 유지하되, plot/{arc}.md를 다시 확인하라.
- 직전 화 마지막 2~3문단에서 오프닝 연결.
- 파일명: chapters/{arc}/chapter-{NN}.md
- 본문만 출력. EPISODE_META 불필요.
- 완료 후 대기.
```

## Supervisor 워크플로우

```
for each episode N:
  1. Claude: compile_brief 실행 → 결과 확인
  2. Claude: review_floor 결정 (§2.5)
  3. Claude: tmux로 codex에 집필 프롬프트 전송
  4. Claude: 주기적으로 tmux capture-pane으로 완료 확인
  5. (완료 후)
     a. Claude: chapter 파일 읽기 → unified-reviewer 실행
     b. Claude: external AI review (MCP)
     c. Claude: 문제 발견 시
        - 연속성/설정 위반 → Claude narrative-fixer가 직접 수정
        - prose 품질 문제 → codex에 부분 재작성 요청 (tmux)
     d. Claude: summary update (직접)
     e. Claude: EPISODE_META 삽입 (직접)
     f. Claude: git commit
  6. 다음 화로
```

## 장점

1. **GPT의 prose 품질** — 전투, 대화, 감정 디테일에서 Claude보다 우수
2. **Claude의 오케스트레이션** — 연속성 관리, 다중 에이전트 검증에서 우수
3. **컨텍스트 연속성** — Codex가 대화 내에서 이전 화 기억
4. **구현 단순성** — 기존 supervisor 패턴 그대로, 새 도구 불필요
5. **비용 효율** — 검증/수정은 Claude (Max 무제한), 집필만 GPT

## 외부 AI 리뷰 변경

GPT가 직접 집필하므로 GPT 피드백은 제거. Claude가 검증 주체로 격상.

| 소스 | lean | hybrid | 이유 |
|------|------|--------|------|
| Claude (unified-reviewer) | 자기 글 자기 리뷰 (약점) | **핵심 검증자** | 다른 모델이 쓴 글 → 교차 검증 효과 |
| Gemini | continuity/worldbuilding | **유지** | 세 번째 시각 |
| NIM | spelling/grammar | **유지** | 맞춤법 전담 |
| GPT (prose/dialogue) | ✅ | **제거** | 자기 글 자기 리뷰 무의미 |
| GPT naturalness | ✅ | **제거** | 동일 모델 |

CLAUDE.md 변경:
```
- gpt_feedback: false    ← hybrid에서는 비활성
- gpt_naturalness: N/A   ← 제거
```

naturalness 검사도 변경:
- Claude korean-naturalness만 실행 (GPT 이중 검사 제거)
- Claude가 GPT 글을 읽으므로 오히려 자연성 검출력이 높아질 수 있음

## MCP → scripts 매핑

Codex는 MCP에 접근할 수 없다. 대신 `scripts/` 폴더의 CLI wrapper로 동일 기능을 사용한다.
소설 프로젝트 초기화 시 `scripts/` 폴더를 소설 폴더에 복사한다.

| MCP 도구 | scripts wrapper | Codex에서 사용법 |
|---------|----------------|-----------------|
| `compile_brief` | `scripts/compile-brief` | `scripts/compile-brief /root/novel/no-title-XXX {N}` |
| `novel-calc` (char_count 등) | `scripts/novel-calc` | `scripts/novel-calc char_count file_path='"path"'` |
| `novel-hanja` | `scripts/novel-hanja` | `scripts/novel-hanja hanja_lookup text='"天外"'` |
| `review_episode` | N/A | Claude supervisor가 담당 |

Codex writer 프롬프트에 포함:
```
- 분량 확인: scripts/novel-calc char_count file_path='"chapters/..."' 로 확인
- 한자 검증: scripts/novel-hanja hanja_lookup text='"한자"' 로 확인
- compile_brief: scripts/compile-brief로 맥락 확인 가능 (supervisor가 미리 호출하는 것이 기본)
```

## 주의점

1. **Codex 상태 감지** — 완료 시 `›` 프롬프트 + `gpt-5.4` 표시. 작업 중 `• Working (Ns)` 표시.
2. **파일 권한** — `--full-auto` 또는 `--dangerously-bypass-approvals-and-sandbox` 사용
3. **EPISODE_META** — Codex가 생성하지 않음 → Claude가 별도 삽입
4. **summary 관리** — Codex가 아닌 Claude가 전담 (compile_brief 정합성)
5. **git** — Claude가 전담 (커밋 메시지 일관성)
6. **Enter 전송** — tmux send-keys 후 1초 대기 후 Enter 별도 전송 필요

## TODO

- [ ] Codex CLI 설치/설정 확인
- [ ] Codex의 tmux 상호작용 패턴 테스트 (프롬프트/완료 감지)
- [ ] GPT_WRITER.md — Codex 전용 집필 프롬프트 작성
- [ ] batch-supervisor.md 수정 — codex 세션 관리
- [ ] writer.md 수정 — Claude의 역할을 "지시+검증"으로
- [ ] 001-hybrid 테스트 소설로 프롤로그 테스트
