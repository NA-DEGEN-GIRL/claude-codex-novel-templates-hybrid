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

tmux pane을 폴링해서 `WRITER_DONE ...` 또는 `FIX_DONE ...` 같은 sentinel 문자열을 기다린다. supervisor가 고정 `sleep`만 길게 두지 않고 더 빨리 다음 단계로 넘어갈 때 쓴다.

```bash
bash scripts/tmux-wait-sentinel write-001 "WRITER_DONE chapter-05.md" 1800 2 200
bash scripts/tmux-wait-sentinel write-001 "FIX_DONE chapter-05" 600 1 120
```

### `scripts/tmux-send-codex`

Codex tmux 세션에 프롬프트를 보내고, `2초` 안에 `Working` 또는 새 응답 블록이 뜨는지 확인한다. 둘 다 안 보이면 `Enter`를 한 번만 다시 보내고 재확인한다.

```bash
bash scripts/tmux-send-codex write-001 "continue" 2 60
```

### `scripts/tmux-send-claude`

Claude tmux 세션에 프롬프트를 보내고, `2초` 안에 새 응답 블록(`● ...`)이 뜨거나 입력 프롬프트 줄이 사라지는지 확인한다. 둘 다 없으면 `Enter`를 한 번만 다시 보내고 재확인한다. `claude mode` writer 세션과 review 세션 모두 이 헬퍼를 쓸 수 있다.

```bash
bash scripts/tmux-send-claude write-001-review "REVIEW_DONE chapter-05 를 마지막 줄에 출력해." 2 80
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
- `tmux-send-codex`는 Codex 전용 전송 확인 헬퍼다. `Working`이 너무 짧게 지나가는 경우를 위해 새 응답 블록도 성공 신호로 본다. 둘 다 없으면 재전송 1회 후 supervisor가 직접 pane을 확인한다.
- `claude mode` writer 세션과 review 세션 프롬프트 전송은 `tmux-send-claude`, 완료 대기는 `tmux-wait-sentinel` 조합을 기본으로 쓴다.
- 이 옵션은 외부 샌드박스나 사용자가 환경을 통제하고 있을 때만 쓰는 것이 맞다.
