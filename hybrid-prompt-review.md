# Hybrid Prompt Review

> 검토일: 2026-03-23
> 대상: `/root/novel/claude-codex-novel-templates-hybrid/*PROMPT.md`, `/root/novel/claude-codex-novel-templates-hybrid/.claude/prompts/*`
> 범위: 프롬프트 문서 구조 및 운영 정합성 리뷰. 실제 end-to-end 실행 테스트는 미포함.

---

## 핵심 판단

실제 런타임 템플릿인 `.claude/prompts/codex-writer.md`, `.claude/prompts/codex-fixer.md`는 현재 hybrid 구조와 비교적 잘 맞는다.

반면 사용자가 처음 복붙하는 상위 프롬프트들 `INIT-PROMPT.md`, `MIGRATION-PROMPT.md`, `REBUILD-PROMPT.md`는 아직 **lean 용어**, **외부 GPT 자문 전제**, **deprecated writer 참조**가 섞여 있다. 즉, 실행 코어보다 진입 문서가 더 stale하다.

---

## Findings

### 1. 상위 프롬프트들이 외부 GPT 자문을 사실상 기본 전제로 둔다

파일:
- [INIT-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/INIT-PROMPT.md#L43)
- [REBUILD-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/REBUILD-PROMPT.md#L65)
- [REBUILD-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/REBUILD-PROMPT.md#L98)
- [REBUILD-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/REBUILD-PROMPT.md#L148)
- [MIGRATION-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/MIGRATION-PROMPT.md#L151)

문제:
- `ask_gpt`, `mcp__external-ai__ask_gpt` 같은 외부 GPT 자문이 여러 단계에서 사실상 필수 절차처럼 들어가 있다.
- 현재 hybrid의 핵심은 `Claude orchestration + Codex writing`인데, 상위 프롬프트는 오히려 외부 GPT 의존이 더 강하다.
- 이건 환경 의존성을 높이고, “로컬만으로 돌아가는 템플릿”이라는 기대를 깨뜨릴 수 있다.

판단:
- 외부 자문은 선택 옵션으로는 좋다.
- 하지만 기본 경로의 필수 단계로 두는 건 과하다.

### 2. `MIGRATION-PROMPT.md`는 이름과 본문 모두 lean 잔재가 크다

파일:
- [MIGRATION-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/MIGRATION-PROMPT.md#L1)
- [MIGRATION-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/MIGRATION-PROMPT.md#L30)
- [MIGRATION-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/MIGRATION-PROMPT.md#L221)

문제:
- 제목이 아직 `Lean 마이그레이션`이다.
- 문서 곳곳에서 `lean 골격`, `lean 구조`, `lean 대응`을 계속 사용한다.

판단:
- 현재 저장소 이름과 운영 철학은 hybrid인데, 가장 중요한 마이그레이션 문서가 이전 명칭을 유지하면 혼선이 생긴다.

### 3. deprecated `writer.md`가 상위 프롬프트에서 아직 실운영 기준처럼 보인다

파일:
- [INIT-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/INIT-PROMPT.md#L127)
- [MIGRATION-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/MIGRATION-PROMPT.md#L116)
- [MIGRATION-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/MIGRATION-PROMPT.md#L257)
- [writer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/writer.md#L1)

문제:
- `writer partial-rewrite mode`, `writer.md 분량`, old→lean 매핑표의 `writer` 등 deprecated 문서를 여전히 살아 있는 집필 기준처럼 참조한다.
- 실제 hybrid 실행 주체는 `Codex writer prompt`인데, 상위 프롬프트는 아직 그 전환을 완전히 반영하지 못했다.

판단:
- reference-only 문서를 상위 진입 프롬프트에서 운영 기준으로 다시 호출하면 문서 계층이 꼬인다.

### 4. 복제/실험 프롬프트가 아직 Claude 집필을 기본 예시로 든다

파일:
- [INIT-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/INIT-PROMPT.md#L249)

문제:
- `WRITER_CMD` 예시가 `claude`, `claude --model ...` 위주다.
- 현재 템플릿의 핵심 차별점은 Codex 집필인데, 실험용 진입점 예시는 그 방향을 살리지 못한다.

판단:
- 복제 실험용 문서는 “모델 비교”라는 목적 때문에 Claude 예시가 있을 수 있다.
- 그래도 기본 예시의 첫 번째는 현재 표준 경로인 Codex가 되는 편이 자연스럽다.

### 5. 런타임 프롬프트는 비교적 잘 정리되어 있다

파일:
- [codex-writer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/prompts/codex-writer.md#L1)
- [codex-fixer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/prompts/codex-fixer.md#L1)

강점:
- `Codex는 본문만`, `Claude supervisor는 리뷰/summary/git` 분리가 명확하다.
- `Voice Profile 우선`, `summary 수정 금지`, `fix-spec 기반 수정` 등이 현재 hybrid와 맞는다.
- `micro/local/rewrite` 모두 Codex가 수행한다는 점도 일관적이다.

판단:
- 현재 구조에서 가장 믿을 수 있는 문서는 오히려 이 두 개다.

---

## 파일별 평가

### 1. `INIT-PROMPT.md`

파일:
- [INIT-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/INIT-PROMPT.md#L1)

평가:
- **REVISE**

강점:
- 신규 프로젝트 생성 절차가 매우 구체적이다.
- `story-consultant`, `/oag-check plan`, `/why-check plan`, 교차 검증까지 순서가 좋다.

리스크:
- 외부 GPT 자문이 너무 깊게 들어간다.
- deprecated `writer.md` 참조가 남아 있다.
- 복제 실험 프롬프트가 hybrid 핵심보다 Claude 예시를 앞세운다.

총평:
- 뼈대는 좋다.
- 진입 문서답게 더 단순하고 현재 표준 경로에 맞춰 정리할 필요가 있다.

### 2. `MIGRATION-PROMPT.md`

파일:
- [MIGRATION-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/MIGRATION-PROMPT.md#L1)

평가:
- **REVISE**

강점:
- 마이그레이션 체크리스트가 촘촘하다.
- 검증 게이트와 승인 게이트가 분리돼 있어 안전하다.

리스크:
- 제목과 본문에 lean 용어가 과다하게 남아 있다.
- GPT 의미 검증과 내부 agent 검증이 실제보다 더 무거운 프로세스로 보일 수 있다.
- old→lean 매핑표가 현재 hybrid 명칭과 충돌한다.

총평:
- 유용하지만 naming과 서술을 current-state 기준으로 다시 써야 한다.

### 3. `REBUILD-PROMPT.md`

파일:
- [REBUILD-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/REBUILD-PROMPT.md#L1)

평가:
- **REVISE**

강점:
- 재구축 절차가 매우 논리적이다.
- 보존 명세서 → 컨셉 재평가 → 설정 재정립 → 사전 검증 → summaries 초기화 순서가 좋다.

리스크:
- 외부 GPT 자문이 여러 단계에서 완료 조건처럼 들어간다.
- 집필 시작 단계 예시가 다시 Claude 중심으로 읽힌다.
- 재구축 목적은 hybrid 재출발인데, 런타임 기준 문서보다 상위 절차가 더 무겁고 외부 의존적이다.

총평:
- 구조는 좋다.
- 그러나 실제로 쓰려면 “필수 경로”와 “선택 자문 경로”를 분리하는 편이 맞다.

### 4. `.claude/prompts/codex-writer.md`

파일:
- [codex-writer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/prompts/codex-writer.md#L1)

평가:
- **GO**

강점:
- 책임 분리가 명확하다.
- Voice Profile 우선 규칙이 잘 들어가 있다.
- supervisor와 writer의 역할 경계가 분명하다.

리스크:
- `CLAUDE.md`와 `settings/`를 직접 읽게 하는 만큼, 상위 문서 충돌이 생기면 가장 먼저 영향받는다.

총평:
- 현재 hybrid의 가장 안정적인 런타임 템플릿이다.

### 5. `.claude/prompts/codex-fixer.md`

파일:
- [codex-fixer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/prompts/codex-fixer.md#L1)

평가:
- **GO**

강점:
- fix-spec 중심 설계가 깔끔하다.
- `micro/local/rewrite`를 모두 Codex 수정으로 통일한 점이 좋다.
- 범위 밖 수정 금지, must_keep/must_avoid가 명확하다.

리스크:
- fix-spec 생성 품질이 낮으면 그대로 오염된다.

총평:
- supervisor가 제대로 spec만 써주면 잘 작동할 구조다.

---

## 제안

### A. 상위 프롬프트에서 외부 GPT 자문을 전부 `선택 옵션`으로 낮추기

권장 원칙:

- 기본 경로: Claude + local agents + Codex만으로 완료
- 선택 경로: Gemini/GPT 외부 자문 추가

권장 문구:

```md
### 선택 단계: 외부 AI 자문

환경에 외부 AI MCP가 연결되어 있으면 GPT/Gemini 자문을 추가로 받을 수 있다.
없으면 이 단계를 건너뛰고 Claude의 내부 평가 + agent 검증만으로 진행한다.
```

효과:
- 프롬프트의 휴대성이 좋아진다.
- 운영 환경 차이 때문에 첫 실행이 깨지는 일을 줄인다.

### B. `MIGRATION-PROMPT.md`의 `lean` 용어를 전부 `hybrid` 기준으로 교체

권장 치환:

- `Lean 마이그레이션` → `Hybrid 마이그레이션`
- `lean 골격` → `hybrid 골격`
- `old → lean` → `old → hybrid`
- `lean 대응` → `hybrid 대응`

효과:
- 현재 저장소 정체성과 문서 제목이 일치한다.

### C. deprecated `writer.md` 참조를 런타임 프롬프트 기준으로 치환

권장 치환 방향:

- `writer partial-rewrite mode` → `Codex rewrite-brief / codex-writer partial rewrite`
- `writer.md 분량` → `codex-writer.md 분량 규칙`
- 매핑표의 `writer`는 `codex-writer prompt` 또는 `Codex writer session` 기준으로 재서술

효과:
- 문서 계층이 정리된다.
- reference-only 문서가 실운영 기준처럼 보이는 문제를 막는다.

### D. INIT 복제/실험 프롬프트의 기본 집필 명령 예시를 Codex 우선으로 재배치

권장 예시 순서:

1. `codex --full-auto`
2. `codex ...` 커스텀 옵션
3. Claude 계열 예시

효과:
- 현재 템플릿의 표준 경로가 무엇인지 사용자가 바로 이해한다.

### E. 상위 프롬프트의 “완료 기준”에서 외부 GPT 승인 조건 제거

예:

현재:
- `story-consultant GO 판정 + GPT 동의`

권장:
- `story-consultant GO 판정`
- `외부 GPT 자문이 있으면, high-risk 항목만 추가 반영`

효과:
- 로컬 단독 운용이 가능해진다.
- 하이브리드의 중심축이 흐려지지 않는다.

---

## 최소 수정 세트

시간이 없으면 아래만 먼저 고치는 편이 좋다.

1. [MIGRATION-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/MIGRATION-PROMPT.md#L1) 제목과 `lean` 용어 전면 교체
2. [INIT-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/INIT-PROMPT.md#L43) 외부 GPT 자문을 선택 단계로 강등
3. [REBUILD-PROMPT.md](/root/novel/claude-codex-novel-templates-hybrid/REBUILD-PROMPT.md#L65) 외부 GPT 완료 조건 제거
4. 상위 프롬프트 전반의 `writer.md` 직접 참조를 `codex-writer.md` 또는 `Codex writer session` 기준으로 교체

---

## 결론

프롬프트 계층은 `실행 코어는 꽤 정리됐고, 진입 문서가 아직 과거 습관을 끌고 가는 상태`다.

따라서 우선순위는 명확하다.

1. `.claude/prompts/`는 유지
2. `INIT/MIGRATION/REBUILD`를 hybrid 현재 상태에 맞게 재서술
3. 외부 GPT 자문은 기본 경로에서 빼고 선택 옵션으로 내리기

이 세 가지만 하면 프롬프트 계층 완성도가 크게 올라간다.
