"""템플릿 헤딩/포맷 계약 테스트.

레포에 배포된 실제 템플릿 파일들(summaries/*.md, plot/foreshadowing.md, CLAUDE.md §8)을
fixture로 사용해 "템플릿 형식 그대로 채우면 compile_brief 파서가 추출한다"를 검증한다.
템플릿의 헤딩/컬럼이 바뀌어 파서와 어긋나면 이 테스트가 잡는다.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import compile_brief
from test_compile_brief import make_novel


def _template(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _fill_rest(text: str, filler: str = "채움") -> str:
    """남은 {{...}} placeholder를 일괄 치환한다."""
    return re.sub(r"\{\{[^}]*\}\}", filler, text)


# ── A.1 · 캐릭터별 knowledge-map ──────────────────────────


def _filled_knowledge_map() -> str:
    km = _template("summaries/knowledge-map.md")
    km = km.replace("{{캐릭터A}}", "린").replace("{{캐릭터B}}", "가온")
    km = km.replace("{{N}}", "1")
    km = km.replace("{{정보1}}", "봉인의 위치라는 비밀 [PIN]")
    km = km.replace("{{정보2}}", "가온의 진짜 정체")
    km = km.replace("{{정보3}}", "문지기 규칙")
    return _fill_rest(km, "미정")


def test_character_keyed_knowledge_map_extracts_requested_character() -> None:
    km = _filled_knowledge_map()
    result = compile_brief._filter_knowledge_map(km, ["린"], before_episode=5)
    assert "### 린" in result
    assert "봉인의 위치라는 비밀 [PIN]" in result
    assert "문지기 규칙" in result
    # 요청하지 않은 캐릭터 블록은 나오지 않는다 (가온 블록은 예시 '—' 행뿐).
    assert "### 가온" not in result


def test_global_knowledge_preserves_owner_in_character_keyed_map() -> None:
    km = _filled_knowledge_map()
    result = compile_brief._extract_global_knowledge(km)
    assert "소유자" in result  # 합성된 소유자 열
    assert "린" in result
    assert "봉인의 위치라는 비밀" in result


def test_knowledge_map_pin_row_survives_recent_window() -> None:
    rows = "\n".join(
        f"| 사실{i} | O | {i}화 | 직접 | |" for i in range(2, 20)
    )
    content = (
        "### 린\n\n"
        "| 정보 | 알고 있음? | 습득 화수 | 출처 | 비고 |\n"
        "|------|-----------|----------|------|------|\n"
        "| 최초의 비밀 [PIN] | O | 1화 | 직접 | |\n"
        + rows + "\n"
    )
    result = compile_brief._filter_knowledge_map(content, ["린"], before_episode=0)
    # 창(12행) 밖의 가장 오래된 행이지만 [PIN]이라 항상 포함.
    assert "최초의 비밀 [PIN]" in result
    assert "생략" in result  # 창 밖 나머지는 생략 표시


def test_matrix_knowledge_map_still_supported() -> None:
    """하위 호환: 단일 매트릭스 형식도 그대로 동작."""
    content = (
        "| 정보 | 린 | 가온 | 비고 |\n"
        "|------|----|----|------|\n"
        "| 봉인의 위치 | O(1화) | X | 린만 확인 |\n"
    )
    result = compile_brief._filter_knowledge_map(content, ["린"], before_episode=5)
    assert "봉인의 위치" in result
    assert "린" in result


# ── A.2 · CLAUDE.md §8.1 blockquote + §8.2 + §8.3 ──────────


def test_claude_md_section8_full_extraction() -> None:
    cm = _template("CLAUDE.md")
    cm = (
        cm.replace("{{CHAR_A}}", "린")
        .replace("{{CHAR_B}}", "가온")
        .replace("{{CHAR_C}}", "도현")
        .replace("{{DEFAULT_RULE}}", "초면은 존댓말, 친밀해지면 반말")
        .replace("{{CHAR}}", "린")
    )
    cm = _fill_rest(cm)
    rules = compile_brief._extract_claude_md_rules(cm)
    assert "### 호칭/어투" in rules
    assert "린" in rules  # §8.1 매트릭스 데이터
    assert "미등록 조합 기본값" in rules  # §8.1 blockquote
    assert "상황별 어투 전환 (§8.2)" in rules
    assert "어투 변화 이력 (§8.3)" in rules


def test_claude_md_section8_heading_suffix_tolerant() -> None:
    content = (
        "### 8.1 호칭/어투 매트릭스 (갱신)\n"
        "| 화자 | 대상 | 어투 |\n"
        "|------|------|------|\n"
        "| 린 | 가온 | 반말 |\n"
        "> 미등록 조합 기본값: 존댓말\n"
    )
    rules = compile_brief._extract_claude_md_rules(content)
    assert "### 호칭/어투" in rules
    assert "미등록 조합 기본값" in rules


# ── A.6 · episode-log header-aware ─────────────────────────


def test_episode_log_header_aware_columns() -> None:
    el = _template("summaries/episode-log.md")
    el += (
        "| 1 | 세라 각성 | 302호 | 린, 가온 | 첫 대면 | 귀환 선언 "
        "| description | emotion | relationship |\n"
    )
    result = compile_brief._extract_last_n_episodes(el, n=3, before_episode=5)
    # '요약' 열이 '제목'으로 오독되지 않는다 (헤더에 제목 열 없음).
    assert "### 1화 — 세라 각성" not in result
    assert "- 요약: 세라 각성" in result
    assert "- 장소: 302호" in result
    assert "- 등장인물: 린, 가온" in result
    assert "- 핵심 사건: 첫 대면" in result
    assert "- 엔딩 훅: 귀환 선언" in result


def test_episode_log_legacy_two_column_still_supported() -> None:
    content = (
        "| 화 | 제목 | 요약 |\n"
        "|----|------|------|\n"
        "| 1 | 검은 봉투 | 봉투를 숨긴다 |\n"
    )
    result = compile_brief._extract_last_n_episodes(content, n=3, before_episode=5)
    assert "### 1화 — 검은 봉투" in result
    assert "- 요약: 봉투를 숨긴다" in result


def test_episode_log_characters_column_used_for_detection(tmp_path) -> None:
    novel_dir = make_novel(tmp_path)
    (novel_dir / "summaries" / "episode-log.md").write_text(
        "| 화 | 요약 | 장소 | 등장인물 | 핵심 사건 | 엔딩 훅 |\n"
        "|----|------|------|----------|----------|---------|\n"
        "| 1 | 도입 | 시장 | 서린, 이도 | 첫 충돌 | 추격 |\n",
        encoding="utf-8",
    )
    chars = compile_brief._extract_characters_from_episode_log(str(novel_dir), 2)
    assert "서린" in chars and "이도" in chars


# ── A.7 · foreshadowing alias + 회수 완료 lookup ────────────


def test_foreshadowing_template_active_block_extracted() -> None:
    fs = _template("plot/foreshadowing.md")
    fs = fs.replace("{{복선 제목}}", "린의 정체", 1)
    fs = _fill_rest(fs)
    result = compile_brief._filter_foreshadowing(fs)
    assert "F001" in result
    assert "린의 정체" in result


def test_foreshadowing_alias_and_completed_episode_lookup() -> None:
    content = (
        "## 복선 현황\n\n"
        "### F001. 세라의 정체\n\n"
        "- **설치**: 1화\n"
        "- **내용**: 표면적으로 보이는 것\n"
        "- **현재 상태**: 회수 완료\n\n"
        "## 회수 완료\n\n"
        "| ID | 복선 | 회수 화수 | 비고 |\n"
        "|----|------|----------|------|\n"
        "| F001 | 세라의 정체 | 41화 | 완료 |\n"
    )
    result = compile_brief._filter_foreshadowing(content)
    assert "F001" in result
    # '## 복선 현황' alias 인식 + 회수 완료 표에서 화수(41화) 조회.
    assert "회수 완료 (41화)" in result


# ── A.4/A.12 · relationship matrix(+blockquote)/만남/변화 이력 ─


def test_relationship_log_template_all_tables_extracted() -> None:
    rl = _template("summaries/relationship-log.md")
    rl = (
        rl.replace("{{CHAR_A}}", "린")
        .replace("{{CHAR_B}}", "가온")
        .replace("{{CHAR_C}}", "도현")
        .replace("{{A}}", "린")
        .replace("{{B}}", "가온")
        .replace("{{N}}", "3")
    )
    rl = _fill_rest(rl)
    result = compile_brief._filter_relationship_log(rl, ["린", "가온"])
    # 헤딩과 표 사이 blockquote가 있어도 매트릭스가 추출된다.
    assert "### 관계 매트릭스" in result
    assert "### 최근 만남 로그" in result
    assert "### 관계 변화 이력" in result


def test_relationship_first_meeting_preserved_outside_window() -> None:
    log = "## 만남 로그\n\n> 설명 blockquote\n\n"
    log += "| 화수 | A | B | 유형 | 맥락 | 결과 |\n|---|---|---|---|---|---|\n"
    log += "| 1화 | 린 | 가온 | 첫 만남 | 최초 대면 | 경계 |\n"
    for ep in range(2, 10):
        log += f"| {ep}화 | 린 | 가온 | 대화 | 상황{ep} | 결과{ep} |\n"
    result = compile_brief._filter_relationship_log(log, ["린"])
    assert "최초 대면" in result  # 창 밖 첫 만남 보존
    assert "…" in result or "중략" in result  # 생략 마커


# ── A.5 · Voice Profile 부분 탈락 경고 ─────────────────────


def test_voice_profile_partial_dropout_warns() -> None:
    style = (
        "## 0. Voice Profile\n\n"
        "### 0.1 서술 온도\n"
        "**서술 온도**: 건조하게 관찰한다.\n\n"
        "### 0.2 보이스 우선순위\n"
        "1. 장면 이해\n"
        "2. {{PLACEHOLDER}}\n\n"
        "### 0.3 대표 문단\n"
        "> 채워진 문단.\n\n"
        "## 1. 시점\n"
        "- **시점**: 3인칭\n"
    )
    result = compile_brief._extract_style_rules(style)
    assert "### Voice Profile" in result
    assert "0.1 서술 온도" in result  # 채워진 subsection 유지
    assert "0.3 대표 문단" in result
    assert "### 0.2" not in result  # placeholder subsection 탈락
    assert "⚠️ Voice Profile 일부 미추출" in result
    assert "0.2" in result  # 탈락 번호 명시


def test_voice_profile_all_filled_no_warning() -> None:
    style = (
        "## 0. Voice Profile\n\n"
        "### 0.1 서술 온도\n**서술 온도**: 건조.\n\n"
        "### 0.2 보이스 우선순위\n1. 장면 이해\n\n"
        "## 1. 시점\n- **시점**: 3인칭\n"
    )
    result = compile_brief._extract_style_rules(style)
    assert "### Voice Profile" in result
    assert "미추출" not in result


# ── A.8/A.9 · PARSE-MISS + 버전 스탬프 ─────────────────────


def test_version_stamp_present(tmp_path) -> None:
    novel_dir = make_novel(tmp_path)
    brief = compile_brief._compile_brief(str(novel_dir), 2)
    assert brief.splitlines()[0] == (
        f"<!-- compile_brief v{compile_brief.COMPILE_BRIEF_VERSION} -->"
    )


def test_parse_miss_reported_and_logged(tmp_path) -> None:
    novel_dir = make_novel(tmp_path)
    # 활성 약속을 placeholder(데이터 행 없음) 상태로 만든다.
    (novel_dir / "summaries" / "promise-tracker.md").write_text(
        "## 활성 약속\n| ID | 당사자 | 내용 |\n|----|------|------|\n",
        encoding="utf-8",
    )
    brief = compile_brief._compile_brief(str(novel_dir), 2)
    miss_line = brief.splitlines()[1]
    assert miss_line.startswith("> ⚠️ PARSE-MISS:")
    assert "활성 약속" in miss_line

    events = (novel_dir / "tmp" / "run-metadata" / "events.jsonl").read_text(
        encoding="utf-8"
    )
    assert "parse_miss" in events


def test_no_parse_miss_when_all_sections_present(tmp_path) -> None:
    novel_dir = make_novel(tmp_path)
    brief = compile_brief._compile_brief(str(novel_dir), 2)
    assert "PARSE-MISS" not in brief
