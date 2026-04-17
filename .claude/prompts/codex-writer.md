# Codex Writer Prompt Template

> 이 파일은 batch-supervisor가 Codex tmux 세션에 전송하는 기본 집필 프롬프트 템플릿이다.
> writer는 **장면을 분명하고 자연하게 쓰는 것**에 집중한다. 세밀한 감사는 review 단계가 맡는다.
>
> **Phase 1 diet (2026-04-17)**: 집필 전 메모 5개 → 3개, Drafting Surface 9개 → 4원칙, 자기점검 9개 → 3개로 압축. claude-writer.md와 동기화. 자세한 근거와 롤백: `docs/updates/phase-1-hot-path.md`.

---

## Chunk Start Prompt (첫 화 또는 새 세션)

```
목표: {N}화를 작성해 chapters/{arc}/chapter-{NN}.md에 저장한다.

[읽기 — 반드시]
0. .claude/prompts/codex-writer-role.md — 역할과 공통 문체 원칙
1. CLAUDE.md — 금지사항, 시대감, 핵심 약속
2. settings/03-characters.md — 핵심 인물의 대표 대사, 관계별 말투 규칙, 대화 대비축
3. CLAUDE.md §8.1 호칭/어투 매트릭스 — 이번 화에서 실제로 만나는 관계축 확인
4. plot/{arc}.md — 이번 화의 기능과 다음 2~3화 런웨이
5. 직전 화 마지막 장면 — 마지막 장면 전체 또는 마지막 8~12문단 (최소 2~3문단). 오프닝 연결용.

[MCP — 집필 전 필수]
- `novel-editor` MCP의 `compile_brief(novel_dir="{{NOVEL_DIR}}", episode_number={N})` 호출
- MCP는 직접 호출한다. `scripts/*` wrapper를 기본 경로로 쓰지 않는다.

[집필 전 메모 — 3개만]
`compile_brief`의 `Live Drafting Cues`가 공개/비공개 정보, 보이스 압력, 주요 장면, 감정 앵커를 이미 제공한다. 아래 3개만 직접 정리한다.
1. 이번 화의 기능 1줄
2. 직전 화에서 반드시 이어받을 carry-forward 3~5개 (위치/시간/부상/공개 정보/미완 조치)
3. 이번 화의 엔딩 훅 1개

[Drafting Surface — 4원칙]
1. **선명도 우선**: 잘 쓰려 하기보다 **잘 읽히게**. 누가 무엇을 보고, 어떻게 판단하고, 무엇이 바뀌는지가 문장에서 바로 읽혀야. 첫 문장과 전투/위기 장면에서 특히. 숫자를 세는 듯한 문장, 결과만 요약하는 문장, 몸으로 바로 그려지지 않는 문장은 피한다.
2. **평이함**: 뜻은 통하지만 한국어 결합이 이상한 문장은 버린다. 평이한 문장이 더 정확하면 그쪽을 택한다.
3. **대사 위계 먼저**: 인물 둘 이상 장면에서 기본 캐릭터 톤보다 화자-청자 관계 register를 먼저 맞춘다. 부모/연장자/사부/상급자 앞에서는 관계가 읽혀야 한다.
4. **carry-forward 존중**: 직전 화 미완 조치, 공간 공유 인물, 오프스크린 완료 처리 금지. 보고/허락/안심/소문 확산/관아 전달/관계 변화는 본문에 보인 경우에만 이번 화의 기정사실로 사용한다.

[Hard Rules — 위반 금지]
- 한국어 본문만 작성. 마크다운 제목(# {N}화 - {제목})으로 시작.
- 장면 구분: ***
- 분량: {MIN}~{MAX}자. 초안 후 `novel-calc` MCP의 `char_count`로 확인.
- 본문과 대사에서 `1화에서`, `3화에서`, `프롤로그에서`, `에필로그에서`, `1부에서` 같은 메타 참조를 쓰지 않는다.
- 과거 사건은 화수/부/프롤로그 같은 메타 단위가 아니라 날짜, 장소, 사건명, 인물 기억으로만 지칭한다.
- 비현대 배경이면 외래어/아라비아 숫자를 쓰지 않는다 (회귀/환생 POV의 현대 내면 독백은 예외).

[Review Surface — 지금 다 짊어지지 말 것]
- summary/meta/git/external review는 review 단계가 맡는다.
- §0.6~§0.8 drift 판정까지 초안 단계에서 한꺼번에 해결하려 들지 않는다. 문장이 멈추면 `Live Drafting Cues`와 장면 기능으로 복귀한다.
- 반복 설명 / 결합 자연성 / 전투 선명도 / 공간 공유 인물 / 대사 평탄화 / 호칭 위계 등 **세부 품질은 unified-reviewer 전담**. 초안에서 과도하게 신경 쓰지 말 것.

[초안 후 자기점검 — 3개만]
1. 분량이 {MIN}~{MAX}자 범위 안인가? (`novel-calc char_count`로 확인)
2. 이번 화의 기능이 실제로 수행되었는가?
3. 오프스크린 점프 / carry-forward 누락이 없는가?

[금지]
- summaries/* 수정 금지
- EPISODE_META 삽입 금지
- git commit 금지
- config.json 수정 금지
- 질문하지 말고 자율 완료 (판단 모호한 표기는 `summaries/style-lexicon.md` 우선 참조. 없으면 한자어/전통어 우선 선택)

[완료]
- run nonce: `{RUN_NONCE}`
- 완료 문자열 접두: `WRITER_DONE chapter-{NN}.md`
- **`{NN}`은 반드시 2자리 0-padded** (예: `chapter-05.md`, `chapter-12.md`, `chapter-101.md`은 3자리 OK)
- chapter 저장 후 `mkdir -p tmp/sentinels && printf '%s\n' "WRITER_DONE chapter-{NN}.md :: run={RUN_NONCE}" > tmp/sentinels/chapter-{NN}.done` 실행
- 마지막 줄 exact 형식은 `<접두> :: run=<run nonce>` 이다.
- 위 형식으로 만든 완성 문자열은 마지막 줄에만 1회 출력하고, 계획/메모/자기점검/중간 보고/오류 설명에 다시 쓰지 말 것.
```

---

## Continuation Prompt (이전 화 컨텍스트 유지 중)

```
이어서 {N}화를 집필해줘.
- `compile_brief(novel_dir="{{NOVEL_DIR}}", episode_number={N})` 먼저 호출.
- plot/{arc}.md와 직전 화 마지막 장면을 다시 확인. 마지막 장면 전체 또는 마지막 8~12문단 (최소 2~3문단) 우선.
- 파일명: chapters/{arc}/chapter-{NN}.md (NN은 2자리 0-padded).
- `Live Drafting Cues`를 먼저 읽고, 아래 3개만 직접 정리한다:
  1. 이번 화 기능 1줄
  2. 직전 화 carry-forward 3~5개
  3. 엔딩 훅 1개
- Drafting Surface 4원칙(선명도·평이함·대사 위계·carry-forward 존중)을 먼저 따르고, Hard Rules는 위반 금지선으로만 유지한다.
- 세부 품질(반복/결합/전투 선명도/공간 공유 인물/대사 평탄화/호칭 위계)은 unified-reviewer 전담. 초안에서 과도하게 신경 쓰지 말 것.
- `settings/03-characters.md`와 `CLAUDE.md §8.1` 기준으로 관계별 register는 먼저 맞춘다.
- 오프스크린 완료 처리 금지: 보고/허락/안심/소문 확산/관아 전달/관계 변화는 본문에 보였을 때만 이번 화 기정사실로.
- 초안 후 자기점검 3개만: 분량 / 기능 수행 / carry-forward 점프.
- run nonce: `{RUN_NONCE}`
- 완료 문자열 접두: `WRITER_DONE chapter-{NN}.md` ({NN}은 2자리 0-padded)
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
- 완료 문자열 접두: `REWRITE_DONE chapter-{NN}.md {시작줄}-{끝줄}` ({NN}은 2자리 0-padded)
- 마지막 줄 exact 형식은 `<접두> :: run=<run nonce>` 이다.
```
