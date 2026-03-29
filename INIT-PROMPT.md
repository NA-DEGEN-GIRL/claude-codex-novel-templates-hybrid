# 소설 초기 셋업 프롬프트

> `/root/novel/`(상위 폴더)에서 Claude Code를 열고 아래 프롬프트를 붙여넣는다.
> Claude가 시나리오를 제안하고, 선택 후 전체 프로젝트를 자동 생성한다.

---

## 사용법

```bash
cd /root/novel && claude
```

아래 프롬프트 중 하나를 선택하여 붙여넣는다.

---

## 프롬프트 1: 시나리오 선택형 (추천)

장르와 키워드만 주면 Claude가 3개 시나리오를 제안하고, 선택 후 전체 셋업을 수행한다.

```
claude-codex-novel-templates-hybrid/ 를 참고해서 새 소설 프로젝트를 만들어줘.

## 조건

- 장르: [장르] (예: 무협 회귀물, SF 스릴러, 현대 로맨스, 판타지)
- 톤: [톤앤무드] (예: 다크+감성 8:2, 진지+유머 7:3, 코미디 중심)
- 분량: [에피소드 목표 분량] (예: 4000~6000자)
- 총 화수: [목표 화수] (예: 70화, 200화)
- 특이사항: [있으면 적어줘] (예: 한자 병기 필요, 현대 배경이라 외래어 OK 등)

## 진행 방식

### 1단계: 시나리오 제안
위 조건으로 **서로 다른 컨셉의 시나리오 3개**를 제안해줘. 각 시나리오마다:
- 제목 + 한줄 소개
- 주인공 (이름, 한줄 설명) — 이름 선택 시 `reference/name-table.md` 참조 가능
- 핵심 갈등/컨셉
- 예상 아크 구성 (대략적)
- 차별점 (왜 이 시나리오가 재밌는지)

### 1.5단계: 외부 AI 아이디어 의논 (optional — codex mode 권장, claude mode 선택)
시나리오 3개를 **GPT 5.4에게 보여주고 의견을 받는다** (`ask_gpt` MCP 활용).

- 각 시나리오의 상업성, 독자 흡인력, 장르 차별성에 대한 GPT 의견
- Claude가 놓친 아이디어나 변주 제안
- "이 컨셉으로 50화+ 연재가 가능한가" 관점의 지속 가능성 피드백
- codex mode: GPT가 집필 모델이므로 실행 관점 피드백이 특히 유용
- claude mode: 교차 검증 목적. 필수는 아니지만 다른 모델의 시각이 도움될 수 있음

### 1.7단계: 전문가 컨셉 평가
시나리오를 **story-consultant 에이전트**(`claude-codex-novel-templates-hybrid/.claude/agents/story-consultant.md`)로 평가한다. 7개 관점에서 채점하고 리스크를 진단한다.

- 각 시나리오에 GO / REVISE / NO-GO 판정
- 강점, 리스크, "3화까지 보여줘야 할 것" 제시
- 결과를 사용자에게 보여주고 선택에 참고하게 한다

### 2단계: 선택 & 확장
내가 하나를 고르면 (또는 여러 개를 섞으라고 하면), 그걸로:
- 주요 캐릭터 3~5명 설계
- 아크별 대략적 플롯
- 핵심 약속 3가지
- 세계관 핵심 규칙

을 정리해서 보여줘.

### 2.5단계: 확장 컨셉 재평가
확장된 컨셉(캐릭터, 아크 설계, 핵심 약속)을 **story-consultant 에이전트**(`claude-codex-novel-templates-hybrid/.claude/agents/story-consultant.md`)로 재평가한다.

- 에피소드 엔진 강도, 주인공 매력, 장르 쾌감 밀도, 아크 지속 가능성
- 필수 수정 사항 (GO 전 해결)
- 파일 생성 시 반드시 보존할 것
- 예상 위험 요소 (집필 중 주의)

**전문가 평가가 GO가 나오면** 3단계로 진행. REVISE가 나오면 수정 후 재평가.

### 3단계: 프로젝트 생성
claude-codex-novel-templates-hybrid/의 구조를 참조하여 아래 체크리스트대로 전체 파일을 생성해줘:

1. 소설 폴더 생성 (no-title-XXX, 다음 번호 자동 결정)
2. 템플릿 파일 복사 (CLAUDE.md, settings/, .claude/agents/, .claude/commands/, summaries/ 등)
3. 권한 설정: `.claude/settings.local.example.json`을 `.claude/settings.local.json`으로 복사 (`claude -p` 배치 실행에 필수)
4. CLAUDE.md의 {{PLACEHOLDER}} 전부 채우기
5. settings/ 파일 전부 실제 내용으로 작성 (01-style-guide.md ~ 05-continuity.md, 07-periodic.md, 08-illustration.md, 선택: 06-humor-guide.md)
6. plot/master-outline.md 작성 (전체 아크 구성)
7. plot/foreshadowing.md 초기 복선 설계
8. plot/arc-01.md 작성 (1아크 상세 플롯). 모든 plot 파일(prologue, arc-XX, epilogue, interlude 등)의 에피소드 항목에 optional `risk:` 필드 사용 가능 — 허용 값: `oag`, `why`, `pov-era`, `scene-logic` (쉼표 구분). 고위험 장면에만 태깅. 없으면 생략.
9. summaries/ 초기 파일 생성 (빈 템플릿: running-context.md, episode-log.md, character-tracker.md, promise-tracker.md, knowledge-map.md, relationship-log.md, explained-concepts.md, hanja-glossary.md, illustration-log.md, decision-log.md, editor-feedback-log.md)
10. batch-supervisor.md 생성 (아크 매핑, 화수 범위 설정)
11. config.json에 새 소설 등록 (totalEpisodes: 0, parts 구조)
12. .gitignore, vercel.json 보안 설정 추가

**에피소드 집필은 하지 않는다. 파일 생성 후 3.7단계 Writer Runtime 정밀 검토로 넘어간다.**

### 3.7단계: Writer Runtime 정밀 검토

`3단계`의 5번(`settings/` 작성) 완료 직후, **실제 집필에 쓸 writer 계열**이 settings 핵심 3종을 검토한다. 이 단계에서는 본문을 쓰지 않는다.

- `writer_model: codex` 예정이면 `ask_gpt` MCP를 활용해 GPT 관점에서 검토
- `writer_model: claude` 예정이면 `claude-writer-role.md` / `claude-writer.md` 기준으로 Claude writer 관점에서 검토

- 검토 순서: `01-style-guide.md` → `03-characters.md` → `02-episode-structure.md`
- `01-style-guide.md`: Voice Profile이 평균체로 미끄러지지 않는지, 대표 문단·우선순위·금지 패턴이 같은 목소리를 가리키는지 점검. **이 파일이 소설의 읽힘을 가장 크게 결정한다.**
- `03-characters.md`: 주인공과 핵심 인물의 동기·말투·대표 대사가 실제 집필에서 서로 교체 불가능한 수준으로 구분되는지 점검
- `02-episode-structure.md`: 훅, 감정 곡선, 변화량, 분량 규칙이 장르와 Voice Profile을 밀어주는지 점검
- 산출물: 파일별 `GO / REVISE` + 수정 필요 항목 요약
- `REVISE`가 하나라도 나오면 Claude가 settings를 수정한 뒤 이 단계를 **1회 재실행**
- 3회째 REVISE가 나오면 사용자에게 판단을 요청한다
- 통과 후 `3.5단계` 플롯 사전 검증으로 진행

> **왜 이 단계가 필요한가**: Voice Profile 하나의 차이가 소설 전체의 문체를 바꾼다. 설정을 만든 쪽과 실제 집필 writer가 다르면, "규칙은 맞지만 안 읽히는" 문체가 고착되기 쉽다. 초기 세팅에서 잡는 비용이 50화 뒤에 고치는 비용보다 압도적으로 낮다.

### 3.5단계: 플롯 사전 검증

생성된 `plot/master-outline.md`와 **첫 집필 구간의 상세 plot 파일**(`plot/prologue.md`, `plot/arc-01.md` 등 `ARC_MAP`의 시작 구간에 해당하는 파일)에 대해 두 가지 사전 검증을 실행한다.

**A. `/oag-check plan` (동기 갭 검증 — 먼저)**
- `oag-checker.md`의 Planning Mode 절차를 따른다.
- 각 캐릭터의 최우선 목표와 플롯 내 행동이 충돌하지 않는지 검증한다.
- PLANNING GAP / MOTIVATION GAP이 발견되면 **즉시 플롯을 수정**한다.
- 산출물: `summaries/oag-check-plan-arc-01.md`

**B. `/why-check plan` (설명 갭 검증 — A 수정 후)**
- `why-checker.md`의 Planning Mode 절차를 따른다.
- 각 플롯의 주요 사건에 대해 WHY/HOW/WHEN/SO-WHAT 질문을 생성한다.
- PLANNING GAP(답이 아무 곳에도 없음)이 발견되면 **즉시 플롯을 수정**한다.
- 산출물: `summaries/why-check-plan-master.md`, `summaries/why-check-plan-arc-01.md`

> 플롯 단계에서 구멍 1개를 막는 비용은 문장 1개다. 같은 구멍이 집필 후 발견되면 장면 재작성이 필요하다. 이 단계가 가장 비용 효율이 높은 검증이다.

### 4단계: 교차 검증
생성된 설정 파일들을 에이전트 3팀으로 병렬 검증한다. 모순이 발견되면 즉시 수정한다.

**팀 A (사실 관계 대조):**
- 캐릭터 능력/출신이 세계관에 존재하는가 (03-characters ↔ 04-worldbuilding)
- 플롯이 요구하는 역할을 수행할 캐릭터가 있는가 (master-outline ↔ 03-characters)
- 호칭 매트릭스가 캐릭터 관계와 일치하는가 (CLAUDE.md 8.1 ↔ 03-characters)
- 복선 설치/회수 시점이 아크 구성과 정합하는가 (foreshadowing ↔ master-outline)
- CLAUDE.md 연속성 항목과 .claude/agents/unified-reviewer.md의 continuity 모드 항목이 일치하는가

**팀 B (서사 실현성):**
- 핵심 약속 3가지가 아크 구성으로 실현 가능한가 (CLAUDE.md 1.1 ↔ master-outline)
- 플롯이 금지 사항을 위반하지 않는가 (CLAUDE.md 5 ↔ master-outline)
- CLAUDE.md의 분량 목표와 **선택한 writer prompt**가 일치하는가 (`writer_model: codex`면 `codex-writer.md`, `claude`면 `claude-writer.md`)
- .claude/agents/unified-reviewer.md가 소설 고유 톤/장르를 반영하는가

**팀 C (표기/일관성):**
- 문체/단위/외래어 규칙이 세계관 시대 배경과 맞는가 (01-style-guide ↔ 04-worldbuilding)
- 07-periodic.md 항목 수가 CLAUDE.md 참조와 일치하는가
- illustration 플래그가 관련 파일들과 일치하는가
- EPISODE_META 고유 필드가 continuity 설정에 반영되었는가

검증 완료 후 모순 0건이면 5단계로. **만약 4단계에서 plot 파일(master-outline, arc-01)이 수정되었다면, 3.5단계 `/oag-check plan` + `/why-check plan`을 해당 파일에 대해 1회 재실행한다.**

### 5단계: git commit (2단계)
셋업은 /root/novel/ 에서 실행되므로 두 곳에 각각 커밋한다.

**5-A: 소설 폴더 독립 레포 생성**
소설 폴더는 상위 레포의 .gitignore로 제외되어 있으므로 독립 git 레포로 초기화한다.
```bash
cd no-title-XXX && git init && git add -A && git commit -m "프로젝트 초기 셋업"
```

**5-B: 상위 레포에 등록 커밋**
상위 레포에서는 config.json, vercel.json, .gitignore만 커밋한다.
```bash
cd /root/novel && git add config.json vercel.json .gitignore && git commit -m "소설명(no-title-XXX) 등록"
```

**주의: 에피소드 집필은 하지 않는다. 프로젝트 셋업(설정 파일 생성 + 검증)까지만 수행.**
```

