#!/usr/bin/env python3
"""존댓말/반말 결정론적 스캐너 — unified-reviewer 항목 6(존댓말 검사) 보조 도구.

이 스크립트는 **판정기가 아니라 리뷰어 보조 도구**다. 대사의 종결어미를
휴리스틱으로 존대/반말/중립으로 분류하고, 인접 지문에서 화자 후보를 추출하며,
CLAUDE.md §8.1 호칭/어투 매트릭스를 함께 출력한다. 최종 존댓말 위반 판정은
사람(unified-reviewer)이 이 재료를 §8.1 매트릭스와 대조해 내린다.

동작
----
(a) 큰따옴표("..." 또는 “...”) 기준으로 대사를 추출한다.
(b) 종결어미 휴리스틱으로 존대/반말/중립을 분류한다.
    - 존대: -요/-죠(해요체), -ㅂ니다/-습니다·-ㅂ니까/-습니까(합쇼체), -시오/-십시오,
      -ㅂ시다(청유), 하오체(-오/-소), 정중 응답(예/네)
    - 반말: -다/-냐/-니/-라/-자/-지/-어/-아/-네/-군/-야 등 해라체·해체
    - 중립: 호명(이름/친족어)·감탄사·명사 종결처럼 register 표지가 없는 경우
(c) 대사 앞뒤 지문에서 인명 후보(§8.1 매트릭스·EPISODE_META characters_appeared 기반)를
    추출해 화자 후보 힌트로 제시한다.
(d) --claude-md가 주어지면 §8.1 매트릭스 표를 파싱해 함께 출력한다.

한계 (반드시 인지할 것)
----------------------
- **화자 귀속은 불확실**하다. 인접 지문의 인명을 후보로 제시할 뿐, 실제 화자를
  단정하지 않는다. 3인칭 지문·연속 대사·화자 태그 생략 시 오귀속 가능.
- **한국어 어미는 중의적**이다. `-니까`는 연결어미(배고프니까)일 수 있고, `-네`는
  감탄(좋네, 반말)과 정중(-네요에서 -요 탈락)의 경계가 흐리며, `-오/-소`(하오체)는
  명사(미소)와 충돌할 수 있다. `아니다`(반말)와 `-ㅂ니다`(존대)는 종성 ㅂ 유무로만
  구분한다. 보수적으로 분류하되, 확신 낮음 항목은 `확신` 열에 표시한다.
- 이 도구는 **문장 부호가 없는 구어체·사투리·시대어**를 완전히 다루지 못한다.
- 출력은 리뷰 재료다. **위반 여부를 스스로 판정하지 않는다.**

usage
-----
    # 기본: 대사 분류 + 화자 후보만
    python3 scripts/speech-level-scan.py --chapter chapters/prologue/chapter-02.md

    # §8.1 매트릭스까지 함께 대조 (권장)
    python3 scripts/speech-level-scan.py \
        --chapter no-title-001/chapters/arc-01/chapter-07.md \
        --claude-md no-title-001/CLAUDE.md

    # 존대/반말만 필터
    python3 scripts/speech-level-scan.py --chapter <ch> --only 존대,반말
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ── 한글 종성(받침) 계산 ─────────────────────────────────────
_HANGUL_BASE = 0xAC00
_HANGUL_LAST = 0xD7A3
_JONG_B = 17  # 종성 ㅂ 인덱스 (합/습/입/갑/십 …)


def _jongseong(ch: str) -> int:
    """한글 음절의 종성 인덱스. 한글 음절이 아니면 -1."""
    code = ord(ch)
    if _HANGUL_BASE <= code <= _HANGUL_LAST:
        return (code - _HANGUL_BASE) % 28
    return -1


def _formal_before(clause: str, tail: str) -> bool:
    """clause가 tail로 끝나고, tail 직전 음절의 종성이 ㅂ이면 True.

    -ㅂ니다/-습니다(존대) vs 아니다(반말), -ㅂ니까(존대) vs -니까(연결어미),
    -ㅂ시다(존대) vs 계시다(평서) 구분에 사용.
    """
    if not clause.endswith(tail) or len(clause) < len(tail) + 1:
        return False
    pre = clause[-(len(tail) + 1)]
    return _jongseong(pre) == _JONG_B


# ── 호명(vocative) / 응답 사전 ────────────────────────────────
KINSHIP = {
    "어머니", "어머님", "엄마", "아버지", "아버님", "아빠", "할머니", "할머님",
    "할아버지", "할아버님", "형", "형님", "누나", "누님", "언니", "오빠", "아우",
    "동생", "아들", "딸", "선생", "선생님", "사부", "사부님", "스승", "스승님",
    "나리", "도련님", "아씨", "마님", "대인", "소협", "대협", "낭자", "공자",
    "소저", "낭군", "부인", "여보", "당신",
}
AFFIRM_JONDAE = {"예", "네", "넵", "예예", "네네", "그럼요", "아니요", "아니오", "글쎄요"}
AFFIRM_BANMAL = {"응", "어", "그래", "아니", "글쎄", "싫어", "됐어", "그럼"}

# 지문 화자 귀속에 쓰는 발화 동사 힌트 (참고용).
SPEECH_VERBS = (
    "말했다", "말한다", "물었다", "묻는다", "답했다", "대답했다", "대꾸했다",
    "중얼거렸다", "외쳤다", "소리쳤다", "속삭였다", "내뱉었다", "덧붙였다",
    "읊조렸다", "말을 이었다", "입을 열었다", "되물었다",
)

_VOCATIVE_PARTICLE = re.compile(r"(아|야|여|이여|이시여|님)$")


def _strip_edges(text: str) -> str:
    """앞뒤 공백·따옴표·종결 문장부호 제거."""
    return re.sub(r'^[\s"“”\'‘’]+|[\s"“”\'‘’.…?!~\-—―、。,，)\]』」]+$', "", text)


def _is_vocative(clause: str, names: set[str]) -> bool:
    """호명(이름/친족어, +호격조사)인지. register 표지가 아니므로 backtrack 대상."""
    base = _VOCATIVE_PARTICLE.sub("", clause).strip()
    if not base:
        return False
    if clause in KINSHIP or base in KINSHIP:
        return True
    if clause in names or base in names:
        return True
    # 이름+호격조사 (무진아, 서린아) — 짧은 순한글 토큰이면 호명 후보로 본다.
    if _VOCATIVE_PARTICLE.search(clause) and re.fullmatch(r"[가-힣]{1,4}", base):
        return True
    return False


def _clause_label(clause: str, names: set[str]) -> tuple[str, str, str] | None:
    """한 절(clause)의 speech-level. register 표지가 없으면 None (backtrack)."""
    c = _strip_edges(clause)
    if not c:
        return None
    if _is_vocative(c, names):
        return None  # 호명 — 표지 아님, 앞 절로 backtrack

    if c in AFFIRM_JONDAE:
        return ("존대", "정중 응답(예/네)", "낮음")
    if c in AFFIRM_BANMAL:
        return ("반말", "반말 응답(응/어/그래)", "낮음")

    # ── 존대 (해요체 → 합쇼체 → 하오체) ──
    if c.endswith("요") or c.endswith("죠"):
        return ("존대", "-요/-죠 (해요체)", "높음")
    if _formal_before(c, "니다"):
        return ("존대", "-ㅂ니다/-습니다 (합쇼체 서술)", "높음")
    if _formal_before(c, "니까"):
        return ("존대", "-ㅂ니까/-습니까 (합쇼체 의문)", "높음")
    if _formal_before(c, "시다"):
        return ("존대", "-ㅂ시다 (합쇼체 청유)", "보통")
    if c.endswith("십시오") or c.endswith("시오"):
        return ("존대", "-시오/-십시오 (명령)", "보통")

    # ── 반말 (해라체 → 해체) ──
    if c.endswith("냐"):
        return ("반말", "-냐 (해라체 의문)", "높음")
    if c.endswith("니"):
        return ("반말", "-니 (해라체 의문)", "보통")
    if c.endswith("다"):
        return ("반말", "-다 (해라체 서술)", "보통")
    if c.endswith("라"):
        return ("반말", "-라/-어라 (해라체 명령)", "보통")
    if c.endswith("자"):
        return ("반말", "-자 (해라체 청유)", "보통")
    if c.endswith("지"):
        return ("반말", "-지 (해체)", "보통")
    if c.endswith("군") or c.endswith("구나"):
        return ("반말", "-군/-구나 (감탄)", "보통")
    if c.endswith("야"):
        return ("반말", "-야 (해체)", "보통")
    if c.endswith("네"):
        return ("반말", "-네 (감탄, 해체)", "낮음")
    if re.search(r"(어|아|여|해|봐|와|까|걸|게)$", c):
        return ("반말", "-어/-아/해체 종결", "낮음")

    # ── 하오체 (-오/-소) : 명사 충돌 위험, 최저 확신 ──
    if c.endswith("소") or c.endswith("오"):
        return ("존대", "-오/-소 (하오체, 명사 충돌 주의)", "낮음")

    return None


def classify_dialogue(text: str, names: set[str]) -> tuple[str, str, str]:
    """대사 전체를 절 단위로 뒤에서부터 검사, 첫 register-표지 절로 분류.

    끝의 호명·감탄사는 건너뛰고 실제 종결 register를 찾는다. 절마다 라벨이
    엇갈리면 note에 '혼합' 표시. 아무 표지도 없으면 중립.
    """
    clauses = [cl for cl in re.split(r"[.?!…,、，。]\s*", text) if cl.strip()]
    if not clauses:
        return ("중립", "표지 없음", "-")

    chosen: tuple[str, str, str] | None = None
    seen_labels: set[str] = set()
    for clause in reversed(clauses):
        label = _clause_label(clause, names)
        if label is not None:
            seen_labels.add(label[0])
            if chosen is None:
                chosen = label
    if chosen is None:
        return ("중립", "호명/감탄/명사 종결", "-")
    level, note, conf = chosen
    if len({lbl for lbl in seen_labels if lbl in ("존대", "반말")}) > 1:
        note = f"{note} · ⚠️혼합(존대+반말)"
    return (level, note, conf)


# ── 매트릭스 / 인명 파싱 ──────────────────────────────────────
def _slice_section(text: str, key: str) -> str | None:
    lines = text.splitlines()
    start: int | None = None
    start_level = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#") and key in line:
            start = i
            start_level = len(stripped) - len(stripped.lstrip("#"))
            break
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start + 1:]:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            if level <= start_level:
                break
        body.append(line)
    return "\n".join(body)


def _clean_name(cell: str) -> str | None:
    """매트릭스 셀에서 인명만 추출. register 규칙 셀(존대+어머니 등)은 제외."""
    c = cell.replace("*", "").strip()
    if not c or c in ("—", "-") or "{{" in c:
        return None
    return c if re.fullmatch(r"[가-힣]{2,5}", c) else None


def parse_matrix(claude_md_text: str) -> tuple[str | None, set[str]]:
    """§8.1 매트릭스 섹션 원문과 인명 집합을 반환.

    인명은 헤더 행(열 = 청자)과 각 데이터 행의 첫 셀(행 = 화자)에서만 뽑는다.
    내부 규칙 셀(존대/반말/호칭 등)은 인명원으로 쓰지 않아 노이즈를 줄인다.
    """
    section = _slice_section(claude_md_text, "호칭/어투 매트릭스")
    if section is None:
        return (None, set())
    names: set[str] = set()
    table_lines: list[str] = []
    for line in section.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        table_lines.append(line)
        if set(s) <= set("|-: "):  # 구분선
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        if "화자" in s or "청자" in s:  # 헤더 행 → 열(청자) 인명
            for cell in cells[1:]:
                nm = _clean_name(cell)
                if nm:
                    names.add(nm)
            continue
        nm = _clean_name(cells[0])  # 데이터 행 → 첫 셀(화자) 인명
        if nm:
            names.add(nm)
    table = "\n".join(table_lines)
    return (table or None, names)


def parse_meta_characters(full_text: str) -> set[str]:
    """EPISODE_META의 characters_appeared 인명."""
    names: set[str] = set()
    m = re.search(r"characters_appeared:\s*\n((?:\s*-\s*.+\n?)+)", full_text)
    if m:
        for line in m.group(1).splitlines():
            item = line.strip().lstrip("-").strip().strip('"').strip("'")
            if item:
                names.add(item)
    return names


# ── 대사 추출 + 화자 힌트 ─────────────────────────────────────
_QUOTE_RE = re.compile(r'"([^"]+)"|“([^”]+)”')


def _is_dialogue_line(line: str) -> bool:
    s = line.strip()
    return s.startswith('"') or s.startswith("“")


def _is_narration_line(line: str) -> bool:
    s = line.strip()
    if not s or _is_dialogue_line(line):
        return False
    return not (s.startswith("#") or s.startswith("***") or s.startswith("---")
                or s.startswith("```") or s.startswith("["))


def _nearest_narration(lines: list[str], idx: int, step: int) -> str:
    j = idx + step
    while 0 <= j < len(lines):
        if _is_narration_line(lines[j]):
            return lines[j].strip()
        j += step
    return ""


def _speaker_hint(context_after: str, context_before: str,
                  same_line: str, names: set[str]) -> str:
    """인접 지문에서 인명 후보 추출. (뒤)=대사 다음 지문, (앞)=이전 지문."""
    hints: list[str] = []

    def _found(text: str) -> list[str]:
        got = [n for n in names if n and n in text]
        # 발화 동사 근처 인명을 앞세운다.
        got.sort(key=lambda n: (0 if any(v in text for v in SPEECH_VERBS) else 1))
        return got

    for name in _found(same_line):
        hints.append(f"{name}(동일행)")
    for name in _found(context_after):
        tag = f"{name}(뒤)"
        if tag not in hints and f"{name}(동일행)" not in hints:
            hints.append(tag)
    for name in _found(context_before):
        tag = f"{name}(앞)"
        if all(name not in h for h in hints):
            hints.append(tag)
    # 중복 인명 축약
    seen: set[str] = set()
    out: list[str] = []
    for h in hints:
        base = re.sub(r"\(.*\)$", "", h)
        if base in seen:
            continue
        seen.add(base)
        out.append(h)
    return ", ".join(out) if out else "-"


def scan_chapter(chapter_text: str, names: set[str]) -> list[dict]:
    """본문에서 대사 단위 스캔 결과 리스트."""
    # EPISODE_META 이하 제거 (본문만, 줄번호는 파일과 일치).
    body = re.split(r"^---\s*\n###\s*EPISODE_META", chapter_text, flags=re.MULTILINE)[0]
    body = re.split(r"^###\s*EPISODE_META", body, flags=re.MULTILINE)[0]
    lines = body.splitlines()

    results: list[dict] = []
    for i, line in enumerate(lines):
        matches = list(_QUOTE_RE.finditer(line))
        if not matches:
            continue
        same_line_rest = _QUOTE_RE.sub("", line).strip()
        after = _nearest_narration(lines, i, +1)
        before = _nearest_narration(lines, i, -1)
        hint = _speaker_hint(after, before, same_line_rest, names)
        for mt in matches:
            quote = mt.group(1) or mt.group(2) or ""
            quote = quote.strip()
            if not quote:
                continue
            level, note, conf = classify_dialogue(quote, names)
            results.append({
                "line": i + 1,
                "quote": quote,
                "level": level,
                "note": note,
                "conf": conf,
                "speaker_hint": hint,
            })
    return results


# ── 출력 ─────────────────────────────────────────────────────
def _truncate(text: str, n: int = 24) -> str:
    text = text.replace("|", "/").replace("\n", " ")
    return text if len(text) <= n else text[: n - 1] + "…"


def render(results: list[dict], matrix_table: str | None,
           matrix_names: set[str], only: set[str] | None) -> str:
    out: list[str] = []
    out.append("## 존댓말/반말 스캔 (리뷰어 보조 — 판정 아님)\n")
    out.append(
        "> 종결어미 휴리스틱 분류 + 인접 지문 화자 후보. 실제 위반 판정은 §8.1 "
        "매트릭스와 대조해 리뷰어가 내린다. 귀속/어미 중의성 한계는 스크립트 "
        "docstring 참조.\n"
    )
    shown = [r for r in results if not only or r["level"] in only]
    counts = {"존대": 0, "반말": 0, "중립": 0}
    for r in results:
        counts[r["level"]] = counts.get(r["level"], 0) + 1
    out.append(
        f"- 대사 {len(results)}건 (존대 {counts['존대']} / 반말 {counts['반말']} "
        f"/ 중립 {counts['중립']})"
        + (f" · 필터: {'/'.join(sorted(only))}" if only else "")
        + "\n"
    )
    out.append("| 줄 | 대사(축약) | 분류 | 근거(어미) | 확신 | 화자 후보 힌트 |")
    out.append("|----|-----------|------|-----------|------|----------------|")
    for r in shown:
        out.append(
            f"| {r['line']} | {_truncate(r['quote'])} | {r['level']} | "
            f"{r['note']} | {r['conf']} | {r['speaker_hint']} |"
        )

    out.append("\n### §8.1 호칭/어투 매트릭스")
    if matrix_table:
        out.append("")
        out.append(matrix_table)
        if matrix_names:
            out.append(f"\n- 매트릭스 인명: {', '.join(sorted(matrix_names))}")
    else:
        out.append("\n(제공되지 않음 — `--claude-md` 미지정 또는 §8.1 섹션 없음. "
                    "리뷰어가 매트릭스를 직접 대조할 것)")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="존댓말/반말 스캐너 (리뷰어 보조, 비판정)."
    )
    parser.add_argument("--chapter", required=True, help="챕터 md 경로")
    parser.add_argument("--claude-md", default=None,
                        help="§8.1 매트릭스 파싱용 CLAUDE.md 경로 (선택)")
    parser.add_argument("--only", default=None,
                        help="분류 필터 (쉼표구분: 존대,반말,중립)")
    args = parser.parse_args(argv[1:])

    chapter_path = Path(args.chapter)
    try:
        chapter_text = chapter_path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as exc:
        print(f"ERROR chapter 읽기 실패: {exc}", file=sys.stderr)
        return 2

    matrix_table: str | None = None
    matrix_names: set[str] = set()
    if args.claude_md:
        try:
            claude_text = Path(args.claude_md).read_text(encoding="utf-8")
            matrix_table, matrix_names = parse_matrix(claude_text)
        except (FileNotFoundError, OSError) as exc:
            print(f"WARN claude-md 읽기 실패: {exc}", file=sys.stderr)

    names = matrix_names | parse_meta_characters(chapter_text)

    only: set[str] | None = None
    if args.only:
        only = {s.strip() for s in args.only.split(",") if s.strip()}

    results = scan_chapter(chapter_text, names)
    print(render(results, matrix_table, matrix_names, only))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
