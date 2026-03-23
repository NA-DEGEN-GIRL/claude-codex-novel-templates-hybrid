# Codex Writer Prompt Template

> 이 파일은 batch-supervisor가 Codex(GPT 5.4) tmux 세션에 전송하는 집필 프롬프트의 템플릿이다.
> Codex는 본문 생성만 담당한다. 리뷰, summary, EPISODE_META, git은 Claude supervisor가 처리한다.
>
> **전송 프로토콜**: `tmux send-keys -l '...'` 후 **3초 대기** 후 `Enter`. 즉시 Enter는 줄바꿈만 됨.

---

## Chunk Start Prompt (첫 화 또는 새 세션)

```
목표: {N}화를 작성해 chapters/{arc}/chapter-{NN}.md에 저장한다.

[읽기 — 반드시]
0. .claude/prompts/codex-writer-role.md — 네 역할과 문체 원칙. 반드시 먼저 읽어라.
1. CLAUDE.md — 소설 헌법. 금지사항(§5), 호칭 매트릭스(§8) 확인.
2. settings/01-style-guide.md — §0 Voice Profile(서술 온도, 대표 문단) 반드시 따를 것.
3. settings/03-characters.md — 등장인물 성격/말투/대표 대사.
4. settings/05-continuity.md — Continuity Invariants(불변 조건 표) 반드시 대조.
5. plot/{arc}.md — 이번 화의 아크 역할과 다음 2~3화 런웨이.
6. 직전 화(chapters/{arc}/chapter-{NN-1}.md) 마지막 2~3문단 — 오프닝 연결.

[MCP 도구 — 집필 전 필수]
- `novel-editor` MCP의 `compile_brief(novel_dir="{{NOVEL_DIR}}", episode_number={N})` 호출하여 압축 맥락 확인.

사용 가능한 MCP 서버:
- `novel-editor`: compile_brief, review_episode
- `novel-calc`: char_count, calculate, date_calc, travel_estimate 등
- `novel-hanja`: hanja_lookup, hanja_search, hanja_verify
- `novel-naming`: naming_check

[읽기 — 필요시]
- settings/04-worldbuilding.md — 세계관/시대 용어 확인 (비현대 배경)

[집필 전 미니 계획 — 반드시]
초안 전에 아래를 짧게 정리한다 (터미널 출력 불필요, 내부 정리용):
- 이번 화의 기능: 이 화가 아크 안에서 무엇을 수행하는가?
- 주요 장면 아웃라인: 3~6개, 각 장면의 {목적, 등장인물, 톤}
- 감정 앵커: 최소 1개 장면에서 인물의 개인적 이해관계가 드러나는 순간
- WHY/HOW 질문: 이 화가 만드는 핵심 질문 1~2개. 답변됨/미스터리 유예/답 없음 판정.
- 엔딩 훅 유형: 직전 화와 다른 유형인지 확인.
- 반복 회피: compile_brief의 최근 에피소드 상세와 대조. 오프닝/엔딩/장면 구조가 직전 2~3화와 겹치지 않는지.

[작성 규칙]
- **Voice Profile 우선**: 더 표준적이거나 더 매끈한 문장으로 수렴시키지 않는다. settings/01-style-guide.md §0의 보이스를 우선한다.
- 한국어 본문만 작성. 마크다운 제목(# {N}화 - {제목})으로 시작.
- 장면 구분: ***
- 분량: {MIN}~{MAX}자. 초안 완성 후 `novel-calc` MCP의 `char_count(file_path="chapters/{arc}/chapter-{NN}.md")`로 확인.
- 수치 검증 필요 시 `novel-calc` MCP 활용: `date_calc`, `calculate`, `travel_estimate` 등. 단, 계산 결과를 대사/서술에 그대로 넣지 말 것 — 인간적 어림으로 변환.
- 비현대 배경: 외래어/아라비아 숫자 금지. 한자어/한글 수사 사용.
- 메타 표현 금지: "N화에서", "독자 여러분", "프롤로그에서"
- 한자 병기: 첫 등장 시 음+한자 병기 (예: 내공(內功)). 이후 한국어만. `hanja_lookup(text="용어")` MCP로 검증. 모르면 한글만 쓰고 넘어가라 — review가 보정.

[초안 후 자기점검]
연속성 (치명적):
- 즉흥 설정 추가하지 않았는가? (settings에 없는 인물/능력/장소)
- POV 인물이 모르는 정보를 서술에 사용하지 않았는가?
- 불변 조건 표의 나이/시점/사건과 본문 수치가 일치하는가?

서사 기능:
- 계획한 각 장면이 의도한 기능을 실제로 수행했는가?
- WHY/HOW 질문에 대해 독자가 최소한 읽힐 수준의 답이 있는가?
- 첫 문단이 바로 장면을 붙잡는가?
- 엔딩 훅이 직전 화와 같은 유형이 아닌가?
- 같은 감정/정보를 반복 설명하지 않았는가?

한국어 1회 훑기:
- 번역투, 약한 동사(했다/되었다/있었다) 과다 반복, 어미 반복
- 서수 체계("두 명째" ❌ → "둘째" ✅), 격틀/호응, 외래어 확인.

[금지]
- summaries/* 수정 금지
- EPISODE_META 삽입 금지
- git commit 금지
- config.json 수정 금지
- 질문하지 말고 자율 완료

[완료]
- 파일 저장 후 터미널에 다음 한 줄만 출력:
WRITER_DONE chapter-{NN}.md
```

---

## Continuation Prompt (이전 화 컨텍스트 유지 중)

```
이어서 {N}화를 집필해줘.
- novel-editor MCP의 compile_brief(novel_dir="{{NOVEL_DIR}}", episode_number={N}) 먼저 호출.
- 직전 화 컨텍스트를 유지하되, plot/{arc}.md를 다시 확인하라.
- 직전 화 마지막 2~3문단에서 오프닝 연결.
- 파일명: chapters/{arc}/chapter-{NN}.md
- 한국어 본문만 작성. EPISODE_META/summary 불필요.
- 집필 전 미니 계획: 이번 화 기능, 장면 아웃라인, 감정 앵커, WHY/HOW, 엔딩 훅 유형, 반복 회피.
- 초안 후 novel-calc char_count로 분량 확인. 한자는 novel-hanja hanja_lookup으로 검증.
- 초안 후 자기점검: 연속성(즉흥 설정, POV 경계, 불변 조건) + 서사 기능(장면 기능 수행, WHY/HOW, 첫 문단 견인력, hook 중복, 반복 설명) + 한국어 1회 훑기(번역투, 약한 동사, 어미 반복, 서수/외래어).
- 완료 후: WRITER_DONE chapter-{NN}.md
```

---

## Partial Rewrite Prompt (Claude supervisor가 prose 문제 발견 시)

```
chapters/{arc}/chapter-{NN}.md의 {시작줄}~{끝줄} 구간을 재작성해줘.
문제: {문제 설명}
방향: {수정 방향}
나머지는 건드리지 마라. 해당 구간만 교체.
완료 후: REWRITE_DONE chapter-{NN}.md {시작줄}-{끝줄}
```
