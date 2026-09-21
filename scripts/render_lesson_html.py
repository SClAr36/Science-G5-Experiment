#!/usr/bin/env python3
"""Render a lesson-plan Markdown file to standalone HTML using Lesson 01 styles."""

from __future__ import annotations

import base64
import html
import mimetypes
import re
import subprocess
import sys
from pathlib import Path

from markdown_it import MarkdownIt

from local_document_links import prepare_document_links


HEADING_RE = re.compile(r"<h([34])(?:\s[^>]*)?>(.*?)</h\1>", flags=re.DOTALL)


def heading_text(inner_html: str) -> str:
    """Return the readable text from a rendered Markdown heading."""

    return html.unescape(re.sub(r"<[^>]+>", "", inner_html)).strip()


def collapsible_heading(level: int, text: str) -> tuple[str, str] | None:
    """Classify lesson headings that should be closed by default in HTML."""

    if level == 3 and "核心问答" in text:
        return "qa", f"{text} / Core Q&A"
    if level != 4:
        return None
    if text.startswith("问"):
        return "qa", "问答 / Q&A"
    if text.startswith("板书与记录"):
        return "notes", "板书与记录 / Board notes & record"
    if text.startswith("板书"):
        return "notes", "板书 / Board notes"
    if text.startswith("课堂笔记"):
        return "notes", "课堂笔记 / Class notes"
    if text.startswith("笔记"):
        return "notes", "笔记 / Notes"
    if text.startswith("离堂记录"):
        return "record", f"{text} / Exit record & answers"
    if text.startswith("记录与板书"):
        return "record", text
    if text.startswith("记录"):
        return "record", f"{text} / Record"
    return None


def wrap_collapsible_sections(rendered_body: str) -> str:
    """Wrap Q&A and note sections in touch-friendly native details elements."""

    parts: list[str] = []
    cursor = 0

    while match := HEADING_RE.search(rendered_body, cursor):
        parts.append(rendered_body[cursor : match.start()])
        level = int(match.group(1))
        config = collapsible_heading(level, heading_text(match.group(2)))
        if config is None:
            parts.append(match.group(0))
            cursor = match.end()
            continue

        kind, label = config
        next_heading = re.search(
            rf"<h[1-{level}](?:\s[^>]*)?>",
            rendered_body[match.end() :],
            flags=re.IGNORECASE,
        )
        section_end = (
            match.end() + next_heading.start()
            if next_heading is not None
            else len(rendered_body)
        )
        content = rendered_body[match.end() : section_end].strip()
        parts.append(
            f'''<details class="lesson-collapsible lesson-collapsible-{kind}">
<summary>
<span class="lesson-collapsible-title">{html.escape(label)}</span>
<span class="lesson-collapsible-hint lesson-collapsible-closed">点击展开 / Tap to open</span>
<span class="lesson-collapsible-hint lesson-collapsible-open">点击收起 / Tap to close</span>
</summary>
<div class="lesson-collapsible-content">
{content}
</div>
</details>
'''
        )
        cursor = section_end

    parts.append(rendered_body[cursor:])
    return "".join(parts)


def embed_local_images(rendered_body: str, base_dir: Path) -> str:
    """Embed lesson-local image files as data URLs for standalone HTML."""

    resolved_base = base_dir.resolve()

    def replace_src(match: re.Match[str]) -> str:
        quote = match.group("quote")
        source = html.unescape(match.group("source"))
        if source.startswith(("data:", "http://", "https://", "//", "#")):
            return match.group(0)

        image_path = (resolved_base / source).resolve()
        if not image_path.is_relative_to(resolved_base) or not image_path.is_file():
            return match.group(0)

        media_type, _ = mimetypes.guess_type(image_path.name)
        if media_type is None or not media_type.startswith("image/"):
            return match.group(0)

        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        data_url = f"data:{media_type};base64,{encoded}"
        return f"src={quote}{data_url}{quote}"

    return re.sub(
        r"""src=(?P<quote>["'])(?P<source>.*?)(?P=quote)""",
        replace_src,
        rendered_body,
        flags=re.IGNORECASE,
    )


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
    rendered_body = wrap_collapsible_sections(rendered_body)
    rendered_body = embed_local_images(rendered_body, input_path.parent)
    rendered_body, markdown_previews, preview_styles = prepare_document_links(
        rendered_body,
        input_path,
        Path(__file__).resolve().parents[1],
        lambda source: wrap_collapsible_sections(renderer.render(source)),
        embed_local_images,
    )
    style_blocks += preview_styles
    index_marker = (
        ' data-document-preview-index="true"'
        if input_path.name.lower() == "readme.md" else ""
    )

    document = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh-CN" xml:lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="generator" content="Science G5 lesson renderer" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
  <title>{html.escape(title)}</title>
{style_blocks}
</head>
<body{index_marker}>
<header id="title-block-header">
<h1 class="title">{html.escape(title)}</h1>
</header>
<main id="lesson-content" tabindex="-1">
{rendered_body}</main>
{markdown_previews}
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    print(f"Rendered {input_path} -> {output_path}")
    index_source = input_path.parent / "README.md"
    index_output = output_path.parent / "README.html"
    if (
        input_path.name.lower() != "readme.md"
        and input_path.parent == output_path.parent
        and index_source.is_file()
        and index_output.is_file()
        and 'data-document-preview-index="true"' in index_output.read_text(encoding="utf-8")
    ):
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), str(index_source),
             str(index_output), str(template_path)],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
