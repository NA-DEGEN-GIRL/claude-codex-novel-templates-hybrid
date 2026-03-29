# Native MCP Cleanup Patch

## Purpose

이 패치는 hybrid 템플릿의 운영 경로를 **native MCP only**로 고정하기 위한 정리다.

- MCP wrapper scripts를 삭제
- `writer_model: codex | claude` 기준으로 문서 표현을 재정렬
- `scripts/`의 역할을 tmux/session helper와 codex mode 편의 런처로 한정

## Deleted Files

- `scripts/compile-brief`
- `scripts/novel-calc`
- `scripts/novel-hanja`
- `scripts/novel-naming`

삭제 이유:

- native MCP가 정본인데 wrapper가 있으면 운영 경로가 이중화된다
- 문서와 실제 런타임이 쉽게 drift한다
- hybrid의 핵심은 writer/review/supervisor 분리이지, MCP를 shell wrapper로 우회하는 것이 아니다

## Documentation Sync

다음 문서를 함께 정리했다.

- `CLAUDE.md`
- `README.md`
- `scripts/README.md`
- `INIT-PROMPT.md`
- `HYBRID-DESIGN.md`

핵심 정리 방향:

- `compile_brief`, `novel-calc`, `novel-hanja`, `novel-naming`은 native MCP로만 사용
- Writer 세션은 `writer_model`에 따라 `codex` 또는 `claude`
- fix routing은 항상 같은 Writer 세션(writer=fixer)으로 되돌린다
- review/summaries/META/git은 Claude review/supervisor 쪽 책임으로 유지

## Intentional Non-Changes

이번 패치에서 유지한 것:

- `tmux-send-codex`
- `tmux-send-claude`
- `tmux-wait-sentinel`
- `run-codex-writer`
- `run-codex-supervisor`
- `run-codex-auditor`

이 파일들은 MCP wrapper가 아니라 session/runtime helper이므로 남겨둔다.

## Result

이제 hybrid 템플릿에서는:

1. MCP 관련 기능은 wrapper 없이 직접 호출한다.
2. `scripts/`는 런타임 보조 도구만 담는다.
3. 문서가 `writer_model` 분기와 책임 분리를 더 일관되게 설명한다.