---

## 프롬프트 2: 컨셉 확정형

이미 쓰고 싶은 소설이 정해져 있을 때. 바로 셋업으로 진행한다.

```
claude-codex-novel-templates-hybrid/ 를 참고해서 새 소설 프로젝트를 만들어줘.

## 소설 정보

- 제목: [제목]
- 부제: [부제 또는 없음]
- 장르: [장르]
- 톤: [톤앤무드]
- 한줄 소개: [한줄 소개]
- 배경: [시대/세계관 간단 설명]
- 분량: [에피소드 목표 분량]
- 총 화수: [목표 화수]

## 주인공

- 이름: [이름]
- 설명: [성격, 외형, 배경 등]

## 핵심 컨셉

[2~3줄로 이 소설의 핵심을 설명]

## 진행

1. 위 정보를 바탕으로 주요 캐릭터 3~5명을 제안해줘 (주인공 포함).
2. 아크 구성과 핵심 약속 3가지를 제안해줘.
3. story-consultant 에이전트(`claude-codex-novel-templates-hybrid/.claude/agents/story-consultant.md`)로 컨셉 평가를 수행해줘 (7개 관점). GO가 나오면 다음으로.
4. 내가 OK하면 claude-codex-novel-templates-hybrid/의 구조대로 전체 파일을 생성해줘.
   - CLAUDE.md {{PLACEHOLDER}} 전부 채우기
   - settings/ 파일 전부 실제 내용으로 작성
   - plot/ 초기 설계
   - batch-supervisor.md 생성
   - config.json 등록
5. 파일 생성 후, **Writer Runtime 정밀 검토**:
   - `writer_model: codex`면 `ask_gpt` MCP, `writer_model: claude`면 Claude writer 관점으로 검토
   - `01-style-guide.md` → `03-characters.md` → `02-episode-structure.md` 순서로 검토
   - 파일별 GO/REVISE 판정. REVISE 시 수정 후 1회 재실행
6. 플롯 사전 검증 2종 실행:
   - `/oag-check plan` (동기 갭 — 먼저): PLANNING GAP/MOTIVATION GAP 발견 시 즉시 수정
   - `/why-check plan` (설명 갭 — oag 수정 후): PLANNING GAP 발견 시 즉시 수정
7. 에이전트 3팀으로 교차 검증 수행. 모순 발견 시 즉시 수정.
8. 검증 통과 후 git commit (2단계):
   - 소설 폴더: git init + 전체 커밋 (독립 레포)
   - 상위 레포: config.json + vercel.json + .gitignore만 커밋
9. **에피소드 집필은 하지 않는다. 셋업 + 검증까지만.**
```

