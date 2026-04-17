# Drift Policy

**Phase 5 drift automation (2026-04-17)**

## 목적

템플릿 구조가 시간이 지나면서 drift (규칙과 구현의 어긋남)가 누적되는 것을 방지.

- **정본**: `CLAUDE.md §4 Document Authority & Precedence` + `§4.1 Runtime Spec Canon`
- **검증 도구**: `scripts/validate-docs.py`
- **업데이트 로그**: `docs/updates/phase-*.md`

## 자동 검증 체크 목록

`scripts/validate-docs.py`가 수행하는 8종 체크 (Phase 8 확장, 2026-04-17):

| Check | 내용 | FAIL/WARN 조건 |
|-------|------|----------|
| `orphan` | 문서 간 파일 참조가 실제 경로와 일치 | 마크다운 링크가 존재하지 않는 파일 가리킴. Phase 8: placeholder/`{{var}}`/`~/...`/wildcard 스킵. 확장자 whitelist 확장 (md/py/json/sh/yml/yaml/txt/toml/jsonl/cfg/ini/csv) |
| `sentinel` | WRITER_DONE / FIX_DONE / REVIEW_DONE 표기 | Phase 8: canonical 패턴에 `:: run=` suffix 필수. referential 필터에서 '등'/'/'/`출력` 제거 (너무 관대했음). 백틱 감싼 단순 이름 언급은 면책 |
| `writer_model` | prompt 파일의 mode 라벨 일관성 | `claude-writer.md`에 `writer_model: claude` 라벨 없음 (또는 반대) |
| `mcp_naming` | `compile_brief`가 올바르게 기술됨 | Phase 8: 로직 버그 수정 — 이전에는 "MCP 도구"/"MCP server" 경로가 항상 continue로 skip됐음. `compile_brief`를 "MCP 서버"로 기술하고 면책 표현(`novel-editor MCP의 compile_brief`, `~가 아니라`)이 없으면 WARN |
| `phase_docs` | `docs/updates/phase-*.md` 필수 섹션 + Commit sha | Rationale/Changes/Rollback/Validation/Dependencies/Known Issues/References 중 하나라도 없음. Phase 8 추가: `**Commit**: (추가 후 기록)` placeholder 잔존 시 FAIL |
| `claude_md` | CLAUDE.md의 phase별 필수 블록 | §4.1 Spec Canon 누락 시 FAIL, §5.1A/§1 profile 누락 시 WARN |
| `profile_value` (Phase 8 신규) | CLAUDE.md §1 `profile:` 값이 legal syntax | `wuxia \| modern \| game-fantasy \| romance \| regression+{base}` 외 값 시 FAIL. 기본값 `wuxia`는 언제나 legal |
| `writer_hold` (Phase 8 신규) | style-lexicon의 WRITER-HOLD 태그 누적 | 같은 원 표현에 3회 이상 [WRITER-HOLD] 누적 시 WARN (§5.1A 승격 제안) |

## 사용법

```bash
cd /root/novel/claude-codex-novel-templates-hybrid

# 전체 실행
python3 scripts/validate-docs.py

# 특정 체크만
python3 scripts/validate-docs.py --check orphan
python3 scripts/validate-docs.py --check sentinel --check writer_model

# WARN도 FAIL로 (엄격 모드)
python3 scripts/validate-docs.py --strict
```

**Exit code**:
- `0`: 모든 체크 통과 (strict 모드 기준)
- `1`: 한 개 이상 실패
- `2`: 사용 오류

## 예상 baseline 경고

아래 2건은 의도적이며 FAIL 대상이 아님. strict 모드에서도 `--check`로 제외 가능:

1. **`CLAUDE.md`가 `settings/06-humor-guide.md`를 참조**: 해당 파일은 optional이라 기본 배포에 포함 안 됨. `humor_density`가 필요한 프로젝트만 생성. CLAUDE.md §2에도 `(optional)` 표기.
2. **`HYBRID-DESIGN.md`가 `.claude/agents/writer.md`를 참조**: 이미 삭제된 파일. "삭제됨" 맥락으로 설명 중. 관련 리뷰 문서(`docs/archive/hybrid-agent-review.md`, `docs/archive/hybrid-prompt-review.md`)에서 historical context로 유지.

baseline을 넘어서는 경고가 나오면 **drift 신호**로 간주.

## CI 통합 가이드

### Git pre-commit hook (권장)

`.git/hooks/pre-commit`:

```bash
#!/usr/bin/env bash
set -e
cd "$(git rev-parse --show-toplevel)"
if [ -f scripts/validate-docs.py ]; then
    echo "[drift] validating docs..."
    python3 scripts/validate-docs.py || {
        echo "[drift] FAIL — 문서 drift 감지. 수정 후 다시 commit하거나 --no-verify로 강제 (권장 안 함)."
        exit 1
    }
fi
```

### GitHub Actions (CI)

```yaml
name: drift-check
on: [push, pull_request]
jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.10' }
      - name: Validate docs
        run: python3 scripts/validate-docs.py
```

## 정본 변경 절차

Spec Canon 값(sentinel 포맷, writer_model 값, MCP 서버 이름, review mode 이름 등)을 변경할 때:

1. **먼저 `CLAUDE.md §4.1 Runtime Spec Canon`을 수정**.
2. 해당 변경의 영향 범위를 `scripts/validate-docs.py`로 확인:
   ```bash
   python3 scripts/validate-docs.py --strict
   ```
3. FAIL 항목을 모두 해결 (다른 문서에서 새 값으로 통일).
4. 변경 내용을 `docs/updates/phase-N-{topic}.md` 신규 phase 문서로 기록 (Rationale / Changes / Rollback / Validation).
5. `docs/updates/README.md` 인덱스 업데이트.
6. Commit — pre-commit hook 자동 검증.

## 새 체크 추가하기

`scripts/validate-docs.py`에 새 체크를 추가하려면:

1. `check_<name>(report: Report)` 함수 정의 — `Report.fail()` / `warn()` / `info()` 호출로 결과 기록
2. `CHECKS` 딕셔너리에 등록: `"<name>": check_<name>`
3. 이 문서의 "자동 검증 체크 목록" 테이블에 row 추가
4. 필요 시 새 체크의 baseline 경고를 "예상 baseline 경고" 섹션에 기록

## 알려진 한계

1. **정적 문서 분석만**: 런타임 동작은 검증 안 함. Supervisor가 실제로 올바른 prompt 파일을 tmux에 전송하는지는 test_runtime_helpers.py에서 별도 검증.
2. **배치 분석**: 각 파일을 독립 읽기로 처리. 파일 간 의존 그래프는 구성하지 않음. 순환 참조 검출은 범위 외.
3. **다국어 처리**: 체크 대부분은 한국어/영어 텍스트 기반. 다른 언어 프롬프트가 추가되면 re-tune 필요.
4. **파이썬 3.10+ 필요**: dataclass decorator 패턴 사용.

## 참고

- `scripts/validate-docs.py` — 구현체
- `CLAUDE.md §4.1 Runtime Spec Canon` — 정본
- `docs/updates/phase-5-drift-automation.md` — 이 policy 작성 근거
