# Claude × Codex Hybrid Novel Templates

**GPT 5.4(Codex)가 쓰고, Claude Code가 지휘한다.**

AI 한국어 웹소설 집필을 위한 하이브리드 파이프라인 템플릿.

---

## 시작 전

이 템플릿은 **Claude Code + Codex CLI를 함께 쓰는 구조**다.

- Claude Code: supervisor / review / summary / git 담당
- Codex CLI: writer / fixer 담당
- MCP 서버: `compile_brief`, `novel-calc`, `novel-hanja`, `novel-editor` 등 보조 도구

사용 형태는 두 가지다.

- 구독형/정액형 환경: 각 서비스의 **자기 플랜 한도 안에서** 사용
- API 과금형 환경: 각 서비스의 **사용량 기반 과금 정책**을 따름

즉, 이 README의 핵심은 "무엇을 설치하느냐"보다 **Claude와 Codex를 어떤 역할로 나눠 쓰느냐**에 있다.

---

## 먼저 볼 문서

- [README.md](./README.md): 전체 구조와 빠른 시작
- [INIT-PROMPT.md](./INIT-PROMPT.md): 새 소설 프로젝트를 처음 만드는 프롬프트
- [batch-supervisor.md](./batch-supervisor.md): 배치 집필 supervisor 운용 규칙
- [HYBRID-DESIGN.md](./HYBRID-DESIGN.md): 왜 이렇게 분리했는지에 대한 설계 근거
- [scripts/README.md](./scripts/README.md): MCP fallback wrapper 설명
- [.claude/prompts/codex-writer.md](./.claude/prompts/codex-writer.md): Codex writer 실제 런타임 프롬프트
- [.claude/prompts/codex-fixer.md](./.claude/prompts/codex-fixer.md): Codex fixer 실제 런타임 프롬프트

초보자 기준 권장 읽기 순서:

1. 이 README
2. [INIT-PROMPT.md](./INIT-PROMPT.md)
3. [batch-supervisor.md](./batch-supervisor.md)

---

## 왜 Hybrid인가?

| 역할 | Claude Code | GPT 5.4 (Codex) |
|------|------------|-----------------|
| 한국어 prose (전투/대화/감정) | △ | **◎** |
| 오케스트레이션 (다중 에이전트) | **◎** | △ |
| 연속성 관리 | **◎** | △ |
| MCP 도구 사용 | **◎** | **◎** (native MCP) / scripts fallback |

**결론**: GPT의 prose 품질 + Claude의 오케스트레이션을 결합.

---

## 아키텍처

```
Claude Code (Supervisor)                 Codex / GPT 5.4 (Writer)
─────────────────────────                ─────────────────────────
/root/novel/ 에서 실행                    tmux 세션에서 실행
                                         소설 폴더 기준

  ┌─ writer 세션 상태 확인
  ├─ review_floor 결정
  ├─ 집필 프롬프트 생성
  │
  └──── tmux send-keys ──────→   프롬프트 수신
                                  MCP: compile_brief 호출
                                  settings/plot/prev ep 직접 읽기
                                  본문 생성 → 파일 저장
                                  MCP: char_count / hanja_lookup 보조 사용
                                  WRITER_DONE 출력
  ←──── tmux capture-pane ────
  │
  ├─ unified-reviewer (Claude) ← 핵심 검증
  ├─ external AI review: Gemini + NIM (MCP)
  ├─ narrative-fixer (Claude)
  ├─ summary update (Claude)
  ├─ EPISODE_META 삽입 (Claude)
  ├─ git commit (Claude)
  └─ 다음 화로
```

---

## 워크플로우: 매 화 집필 사이클

```
Step 1-5: Claude Supervisor (계획)
  │  compile_brief → 맥락 확인
  │  review_floor 결정
  │  집필 프롬프트 조립
  │
  ▼
Step 6: Codex Writer (집필)
  │  novel-editor MCP의 compile_brief 호출
  │  settings/plot/prev ep 직접 읽기
  │  한국어 본문 생성 → chapter 파일 저장
  │  필요 시 novel-calc / novel-hanja MCP 사용
  │  축약 자기점검 (즉흥 설정, POV, hook, 불변 조건)
  │  WRITER_DONE sentinel 출력
  │
  ▼
Step 7-12: Claude Supervisor (검증 + 후처리)
  │  7.  unified-reviewer 실행 (연속성 14항목 + 서사 + 한글)
  │  8.  external AI review: Gemini + NIM (MCP)
  │  9.  문제 발견 시 fix routing:
  │      ├─ micro/local/rewrite → Claude가 fix-spec 생성 → 같은 Codex 세션에서 수정
  │      └─ hold (구조 변경) → 다음 사이클 이관
  │  10. Codex 수정 시: FIX_DONE 확인 → Claude 재검증 (1회 한정)
  │  11. summary 갱신 + fact-check
  │  12. EPISODE_META 삽입
  │  13. action-log + git commit
  │
  ▼
다음 화로 반복
```

