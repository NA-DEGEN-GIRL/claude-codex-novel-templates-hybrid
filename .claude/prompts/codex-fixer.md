# Codex Fixer Prompt Template

> Claude supervisor가 진단한 문제를 Codex(GPT 5.4)가 문체를 유지하며 수정한다.
> Claude는 fix-spec 파일을 생성하고, Codex는 그 파일을 읽고 수정만 수행한다.
>
> **전송 프로토콜**: `tmux send-keys -l '...'` 후 **3초 대기** 후 `Enter`.

---

> **이 파일에는 `patch_class: micro`, `local`, `rewrite`가 모두 온다.**
> 문체 일관성을 위해 사실관계 micro-patch 포함 모든 텍스트 수정은 Codex가 수행한다.
> `hold`만 제외 (다음 사이클 이관).

## Fix Prompt (에피소드 단위 배치)

```
tmp/fix-specs/chapter-{NN}.md 를 읽고 해당 에피소드를 수정해줘.

[규칙]
- fix-spec에 적힌 수정 목표와 제약만 따른다.
- must_keep 항목은 반드시 보존한다.
- must_avoid 항목은 반드시 회피한다.
- 수정 범위(line_start~line_end) 밖의 문장은 건드리지 않는다. 다만 fix-spec에 적힌 원문 앵커를 먼저 대조해 실제 수정 대상을 확인한다.
- 기존 문체, 리듬, 캐릭터 보이스를 유지한다.
- 핵심 설정, 중요 인물, 새 능력, 새 세력, 새 장소를 멋대로 추가하지 않는다.
- 동석 인물 처리나 장면 상식선을 맞추기 위한 최소한의 생활 조연 표기는 허용된다. 단, fix-spec 목적을 넘는 비중 확대나 새 축 생성은 금지한다.
- 수정 후 앞뒤 문맥과 자연스럽게 이어지는지 확인한다.
- 여러 FIX 항목이 있으면 줄번호 드리프트를 피하기 위해 **항상 아래 줄번호부터 위로** 적용한다.
- summaries/*, EPISODE_META, git, config.json은 건드리지 않는다.
- 완료 신호는 `FIX_DONE`만 쓴다. `WRITER_DONE`을 출력하지 않는다.

[완료]
- 파일 직접 수정 후 변경 요약 3줄 이하 출력.
- FIX_DONE chapter-{NN}
```

---

## fix-spec 파일 형식 (`tmp/fix-specs/chapter-{NN}.md`)

> Claude supervisor가 생성. Codex는 이 파일만 읽고 수정.

```markdown
# Fix Spec — {N}화

## 수정 항목

### FIX-001
- **출처**: {checker 이름} (why-check / oag / naturalness / pov-era / scene-logic / repetition / arc-read)
- **심각도**: {HIGH / MEDIUM}
- **위치**: {line_start}~{line_end}행
- **원문 앵커**: "{해당 구간에서 식별 가능한 짧은 원문 한 줄 또는 핵심 구절}"
- **patch_class**: {micro / local / rewrite}
- **문제**: {진단 요약 1-2문장}
- **수정 목표**: {어떻게 바꿔야 하는지 1-2문장}
- **유지 사항**:
  - {톤/리듬/캐릭터 등 보존할 것}
- **금지 사항**:
  - {하지 말아야 할 것}

### FIX-002
...

## 전체 제약
- 이 화의 Voice Profile: {§0 핵심 1줄}
- 이 화의 POV: {인물명}
- 수정 범위 밖 문장 변경 금지
- 여러 항목이 있으면 line_start가 큰 항목부터 처리
```

---

## 단건 긴급 수정 (배치 없이 즉시)

```
chapters/{arc}/chapter-{NN}.md의 {시작줄}~{끝줄}을 수정해줘.
문제: {1줄 진단}
목표: {1줄 수정 방향}
원문 앵커: "{짧은 원문 구절}"
유지: {톤/리듬}
금지: {범위 밖 수정, 새 설정}
완료 후: FIX_DONE chapter-{NN} {시작줄}-{끝줄}
```
