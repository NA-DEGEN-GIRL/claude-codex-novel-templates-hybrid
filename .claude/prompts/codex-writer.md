# Codex Writer Prompt Template

> 이 파일은 batch-supervisor가 Codex(GPT 5.4) tmux 세션에 전송하는 집필 프롬프트의 템플릿이다.
> Codex는 본문 생성만 담당한다. 리뷰, summary, EPISODE_META, git은 Claude supervisor가 처리한다.
>
> **전송 프로토콜**: `tmux send-keys -l '...'` 후 **3초 대기** 후 `Enter`. 즉시 Enter는 줄바꿈만 됨.

---

## Chunk Start Prompt (첫 화 또는 새 세션)

```
너는 Codex full-auto writer다.
목표: {N}화를 작성해 chapters/{arc}/chapter-{NN}.md에 저장한다.

[읽기 — 반드시]
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

[작성 규칙]
- **Voice Profile 우선**: 더 표준적이거나 더 매끈한 문장으로 수렴시키지 않는다. settings/01-style-guide.md §0의 보이스를 우선한다.
- 한국어 본문만 작성. 마크다운 제목(# {N}화 - {제목})으로 시작.
- 장면 구분: ***
- 분량: {MIN}~{MAX}자. 초안 완성 후 `novel-calc` MCP의 `char_count(file_path="chapters/{arc}/chapter-{NN}.md")`로 확인.
- 수치 검증 필요 시 `novel-calc` MCP 활용: `date_calc`, `calculate`, `travel_estimate` 등. 단, 계산 결과를 대사/서술에 그대로 넣지 말 것 — 인간적 어림으로 변환.
- 비현대 배경: 외래어/아라비아 숫자 금지. 한자어/한글 수사 사용.
- 전생 비교문: 화당 2회 이하
- 메타 표현 금지: "N화에서", "독자 여러분", "프롤로그에서"
- 한자 병기: 첫 등장 시 음+한자 병기 (예: 내공(內功)). 이후 한국어만. `hanja_lookup(text="용어")` MCP로 검증. 모르면 한글만 쓰고 넘어가라 — review가 보정.

[초안 후 자기점검 — 짧게]
- 즉흥 설정 추가하지 않았는가? (settings에 없는 인물/능력/장소)
- POV 인물이 모르는 정보를 서술에 사용하지 않았는가?
- 엔딩 훅이 직전 화와 같은 유형이 아닌가?
- 불변 조건 표의 나이/시점/사건과 본문 수치가 일치하는가?
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
- 직전 화 컨텍스트를 유지하되, plot/{arc}.md를 다시 확인하라.
- 직전 화 마지막 2~3문단에서 오프닝 연결.
- 파일명: chapters/{arc}/chapter-{NN}.md
- 한국어 본문만 작성. EPISODE_META/summary 불필요.
- 초안 후 자기점검: 즉흥 설정, POV 경계, hook 중복, 불변 조건 대조, 서수/외래어.
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
