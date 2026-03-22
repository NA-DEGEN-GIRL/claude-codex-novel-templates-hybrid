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
| Claude unified-reviewer | 자기 글 자기 리뷰 (약점) | **핵심 검증자** | GPT가 쓴 글을 Claude가 검증 = 교차 검증 |
| Gemini (MCP) | continuity/worldbuilding | **유지** | 세 번째 모델의 시각 |
| NIM (MCP) | spelling/grammar | **유지** | 맞춤법 전담 |
| GPT prose review | 유지 | **제거** | 같은 모델이 쓰고 리뷰 = 맹점 공유 |
| GPT naturalness | 유지 | **제거** | 동일 모델 |

> **hybrid 3자 리뷰 체계**: GPT(집필) → Claude(검증) + Gemini(보조) + NIM(교정)
>
> CLAUDE.md 변경:
> ```
> gpt_feedback: false
> gpt_naturalness: N/A (제거)
> ```

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

## 수정 라우팅 (Fix Routing)

> **원칙: Claude는 무엇을 고칠지 결정하고, Codex는 어떻게 고칠지 쓴다.**

### 라우팅 기준

| 수정 유형 | 수행자 | 이유 |
|----------|--------|------|
| 사실관계 micro-patch (이름/시점/설정 1-3문장) | **Claude 직접** | 톤 영향 없음 |
| 연속성/논리 위반 (사실만 교정) | **Claude 직접** | "오른손"→"왼손" 수준 |
| 감정선/리듬/묘사 밀도 변경 | **Codex 재작성** | 문체 일관성 필수 |
| 대화 톤/캐릭터 보이스 수정 | **Codex 재작성** | 원 작성 모델이 유지 |
| 장면 구조 변경 (순서/삭제/추가) | **Codex 재작성** | 장면 호흡 영향 |

### 2단계 수정 프로세스

```
1. Claude fix-spec generator
   - 문제 유형, 위치, 원인
   - 수정 목표
   - 반드시 유지할 요소 (톤/리듬/캐릭터)
   - 출력: 인라인 또는 임시 fix-spec

2. 라우팅 판단:
   - micro-patch (사실관계 1-3문장) → Claude 직접 수정
   - prose 수정 (문단+ 또는 톤 영향) → Codex에 partial rewrite 요청

3. Codex style-preserving rewrite
   - fix-spec 기반으로 해당 구간만 재작성
   - 앞뒤 문맥 유지, 기존 문체/리듬 보존
   - REWRITE_DONE sentinel 출력
```

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
patch_class = micro  → Claude 직접 수정 (1-3문장 사실관계)
patch_class = local  → Codex fixer (문단 내 수정, 톤 영향)
patch_class = rewrite → Codex fixer (장면 수준 재작성)
patch_class = hold   → 다음 사이클로 이관
```

### 운영 방식

- 진단은 배치: 모든 checker를 먼저 돌려 fix-spec들을 수집
- 수정은 번들: 한 화의 모든 fix-spec을 모아 Codex에 한 번에 전달
- tmux는 작업 큐 트리거만: 긴 프롬프트 대신 `fix-spec 파일 경로`를 전달
- 집필 세션 ≠ 수정 세션: writer 컨텍스트 오염 방지

```
Claude: "tmp/fix-specs/chapter-018.md 를 읽고 수정해줘. 완료 후 FIX_DONE"
Codex: 파일 읽기 → 수정 → FIX_DONE chapter-018
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
- [x] `.claude/prompts/codex-writer.md` 프롬프트 템플릿
- [x] `batch-supervisor.md` hybrid용 수정 (3a/3b/3b-post/상태 판별)
- [x] `scripts/` MCP wrapper 복사
- [x] README.md hybrid용 작성
- [x] Codex tmux 상호작용 테스트 (1화 집필 성공)
- [x] fix-spec 공통 스키마 정의
- [x] Codex fixer 프롬프트 템플릿 (`.claude/prompts/codex-fixer.md`)
- [x] Supervisor fix routing 로직 (batch-supervisor 3b-post)
- [x] Checker→fix-spec 변환 매핑 테이블
- [ ] 001-hybrid 전체 프롤로그 테스트 (supervisor 자동)
- [ ] 아크 전환 A→F 테스트
