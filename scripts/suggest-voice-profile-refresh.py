#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _find_chapters(novel_dir: Path, start: int, end: int) -> list[Path]:
    result: list[Path] = []
    for path in sorted((novel_dir / "chapters").glob("**/chapter-*.md")):
        match = re.search(r"chapter-(\d+)\.md$", path.name)
        if not match:
            continue
        episode = int(match.group(1))
        if start and episode < start:
            continue
        if end and episode > end:
            continue
        result.append(path)
    return result


def _strip_meta_and_markup(text: str) -> str:
    text = re.sub(r"\n---\s*\n### EPISODE_META\s*```yaml.*", "", text, flags=re.DOTALL)
    text = re.sub(r"^#.*\n+", "", text).strip()
    return text


def _score_paragraph(paragraph: str) -> float:
    length = len(paragraph)
    sentence_count = max(1, len(re.findall(r"[.!?…]|[다요죠]\"", paragraph)))
    quote_penalty = paragraph.count('"') * 20 + paragraph.count("“") * 20
    dialogue_penalty = 80 if paragraph.strip().startswith(("\"", "“")) else 0
    markdown_penalty = 60 if paragraph.startswith(("-", "|", "#")) else 0
    length_score = 220 - abs(220 - length)
    sentence_score = 40 if 2 <= sentence_count <= 5 else max(0, 20 - abs(4 - sentence_count) * 5)
    return float(length_score + sentence_score - quote_penalty - dialogue_penalty - markdown_penalty)


def _collect_candidates(path: Path) -> list[dict[str, object]]:
    body = _strip_meta_and_markup(path.read_text(encoding="utf-8"))
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    candidates: list[dict[str, object]] = []
    for idx, paragraph in enumerate(paragraphs, start=1):
        if len(paragraph) < 100 or len(paragraph) > 420:
            continue
        if paragraph.startswith(("```", "***")):
            continue
        score = _score_paragraph(paragraph)
        candidates.append(
            {
                "chapter": path.name,
                "path": str(path),
                "paragraph_index": idx,
                "score": round(score, 2),
                "text": paragraph,
            }
        )
    return candidates


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--novel-dir", required=True)
    parser.add_argument("--from-episode", type=int, default=0)
    parser.add_argument("--to-episode", type=int, default=0)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--format", choices={"markdown", "json"}, default="markdown")
    args = parser.parse_args(argv[1:])

    novel_dir = Path(args.novel_dir)
    chapters = _find_chapters(novel_dir, args.from_episode, args.to_episode)
    candidates: list[dict[str, object]] = []
    for chapter in chapters:
        candidates.extend(_collect_candidates(chapter))
    candidates.sort(key=lambda item: item["score"], reverse=True)
    candidates = candidates[: args.top]

    if args.format == "json":
        print(json.dumps(candidates, ensure_ascii=False, indent=2))
        return 0

    lines = ["## Voice Profile Refresh Candidates", ""]
    if not candidates:
        lines.append("(후보 없음)")
        print("\n".join(lines))
        return 0

    for item in candidates:
        lines.append(
            f"- {item['chapter']} 문단 {item['paragraph_index']} (score={item['score']})"
        )
        lines.append(f"  {item['text']}")
        lines.append("")
    print("\n".join(lines).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