---

## 아크 전환 워크플로우 (A→F)

아크 마지막 화 완료 후 supervisor가 순차 실행:

```
A. OAG 탐지        → /oag-check (Claude)
B. OAG 패치        → /narrative-fix --source oag (Claude)
C. 설명 갭         → /why-check + fix (Claude)
D. 아크 통독       → Gemini 외부 AI 통독 (MCP) + fix
D.5 전문 감사      → /pov-era-check + /scene-logic-check (Claude)
D.7 반복 감사      → /repetition-check + fix (Claude)
E. 자연스러움      → /naturalness (Claude + GPT MCP) + fix
E.5 개발편집       → /narrative-review (서사 품질 거시 진단)
F. 아크 마감       → summary reset + thread triage + 새 아크 준비
```

---

## 설계 철학: "같은 모델" vs "같은 세션"

이 파이프라인에서 **GPT가 집필하므로 GPT 리뷰를 제거**한 항목과 **유지**한 항목이 있다. 구분 기준은 "같은 모델인가"가 아니라 **"같은 세션/컨텍스트를 공유하는가"**이다.

| 항목 | Codex writer와 컨텍스트 공유? | 판정 |
|------|---------------------------|------|
| GPT prose review (`gpt_feedback`) | 아니오 (MCP 별도 호출) | **제거** — prose 리뷰는 Claude가 더 효과적 (교차 모델) |
| GPT naturalness (`gpt_naturalness`) | 아니오 (MCP 별도 호출, 백지 상태) | **유지** — 결합 자연성 검출에 GPT가 Claude보다 강점. 완전 독립 세션이므로 자기 글 자기 리뷰가 아님 |
| Codex writer 세션 내 자기점검 | 예 (같은 세션) | **축약만 유지** — 즉흥설정/POV/hook/불변조건 정도 |

> GPT prose review를 제거한 이유: Claude unified-reviewer가 GPT의 글을 리뷰하면 **교차 모델 검증**이 되어 더 효과적. 같은 GPT가 prose를 리뷰하면 같은 맹점을 공유할 가능성.
>
> GPT naturalness를 유지한 이유: 결합 자연성(collocational naturalness)은 GPT가 Claude보다 잘 잡는 영역. MCP로 호출하므로 Codex writer와 **컨텍스트를 전혀 공유하지 않는** 독립 판정.

---

## lean과의 차이

| 항목 | lean | hybrid |
|------|------|--------|
| 집필 | Claude Code | **Codex (GPT 5.4)** |
| 오케스트레이션 | Claude Code | Claude Code (동일) |
| 리뷰 | Claude (자기 글 자기 리뷰) | **Claude가 GPT 글 리뷰 (교차 검증)** |
| MCP 도구 | 직접 사용 | **native MCP 우선 + scripts fallback** |
| writer.md | 12-step 전체 | **codex-writer.md** (step 6만) |
| WRITER_CMD | `claude` | `codex --dangerously-bypass-approvals-and-sandbox` |
| 완료 감지 | `❯` 프롬프트 | **`WRITER_DONE` sentinel** |
| summary/META/commit | writer가 수행 | **supervisor가 수행** |
| 외부 리뷰 | Claude + Gemini + GPT + NIM | **Claude + Gemini + NIM + GPT naturalness** (GPT prose만 제거) |
| tmux 세션 | 1개 (Claude writer) | **2개 tmux**: Codex writer + Claude review. Supervisor가 관리 |

---

## 빠른 시작

### 가장 쉬운 시작 순서

처음 쓰는 경우에는 아래 순서가 가장 단순하다.

1. 이 템플릿을 새 소설 폴더로 복사
2. Codex MCP 등록
3. [INIT-PROMPT.md](./INIT-PROMPT.md)를 열고 Claude Code로 프로젝트 초기화
4. 생성된 소설 폴더의 `batch-supervisor.md`를 기준으로 supervisor 실행
5. Claude supervisor가 Codex writer 세션을 만들고 집필 시작

