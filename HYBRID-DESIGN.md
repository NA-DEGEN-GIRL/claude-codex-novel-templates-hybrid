# Claude × Codex Hybrid Pipeline — 설계 문서

> README.md는 사용자 가이드, 이 문서는 내부 설계 근거와 기술 세부사항.

---

## 설계 결정

### tmux Interactive > CLI One-shot

| 방식 | 장점 | 단점 |
|------|------|------|
| CLI one-shot (`codex exec`) | 단순, 상태 없음 | 매 화 컨텍스트 리셋, 정보 손실 |
| **tmux interactive** | 컨텍스트 유지, 파일 직접 접근, 기존 패턴 재사용 | Codex 상태 감지 필요 |

**선택: tmux interactive.** Codex가 대화 내에서 이전 화를 기억하므로 연속성이 보존된다.

### 역할 분리 원칙

- **Codex = prose engine**: 본문 생성만. 프로젝트 상태 관리 안 함.
- **Claude = stateful orchestrator**: 나머지 전부. compile_brief, review, fix, summary, META, commit.
- **경계**: Codex는 `chapters/` 파일만 생성. `summaries/`, `EPISODE_META`, `.git`은 Claude 전담.

### 외부 AI 리뷰

GPT가 집필하므로 리뷰 구조가 변경됨:

| 소스 | lean (Claude 집필) | hybrid (Codex 집필) | 이유 |
|------|-------------------|---------------------|------|
| Claude unified-reviewer | 자기 글 자기 리뷰 (약점) | **핵심 검증자** | 교차 검증 효과 |
| Gemini | 유지 | **유지** | 세 번째 시각 |
| NIM | 유지 | **유지** | 맞춤법 전담 |
| GPT prose review | 유지 | **유지** | MCP 별도 세션이므로 교차 검증 유효 |
| GPT naturalness | 유지 | **유지** | 별도 프롬프트+세션, 결합 자연성 특화 |

> GPT 리뷰를 유지하는 이유: 집필 Codex와 리뷰 GPT는 완전히 분리된 세션.
> Claude가 오케스트레이션하며 MCP로 호출하므로, 사실상 독립적인 제3자 리뷰와 동일.

---

## MCP → scripts 매핑

Codex는 MCP에 접근 불가. `scripts/` CLI wrapper로 대체.

| MCP 도구 | scripts wrapper | 용법 |
|---------|----------------|------|
| `compile_brief` | `scripts/compile-brief` | `scripts/compile-brief {novel_dir} {N}` |
| `novel-calc` | `scripts/novel-calc` | `scripts/novel-calc char_count file_path='"..."'` |
| `novel-hanja` | `scripts/novel-hanja` | `scripts/novel-hanja hanja_lookup text='"..."'` |
| `review_episode` | N/A | Claude supervisor가 MCP로 직접 호출 |

---

## Codex tmux 상호작용 패턴

### 시작
```bash
tmux new-session -d -s {{SESSION}} -x 220 -y 50 -c {{NOVEL_DIR}}
tmux send-keys -t {{SESSION}} 'codex --dangerously-bypass-approvals-and-sandbox' Enter
```
- Trust 프롬프트 생략됨 (`--dangerously-bypass-approvals-and-sandbox`)

### 프롬프트 전송
```bash
tmux send-keys -t {{SESSION}} -l '프롬프트 내용'
sleep 3          # ← 3초 대기 필수! 즉시 Enter = 줄바꿈, 3초 후 Enter = 메시지 전송
tmux send-keys -t {{SESSION}} Enter
```

> **중요**: Codex에서 Enter의 동작이 타이밍에 따라 다르다.
> - 텍스트 입력 직후 Enter → **줄바꿈** (메시지 전송 아님)
> - 3초 이상 대기 후 Enter → **메시지 전송**
> - 따라서 `sleep 3`은 안전한 최소값. 긴 프롬프트는 `sleep 5`도 고려.

### 상태 감지

| 상태 | 패턴 | 조치 |
|------|------|------|
| 작업 중 | `• Working (Ns)`, `• Explored`, `• Edited`, `• Ran` | 대기 |
| 완료 | `WRITER_DONE chapter-{NN}.md` + `›` 프롬프트 | Post-write pipeline |
| 완료 (sentinel 없음) | `›` + `gpt-5.4` 표시만 | chapter 파일 확인 후 진행 |
| 오류 | `Error`, `Permission denied` | 분석 후 복구 |
| 종료 | bash `$` 프롬프트 | Codex 재시작 |

### 완료 후 검증
```bash
# 1. sentinel 확인
tmux capture-pane -t {{SESSION}} -p -S -5 | grep WRITER_DONE

# 2. 파일 존재 확인
ls {{NOVEL_DIR}}/chapters/{arc}/chapter-{NN}.md

# 3. 분량 확인 (supervisor가 직접)
scripts/novel-calc char_count file_path='"chapters/{arc}/chapter-{NN}.md"'
```

---

## 핵심 파일

| 파일 | 역할 | 변경 여부 |
|------|------|----------|
| `.claude/prompts/codex-writer.md` | Codex 집필 프롬프트 템플릿 | **신규** |
| `batch-supervisor.md` | Supervisor 규칙 (hybrid용) | **수정** |
| `scripts/*` | MCP CLI wrapper | **복사** (codex-lean에서) |
| `.claude/agents/writer.md` | Claude writer (lean 전용) | deprecated (hybrid 미사용) |
| 나머지 agents/commands | 그대로 | 변경 없음 |

---

## 구현 상태

- [x] HYBRID-DESIGN.md 설계
- [x] `.claude/prompts/codex-writer.md` 프롬프트 템플릿
- [x] `batch-supervisor.md` hybrid용 수정 (3a/3b/3b-post/상태 판별)
- [x] `scripts/` MCP wrapper 복사
- [x] README.md hybrid용 작성
- [x] Codex tmux 상호작용 테스트 (1화 집필 성공)
- [ ] 001-hybrid 전체 프롤로그 테스트 (supervisor 자동)
- [ ] 아크 전환 A→F 테스트