---

## 프롬프트 3: 풀 자동 (최소 개입)

장르만 던지면 Claude가 알아서 전부 결정한다. 빠르게 테스트하고 싶을 때.

```
claude-codex-novel-templates-hybrid/ 를 참고해서 새 [장르] 소설을 처음부터 끝까지 자동으로 셋업해줘.

조건:
- 장르: [장르]
- 톤: [자유 / 또는 지정]
- 총 화수: [목표 화수]
- 에피소드 분량: [목표 분량 또는 "기본값"]

나한테 물어보지 말고 네가 판단해서 전부 결정해.
제목, 캐릭터, 세계관, 아크 구성, 모든 설정 파일까지 한번에 만들어줘.
프롬프트 1의 3~5단계 절차 전체를 수행하고, 3.7단계 Writer Runtime 정밀 검토 + /oag-check plan + /why-check plan + 교차 검증도 수행해.
모순 발견 시 즉시 수정.
검증 통과 후 git commit 2단계 (소설 폴더 독립 레포 + 상위 레포 등록).
에피소드 집필은 하지 마. 셋업 + 검증만.

다 끝나면 "어떤 소설을 만들었는지" + "검증 결과 요약"을 보여줘.
```

---

## 프롬프트 4: 기존 소설 복제 (실험용)