직접 파일을 하나씩 채우기보다, **INIT-PROMPT로 초기 셋업을 끝낸 뒤 batch-supervisor로 집필을 굴리는 방식**이 초보자에게 가장 안전하다.

### 1. 새 소설 프로젝트 생성

```bash
cp -r claude-codex-novel-templates-hybrid/ /root/novel/no-title-XXX/
cd /root/novel/no-title-XXX/
```

### 2. 설정 채우기

```
CLAUDE.md         → {{PLACEHOLDER}} 채우기
settings/         → 01~08 설정 파일 작성
plot/             → master-outline + arc plots
```

### 3. Codex MCP 등록

```bash
# 한 번만 등록
codex mcp add novel-calc -- python3 /root/novel/mcp-novel-calc/calc_server.py
codex mcp add novel-hanja -- python3 /root/novel/mcp-novel-hanja/hanja_server.py
codex mcp add novel-naming -- python3 /root/novel/mcp-novel-naming/naming_server.py
codex mcp add novel-editor -- python3 /root/novel/mcp-novel-editor/editor_server.py

# 확인
codex mcp list
```

MCP를 등록하지 않은 환경에서는 `scripts/`를 fallback으로 쓸 수 있다.

### 4. scripts 확인 (fallback)

```bash
# MCP wrapper scripts (fallback)
scripts/compile-brief /root/novel/no-title-XXX 1
scripts/novel-calc char_count file_path='"chapters/prologue/chapter-01.md"'
scripts/novel-hanja hanja_lookup text='"天外歸還"'
scripts/novel-naming /root/novel/no-title-XXX 1-10
```

### 5. Supervisor 실행

```bash
# Claude Code supervisor
cd /root/novel
claude

# Supervisor에게 지시:
# "no-title-XXX 소설을 batch-supervisor.md 규칙에 따라 감독해줘.
#  SESSION=write-XXX, START_EP=1, END_EP=50"
```

### 6. Writer/Review 세션 (supervisor가 자동 생성)

```bash
# Writer tmux 세션 생성:
tmux new-session -d -s write-XXX -x 220 -y 50 -c /root/novel/no-title-XXX
sleep 1
tmux send-keys -t write-XXX 'codex --dangerously-bypass-approvals-and-sandbox'
sleep 3    # Codex: 3초 대기 후 Enter
tmux send-keys -t write-XXX Enter

# Review tmux 세션 생성:
tmux new-session -d -s write-XXX-review -x 220 -y 50 -c /root/novel/no-title-XXX
sleep 1
tmux send-keys -t write-XXX-review 'unset CLAUDECODE && claude'
sleep 3
tmux send-keys -t write-XXX-review Enter
```

---

## INIT-PROMPT 사용 예시

새 프로젝트를 만드는 가장 쉬운 방법은 [INIT-PROMPT.md](./INIT-PROMPT.md)를 그대로 쓰는 것이다.

### 예시 1. 시나리오 제안부터 받고 싶을 때

1. `/root/novel`에서 Claude Code 실행
2. [INIT-PROMPT.md](./INIT-PROMPT.md)의 `프롬프트 1: 시나리오 선택형`을 복사
3. 장르/톤/총 화수만 바꿔서 붙여넣기

예:

```text
claude-codex-novel-templates-hybrid/ 를 참고해서 새 소설 프로젝트를 만들어줘.

## 조건
- 장르: 무협 회귀물
- 톤: 진지+유머 8:2
- 분량: 4500~6000자
- 총 화수: 120화
- 특이사항: 한자 병기 필요
```

이 경로에서는 Claude가:

- 시나리오 3개 제안
- story-consultant 평가
- 선택된 컨셉 기준 파일 생성
- plot 사전 검증
- 기본 git 초기화

까지 진행한다.

### 예시 2. 이미 컨셉이 정해져 있을 때

[INIT-PROMPT.md](./INIT-PROMPT.md)의 `프롬프트 2: 컨셉 확정형`을 사용하면 된다.

예:

```text
claude-codex-novel-templates-hybrid/ 를 참고해서 새 소설 프로젝트를 만들어줘.

## 소설 정보
- 제목: 천외귀환록
- 부제: 없음
- 장르: 무협 회귀물
- 톤: 냉정하고 건조한 정통 무협
- 한줄 소개: 멸문 직전으로 돌아온 검객이 가장 늦기 전에 가문을 다시 세운다.
- 배경: 가상의 무림 세계
- 분량: 4500~6000자
- 총 화수: 120화
```

