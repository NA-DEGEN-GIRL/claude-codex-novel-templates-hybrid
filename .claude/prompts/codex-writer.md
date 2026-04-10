# Codex Writer Prompt Template

> 이 파일은 batch-supervisor가 Codex tmux 세션에 전송하는 기본 집필 프롬프트 템플릿이다.
> writer는 **장면을 분명하고 자연하게 쓰는 것**에 집중한다. 세밀한 감사는 review 단계가 맡는다.

---

## Chunk Start Prompt (첫 화 또는 새 세션)

```
목표: {N}화를 작성해 chapters/{arc}/chapter-{NN}.md에 저장한다.

[읽기 — 반드시]
0. .claude/prompts/codex-writer-role.md — 역할과 공통 문체 원칙
1. CLAUDE.md — 금지사항, 시대감, 핵심 약속
2. plot/{arc}.md — 이번 화의 기능과 다음 2~3화 런웨이
3. 직전 화 마지막 2~3문단 — 오프닝 연결

[MCP — 집필 전 필수]
- `novel-editor` MCP의 `compile_brief(novel_dir="{{NOVEL_DIR}}", episode_number={N})` 호출
- MCP는 직접 호출한다. `scripts/*` wrapper를 기본 경로로 쓰지 않는다.

[집필 전 메모 — 짧게]
- `compile_brief`의 `Live Drafting Cues`를 먼저 훑고 아래 5개만 정리
- 이번 화의 기능 1줄
- 오프닝에서 바로 이어질 사실 2~4개
- 이번 화에서 가장 강하게 밀 보이스/관계 압력 1~2개
- 주요 장면 3~5개
- 이번 화의 엔딩 훅 1개

[Drafting Surface — 지금 밀 것]
- 문장은 잘 쓰려 하기보다 **잘 읽히게** 쓴다.
- 분위기보다 장면의 선명도를 우선한다. 누가 무엇을 보고, 어떻게 판단하고, 무엇이 바뀌는지가 바로 읽혀야 한다.
- 첫 문장과 장면 전환 첫 문장은 멋을 부리기보다 상황을 바로 붙잡는다.
- 뜻은 통하지만 한국어 결합이 이상한 문장은 버린다. 평이한 문장이 더 정확하면 그쪽을 택한다.
- 전투/위기 장면에서는 감상적 압축보다 행동의 선명도를 우선한다. 숫자를 세는 듯한 문장, 결과만 요약하는 문장, 몸으로 바로 그려지지 않는 문장은 피한다.
- 인물 둘 이상 장면에서는 대사가 상황, 관계, 숨은 의도 중 최소 하나를 직접 운반해야 한다.
- 같은 공간의 이름 있는 인물을 투명인간처럼 지우지 않는다.

[Hard Rules — 위반 금지]
- 한국어 본문만 작성. 마크다운 제목(# {N}화 - {제목})으로 시작.
- 장면 구분: ***
- 분량: {MIN}~{MAX}자. 초안 후 `novel-calc` MCP의 `char_count`로 확인.
- 본문과 대사에서 `1화에서`, `3화에서`, `프롤로그에서`, `에필로그에서`, `1부에서` 같은 메타 참조를 쓰지 않는다.
- 과거 사건은 화수/부/프롤로그 같은 메타 단위가 아니라 날짜, 장소, 사건명, 인물 기억으로만 지칭한다.
- 비현대 배경이면 외래어/아라비아 숫자를 쓰지 않는다.

[Review Surface — 지금 다 짊어지지 말 것]
- summary/meta/git/external review는 review 단계가 맡는다.
- §0.6~§0.8 drift 판정까지 초안 단계에서 한꺼번에 해결하려 들지 않는다. 문장이 멈추면 `Live Drafting Cues`와 장면 기능으로 복귀한다.

[초안 후 자기점검 — 짧게]
- 이번 화의 기능이 실제로 수행되었는가?
- 첫 문단이 바로 장면을 붙잡는가?
- 같은 감정/정보를 반복 설명하지 않았는가?
- 전투/위기 장면이 숫자 세기처럼 딱딱하지 않은가?
- 뜻은 통하지만 결합이 이상한 문장이 없는가?
- 같은 공간의 이름 있는 인물을 빠뜨리지 않았는가?
- 실제 글자를 세는 맥락이 아니면 호칭·대답·부름을 `두 글자`처럼 처리하지 않았는가?

[금지]
- summaries/* 수정 금지
- EPISODE_META 삽입 금지
- git commit 금지
- config.json 수정 금지
- 질문하지 말고 자율 완료

[완료]
- run nonce: `{RUN_NONCE}`
- 완료 문자열 접두: `WRITER_DONE chapter-{NN}.md`
- chapter 저장 후 `mkdir -p tmp/sentinels && printf '%s\n' "WRITER_DONE chapter-{NN}.md :: run={RUN_NONCE}" > tmp/sentinels/chapter-{NN}.done` 실행
- 마지막 줄 exact 형식은 `<접두> :: run=<run nonce>` 이다.
- 위 형식으로 만든 완성 문자열은 마지막 줄에만 1회 출력하고, 계획/메모/자기점검/중간 보고/오류 설명에 다시 쓰지 말 것.
```

---

## Continuation Prompt (이전 화 컨텍스트 유지 중)

```
이어서 {N}화를 집필해줘.
- `compile_brief(novel_dir="{{NOVEL_DIR}}", episode_number={N})` 먼저 호출.
- plot/{arc}.md와 직전 화 마지막 2~3문단을 다시 확인.
- 파일명: chapters/{arc}/chapter-{NN}.md
- `Live Drafting Cues`를 먼저 읽고, 이번 화 기능/직결 사실/보이스 압력/주요 장면/엔딩 훅만 짧게 정리하고 집필.
- Drafting Surface를 먼저 따르고, Hard Rules는 위반 금지선으로만 유지한다.
- 잘 쓰려 하기보다 잘 읽히게 쓴다. 첫 문장, 전투 문장, 장면 전환 문장을 특히 평이하고 선명하게 유지한다.
- 초안 후 분량 확인 + 기능 수행/반복 설명/결합 자연성/전투 선명도/공간 공유 인물만 짧게 점검.
- run nonce: `{RUN_NONCE}`
- 완료 문자열 접두: `WRITER_DONE chapter-{NN}.md`
- chapter 저장 후 `mkdir -p tmp/sentinels && printf '%s\n' "WRITER_DONE chapter-{NN}.md :: run={RUN_NONCE}" > tmp/sentinels/chapter-{NN}.done` 실행
- 마지막 줄 exact 형식은 `<접두> :: run=<run nonce>` 이다.
- 위 형식으로 만든 완성 문자열은 마지막 줄에만 1회 출력하고, 중간에 다시 쓰지 말 것.
```

---

## Partial Rewrite Prompt

```
chapters/{arc}/chapter-{NN}.md의 {시작줄}~{끝줄} 구간을 재작성해줘.
문제: {문제 설명}
방향: {수정 방향}
나머지는 건드리지 마라. 해당 구간만 교체.
- run nonce: `{RUN_NONCE}`
- 완료 문자열 접두: `REWRITE_DONE chapter-{NN}.md {시작줄}-{끝줄}`
- 마지막 줄 exact 형식은 `<접두> :: run=<run nonce>` 이다.
```
