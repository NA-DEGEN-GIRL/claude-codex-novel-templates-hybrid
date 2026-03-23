# Codex Utility Scripts

Codex/Claude 런타임의 기본 경로는 MCP 직접 호출이다.
이 문서의 `scripts/*`는 수동 셸 테스트와 로컬 디버깅용 보조 스크립트만 다룬다.

## Available

### `scripts/compile-brief`

`compile_brief.py`를 직접 실행한다.

```bash
scripts/compile-brief /root/novel/no-title-001-gpt 7
scripts/compile-brief /root/novel/no-title-001-gpt 7 "윤서하,리라"
```

### `scripts/novel-calc`

`mcp-novel-calc`의 함수들을 CLI처럼 호출한다. 런타임 기본 경로는 아니며, 수동 테스트용이다.

```bash
scripts/novel-calc calculate expression='"1250 * 1.35"'
scripts/novel-calc date_calc date_str='"2026-03-22"' operation='"add"' days=3
scripts/novel-calc char_count file_path='"/root/novel/no-title-001-gpt/chapters/arc-01/chapter-01.md"'
```

JSON 방식도 가능하다.

```bash
scripts/novel-calc date_calc --json '{"date_str":"2026-03-22","operation":"add","days":3}'
```

### `scripts/novel-hanja`

`mcp-novel-hanja`의 함수들을 CLI처럼 호출한다. 런타임 기본 경로는 아니며, 수동 테스트용이다.

```bash
scripts/novel-hanja hanja_lookup text='"天外歸還"'
scripts/novel-hanja hanja_search reading='"검"' meaning_hint='"칼"'
scripts/novel-hanja hanja_verify text='"천외귀환(天外歸還)"' novel_id='"no-title-001-gpt"'
```

### `scripts/run-codex-writer`

현재 프로젝트 디렉터리에서 Codex를 전체 승인/샌드박스 우회 모드로 실행한다.

```bash
scripts/run-codex-writer
```

### `scripts/run-codex-supervisor`

`/root/novel`에서 supervisor Codex를 전체 승인/샌드박스 우회 모드로 실행한다.

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

Claude tmux 세션에 프롬프트를 보내고, `2초` 안에 새 응답 블록(`● ...`)이 뜨거나 입력 프롬프트 줄이 사라지는지 확인한다. 둘 다 없으면 `Enter`를 한 번만 다시 보내고 재확인한다.

```bash
bash scripts/tmux-send-claude write-001-review "REVIEW_DONE chapter-05 를 마지막 줄에 출력해." 2 80
```

### `scripts/run-codex-auditor`

현재 프로젝트 디렉터리에서 감사 전용 Codex 세션을 실행한다.

```bash
scripts/run-codex-auditor
```

## Notes

- 이 스크립트들은 MCP 직접 호출을 대체하지 않는다. MCP를 쓰기 어려운 셸 상황에서만 보조적으로 쓴다.
- 이 스크립트들은 MCP 연결 없이 로컬 import 방식으로 동작한다.
- `mcp` 파이썬 패키지가 설치되어 있어야 서버 모듈 import가 된다.
- 경로는 현재 워크스페이스(`/root/novel/...`) 기준으로 고정되어 있다.
- `run-codex-writer` / `run-codex-supervisor` / `run-codex-auditor`는 승인 프롬프트를 최대한 없애기 위해 `--dangerously-bypass-approvals-and-sandbox`를 사용한다.
- `tmux-wait-sentinel`은 tmux의 `capture-pane`을 주기적으로 읽어 sentinel 문자열만 판정한다. 본문 품질 판단은 여전히 supervisor가 직접 해야 한다.
- `tmux-send-codex`는 Codex 전용 전송 확인 헬퍼다. `Working`이 너무 짧게 지나가는 경우를 위해 새 응답 블록도 성공 신호로 본다. 둘 다 없으면 재전송 1회 후 supervisor가 직접 pane을 확인한다.
- review 세션 프롬프트 전송은 `tmux-send-claude`, 완료 대기는 `tmux-wait-sentinel` 조합을 기본으로 쓴다.
- 이 옵션은 외부 샌드박스나 사용자가 환경을 통제하고 있을 때만 쓰는 것이 맞다.