### INIT-PROMPT를 쓸 때 중요한 점

- `INIT-PROMPT`는 **프로젝트 생성 전용**이다.
- 여기서 에피소드 집필까지 바로 시키지 않는다.
- 초기 셋업이 끝나면 다음 단계는 [batch-supervisor.md](./batch-supervisor.md)다.

---

## batch-supervisor 사용법

[batch-supervisor.md](./batch-supervisor.md)는 "한 화씩 어떻게 굴릴지"를 적은 운영 문서다.

초보자 기준으로는 아래처럼 이해하면 된다.

### 세션 3개가 있다

1. Supervisor
   - `/root/novel`에서 실행하는 Claude Code
   - tmux 세션 상태 확인, 프롬프트 조립, 진행 판단 담당
2. Writer
   - 소설 폴더 안에서 실행하는 Codex
   - 본문 생성과 fix-spec 기반 수정 담당
3. Review
   - 소설 폴더 안에서 실행하는 Claude Code
   - 리뷰, summaries, EPISODE_META, git commit 담당

### 실제 사용 순서

1. INIT-PROMPT로 `no-title-XXX/` 프로젝트를 만든다.
2. 그 폴더 안의 [batch-supervisor.md](./batch-supervisor.md)를 연다.
3. 문서 상단 변수들을 자기 프로젝트 값으로 맞춘다.
   - `NOVEL_ID`
   - `SESSION`
   - `NOVEL_DIR`
   - `START_EP`
   - `END_EP`
   - `ARC_MAP`
4. `/root/novel`에서 Claude Code를 연다.
5. `batch-supervisor.md`의 프롬프트를 supervisor Claude에게 붙여넣는다.
6. supervisor가 writer/review tmux 세션을 만들고 집필을 돌린다.

### 가장 단순한 예시

소설 폴더가 `/root/novel/no-title-020`이고, 1화부터 10화까지 프롤로그/1아크를 돌린다고 하면:

- `NOVEL_ID`: `no-title-020`
- `SESSION`: `write-020`
- `NOVEL_DIR`: `/root/novel/no-title-020`
- `START_EP`: `1`
- `END_EP`: `10`

`ARC_MAP` 예시:

```json
{
  "prologue": [1, 3],
  "arc-01": [4, 10]
}
```

그다음 `/root/novel`에서 Claude를 열고, [batch-supervisor.md](./batch-supervisor.md)의 프롬프트를 넣으면 된다.

### batch-supervisor에서 꼭 알아야 할 것

- writer가 끝나면 `WRITER_DONE chapter-XX.md`를 출력한다.
- supervisor는 그걸 보고 review 세션으로 후처리를 넘긴다.
- 본문 수정이 필요하면 Claude가 fix-spec을 만들고, Codex가 같은 writer 세션에서 수정한다.
- summaries, EPISODE_META, git commit은 Codex가 아니라 Claude가 한다.

즉, 초보자 기준 요약은 이렇다.

- 프로젝트 생성: [INIT-PROMPT.md](./INIT-PROMPT.md)
- 연속 집필 운영: [batch-supervisor.md](./batch-supervisor.md)
- 세부 설계 이해: [HYBRID-DESIGN.md](./HYBRID-DESIGN.md)

---

## 폴더 구조

