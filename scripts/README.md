# Runtime Helper Scripts

Codex/Claude 런타임의 기본 경로는 **native MCP 직접 호출**이다.
이 템플릿은 `compile_brief`, `novel-calc`, `novel-hanja`, `novel-naming`용 shell wrapper를 두지 않는다.
`scripts/*`는 tmux/session orchestration과 codex mode 편의 실행처럼 **런타임 보조 역할**만 다룬다.

## Available

### `scripts/run-codex-writer`

현재 프로젝트 디렉터리에서 codex mode writer를 전체 승인/샌드박스 우회 모드로 실행한다.

```bash
scripts/run-codex-writer
```

### `scripts/run-codex-supervisor`

`/root/novel`에서 codex 기반 supervisor 세션을 전체 승인/샌드박스 우회 모드로 실행한다.

```bash
/root/novel/claude-codex-novel-templates-hybrid/scripts/run-codex-supervisor
```

### `scripts/tmux-wait-sentinel`

tmux pane을 폴링해서 `WRITER_DONE ... :: run=...`, `FIX_DONE ... :: run=...`, `REVIEW_DONE ... :: run=...` 같은 exact sentinel 문자열을 기다린다. supervisor가 고정 `sleep`만 길게 두지 않고 더 빨리 다음 단계로 넘어갈 때 쓴다.

권장 방식은 supervisor가 매 writer/fixer/review 프롬프트마다 고유한 `RUN_NONCE`를 만들고 exact line을 기다리는 것이다. bare `WRITER_DONE`/`FIX_DONE`/`REVIEW_DONE`만 기다리면 오탐 여지가 커진다.

```bash
bash scripts/tmux-wait-sentinel write-001 "WRITER_DONE chapter-05.md :: run=20260407-ep05-a1c9" 1800 2 200
bash scripts/tmux-wait-sentinel write-001 "FIX_DONE chapter-05 :: run=20260407-fix05-b13e" 600 1 120
bash scripts/tmux-wait-sentinel write-001-review "REVIEW_DONE chapter-05 :: run=20260407-review05-77ac" 30 1 200 1
```

### `scripts/tmux-send-codex`

Codex tmux 세션에 프롬프트를 보내고, `2초` 안에 `Working`뿐 아니라 `Explored`/`Edited`/`Ran`/`Reading`/`Searching` 같은 진행 표시, 새 응답 블록, 또는 입력 프롬프트 소멸을 시작 신호로 본다. 입력창에 prompt가 그대로 남아 있으면 3초 간격으로 최대 4회까지 `Enter`를 더 보내고 재확인한다.

```bash
bash scripts/tmux-send-codex write-001 "continue" 2 60
```

### `scripts/tmux-send-claude`

Claude tmux 세션에 프롬프트를 보내고, `2초` 안에 새 응답 블록(`●`/`⏺`/`•`), `Reading`/`Editing`/`Running` 같은 진행 표시, 또는 입력 프롬프트 줄 소멸을 시작 신호로 본다. 셋 다 없으면 `Enter`를 한 번만 다시 보내고 재확인한다. `claude mode` writer 세션과 review 세션 모두 이 헬퍼를 쓸 수 있다.

```bash
bash scripts/tmux-send-claude write-001-review "run nonce는 20260407-review05-77ac 이다. REVIEW_DONE chapter-05 :: run=20260407-review05-77ac 형식을 마지막 줄에만 출력해." 2 80
```

### `scripts/run-codex-auditor`

현재 프로젝트 디렉터리에서 감사 전용 Codex 세션을 실행한다.

```bash
scripts/run-codex-auditor
```

## Notes

- 이 템플릿은 **MCP wrapper scripts를 의도적으로 두지 않는다.** `compile_brief`, `novel-calc`, `novel-hanja`, `novel-naming`은 native MCP로만 사용한다.
- 경로는 현재 워크스페이스(`/root/novel/...`) 기준으로 고정되어 있다.
- `run-codex-writer` / `run-codex-supervisor` / `run-codex-auditor`는 codex mode 편의 실행용이다. `claude mode`는 `batch-supervisor.md`에 적힌 대로 `unset CLAUDECODE && claude`를 tmux 세션에서 직접 실행한다.
- `tmux-wait-sentinel`은 tmux의 `capture-pane`을 주기적으로 읽어 sentinel 문자열만 판정한다. 본문 품질 판단은 여전히 supervisor가 직접 해야 한다.
- `tmux-send-codex`는 Codex 전용 전송 확인 헬퍼다. `Working`이 너무 짧게 지나가도 `Explored`/`Edited`/`Ran`/`Reading` 같은 진행 표시, 새 응답 블록, 또는 입력 프롬프트 소멸을 성공 신호로 본다. prompt가 입력창에 남아 있으면 3초 간격으로 최대 4회까지 `Enter`를 더 보낸다.
- 장문 writer/review/fix prompt는 pane에 직접 paste하지 말고 `tmp/run-prompts/*.txt`에 저장한 뒤, 세션에는 `그 파일을 읽고 그대로 수행해` 같은 짧은 pointer prompt만 보내는 것을 기본값으로 쓴다.
- `tmux-send-codex`와 `tmux-send-claude`는 둘 다 pane 전체가 아니라 마지막 입력 프롬프트 줄이 **현재 pane 바닥에 실제로 남아 있는지**를 기준으로 미제출 상태를 본다. 오래된 prompt echo나 이전 작업 로그만 남은 경우에는 추가 Enter를 보내지 않는다.
- `tmux-send-claude`도 `●`뿐 아니라 `⏺`, `Reading`, `Editing`, `Running` 등을 시작 신호로 허용한다.
- `claude mode` writer 세션과 review 세션 프롬프트 전송은 `tmux-send-claude`, 완료 대기는 `tmux-wait-sentinel` 조합을 기본으로 쓴다.
- 추천 sentinel 형식은 `WRITER_DONE chapter-{NN}.md :: run={RUN_NONCE}`, `FIX_DONE chapter-{NN} :: run={RUN_NONCE}`, `REVIEW_DONE chapter-{NN} :: run={RUN_NONCE}`처럼 nonce가 붙은 exact 한 줄이다.
- 이 옵션은 외부 샌드박스나 사용자가 환경을 통제하고 있을 때만 쓰는 것이 맞다.