같은 설정으로 다른 AI가 쓰게 하고 싶을 때. 모델 비교 테스트용.

```
no-title-[원본 번호]/ 소설의 설정을 복제해서 새 프로젝트를 만들어줘.

## 복제 대상
- 원본: no-title-[번호]
- 복제할 것: CLAUDE.md, settings/, .claude/agents/ (unified-reviewer.md, full-audit.md, narrative-reviewer.md), `.claude/prompts/` 전체(writer/fixer 양 모드), `.claude/commands/` 폴더, plot/master-outline.md, plot/foreshadowing.md
- 복제하지 않을 것: chapters/ (빈 폴더만), summaries/ (빈 템플릿만), EDITOR_FEEDBACK*

## 변경 사항
- 새 폴더명: no-title-[새 번호] (자동 결정)
- CLAUDE.md 폴더 구조의 경로를 새 폴더명으로 업데이트
- author를 "[작성자명]"으로 변경 (실험작 태그 트리거용이면 "다슬기")
- batch-supervisor.md 생성 (`writer_model` + `WRITER_CMD` 반영)
  예시: `writer_model: codex` + `"codex --dangerously-bypass-approvals-and-sandbox"`, `writer_model: claude` + `"claude"`

## 완료 후
- 교차 검증 (프롬프트 1의 4단계) — 복제 과정에서 경로/참조가 깨지지 않았는지 확인
- git commit 2단계:
  - 소설 폴더: git init + 전체 커밋 (독립 레포)
  - 상위 레포: config.json + vercel.json + .gitignore만 커밋
- 최종 상태 요약
- **에피소드 집필은 하지 않는다. 셋업까지만.**
```