```
claude-codex-novel-templates-hybrid/
├── CLAUDE.md                      ← 소설 헌법 (템플릿)
├── HYBRID-DESIGN.md               ← 하이브리드 설계 문서
├── batch-supervisor.md            ← Supervisor 규칙 (hybrid용)
├── batch-supervisor-audit.md      ← Supervisor 운용 감사 메모
├── INIT-PROMPT.md                 ← 신규 프로젝트 초기화 프롬프트
├── MIGRATION-PROMPT.md            ← 기존 프로젝트 마이그레이션 프롬프트
├── REBUILD-PROMPT.md              ← 리빌드 프롬프트
├── compile_brief.py               ← 맥락 압축 엔진
├── scripts/                       ← Codex용 MCP wrapper (fallback)
│   ├── compile-brief
│   ├── novel-calc
│   ├── novel-hanja
│   ├── novel-naming
│   ├── run-codex-auditor
│   ├── run-codex-writer
│   └── run-codex-supervisor
├── .claude/
│   ├── agents/                    ← Claude 에이전트 (검증/수정)
│   │   ├── unified-reviewer.md
│   │   ├── narrative-fixer.md
│   │   ├── oag-checker.md
│   │   ├── why-checker.md
│   │   ├── pov-era-checker.md
│   │   ├── scene-logic-checker.md
│   │   ├── repetition-checker.md
│   │   ├── korean-naturalness.md
│   │   ├── narrative-reviewer.md
│   │   ├── story-consultant.md
│   │   ├── book-reviewer.md
│   │   ├── full-audit.md
│   │   └── ...
│   ├── commands/                  ← Claude 커맨드 (/oag-check, /why-check 등)
│   └── prompts/
│       ├── codex-writer.md        ← Codex 집필 프롬프트 템플릿
│       └── codex-fixer.md         ← Codex 수정 프롬프트 템플릿
├── .claude/settings.local.example.json
│                                  ← 로컬 설정 예시
├── settings/                      ← 소설 설정 (템플릿)
├── summaries/                     ← 요약 파일 (템플릿)
├── reference/                     ← 참조 테이블
└── plot/                          ← 플롯 (템플릿)
```

---

## 에이전트 역할 분담

### Codex (GPT 5.4) — 집필만
- 소설 본문 생성
- native MCP 사용: `compile_brief`, `char_count`, `hanja_lookup`
- 파일 직접 저장
- 축약 자기점검

### Claude Code — 나머지 전부
| 에이전트 | 역할 |
|---------|------|
| **unified-reviewer** | 연속성 14항목 + 서사 품질 + 한글 교정 |
| **narrative-fixer** | 수술적 본문 수정 (oag/why/arc-read/pov-era/scene-logic/repetition) |
| **oag-checker** | 의무 행동 갭 탐지 |
| **why-checker** | 설명 갭 + 결과 공백 탐지 |
| **pov-era-checker** | 시점 지식 + 시대 적합성 감사 |
| **scene-logic-checker** | 장면 내 물리 논리 감사 |
| **repetition-checker** | 크로스 에피소드 반복 패턴 감사 |
| **korean-naturalness** | 한국어 자연스러움 감사 |
| **plot-surgeon** | 플롯 수선 (plot-change-needed 시) |

## MCP 서버

| MCP | 역할 | 사용 시점 |
|-----|------|----------|
| [mcp-novel-editor](https://github.com/NA-DEGEN-GIRL/mcp-novel-editor) | 외부 AI 리뷰 (Gemini/GPT/NIM), compile_brief | 매 화 리뷰 + 아크 통독 |
| [mcp-novel-calc](https://github.com/NA-DEGEN-GIRL/mcp-novel-calc) | 날짜/거리/경제 계산, 분량 측정 | 집필 중 수치 검증 |
| [mcp-novel-hanja](https://github.com/NA-DEGEN-GIRL/mcp-novel-hanja) | 한자 조회/검증/검색 | 무협/사극 한자 병기 |
| [mcp-novel-naming](https://github.com/NA-DEGEN-GIRL/mcp-novel-naming) | 고유명사 표기 변이 탐지 | 아크 경계 + periodic check |
| [mcp-novelai-image](https://github.com/NA-DEGEN-GIRL/mcp-novelai-image) | 삽화/커버 이미지 생성 | 커버 + 에피소드 삽화 (선택) |

### Writer / Review 분담

| 기능 | Writer (Codex) | Review (Claude) |
|------|----------------|-----------------|
| `compile_brief` | 기본 사용 | 재검증 가능 |
| `char_count` | 기본 사용 | 재검증 가능 |
| `hanja_lookup` | 필요 시 사용 | 보정 |
| `naming_check` | 선택 가능 | periodic/아크 경계 기본 |
| `review_episode` | 사용 안 함 | 전담 |
| summaries / EPISODE_META / git | 사용 안 함 | 전담 |

> **Codex도 MCP를 네이티브로 지원한다.** `codex mcp add`로 서버를 등록하면 Claude Code와 동일하게 MCP 도구를 사용한다. `scripts/`는 MCP 미설정 시 fallback이다. Writer가 MCP를 누락해도 Claude review 세션이 동일 검증을 수행한다.

---

## 관련 레포

- [claude-novel-templates-lean](https://github.com/NA-DEGEN-GIRL/claude-novel-templates-lean) — Claude 전용 lean 버전
