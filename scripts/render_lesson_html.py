#!/usr/bin/env python3
"""Render a lesson-plan Markdown file to standalone HTML using Lesson 01 styles."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print(
            "Usage: render_lesson_html.py INPUT.md OUTPUT.html [TEMPLATE.html]",
            file=sys.stderr,
        )
        return 2

    input_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()
    template_path = (
        Path(sys.argv[3]).resolve()
        if len(sys.argv) == 4
        else input_path.parent / "01-单摆周期.html"
    )

    source = input_path.read_text(encoding="utf-8")
    template = template_path.read_text(encoding="utf-8")
    responsive_path = Path(__file__).resolve().parents[1] / "styles" / "lesson-responsive.css"
    responsive_css = responsive_path.read_text(encoding="utf-8")

    title_match = re.search(r"^#\s+(.+?)\s*$", source, flags=re.MULTILINE)
    if not title_match:
        raise ValueError(f"No level-1 Markdown title found in {input_path}")

    title = title_match.group(1).strip()
    body_source = source[: title_match.start()] + source[title_match.end() :]
    extracted_styles = re.findall(
        r"<style(?:\s[^>]*)?>.*?</style>", template, flags=re.DOTALL
    )
    style_blocks = "\n".join(
        block for block in extracted_styles if 'id="science-g5-responsive"' not in block
    )
    if not style_blocks:
        raise ValueError(f"No style blocks found in template {template_path}")
    style_blocks += (
        '\n<style id="science-g5-responsive">\n'
        + responsive_css.rstrip()
        + "\n</style>"
    )

    renderer = MarkdownIt("commonmark", {"html": True, "typographer": False})
    renderer.enable("table")
    renderer.enable("strikethrough")
    rendered_body = renderer.render(body_source.strip() + "\n")

    document = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh-CN" xml:lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="generator" content="Science G5 lesson renderer" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
  <title>{html.escape(title)}</title>
{style_blocks}
</head>
<body>
<header id="title-block-header">
<h1 class="title">{html.escape(title)}</h1>
</header>
<main>
{rendered_body}</main>
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    print(f"Rendered {input_path} -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