---

## 셋업 후 집필 시작 (Hybrid)

프로젝트 생성이 완료되면, **CLAUDE.md의 `writer_model`에 맞는 writer 세션 + Claude supervisor/review 세션** 구조로 집필을 시작한다:

```bash
# 상위 폴더에서 감독자(Claude) 실행
cd /root/novel && claude
# → "no-title-XXX/batch-supervisor.md 대로 수행"
```

Claude supervisor가 tmux 세션에서 선택한 writer runtime을 실행하고 자동 관리한다.
`WRITER_CMD`는 `writer_model`에 맞춘다. 예: codex mode는 `codex --dangerously-bypass-approvals-and-sandbox`, claude mode는 `claude`.

---

## 참고

- 시나리오 제안 단계에서 마음에 드는 게 없으면 "다시" 또는 "이런 방향으로" 라고 하면 된다.
- 2단계에서 캐릭터/플롯을 수정 요청할 수 있다. OK할 때까지 3단계로 넘어가지 않는다.
- 모든 프롬프트에서 `[대괄호]` 안의 내용을 실제 값으로 바꿔서 사용한다.
- 셋업 완료 후 settings/ 파일을 직접 수정해도 된다. CLAUDE.md가 일반 원칙이고, settings/의 세부 규칙이 구체화/보정한다 (settings/의 구체적 규칙이 CLAUDE.md의 일반 원칙보다 우선).
- 4단계 교차 검증에서 발견된 모순은 즉시 수정된다. 집필 중 설정 충돌을 사전에 방지하는 핵심 단계다.
