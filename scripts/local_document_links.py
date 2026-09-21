"""Browser-safe navigation for local Markdown and HTML documents.

A file:// browser normally downloads .md files. Index pages therefore embed
Markdown previews and use fragment navigation; no custom app URL scheme,
network request or local web server is needed. A small script resets scrolling
after fragment navigation; the previews remain readable without JavaScript.
"""

from __future__ import annotations

import hashlib
import html
import os
import re
from collections import deque
from pathlib import Path
from typing import Callable
from urllib.parse import quote, unquote, urlsplit

ANCHOR = re.compile(r'(<a\b[^>]*\bhref=")([^"]*)("[^>]*>)(.*?)(</a>)', re.S)
ID = re.compile(r'\bid="([^"]+)"')

PREVIEW_CSS = """
<style id="science-g5-document-previews">
.document-preview { display: none; }
.document-preview:target, .document-preview:has(:target) { display: block; }
body:has(.document-preview:target, .document-preview :target) > #title-block-header,
body:has(.document-preview:target, .document-preview :target) > #lesson-content { display: none; }
.document-preview-bar {
  display: flex; flex-wrap: wrap; align-items: center; gap: .7rem 1rem;
  margin: 0 0 1rem; padding: .8rem 1rem; border: 1px solid #d7e1df;
  border-radius: .65rem; background: #f3f8f6;
}
.document-preview-bar a { font-weight: 600; }
.document-preview-label { color: #536863; font-size: .9rem; }
.document-preview-path { margin: 0 0 1.4rem; }
.document-preview-path summary { cursor: pointer; color: #536863; }
.document-preview-path code {
  display: block; margin-top: .5rem; padding: .7rem;
  white-space: pre-wrap; overflow-wrap: anywhere; user-select: all;
}
.document-preview article > h1:first-child { margin-top: 1rem; }
@media print {
  .document-preview-bar, .document-preview-path { display: none; }
}
</style>
"""


def browser_file_uri(path: Path) -> str:
    """Map a WSL-mounted Windows path to the actual Windows file URL."""
    path = path.resolve()
    value = path.as_posix()
    match = re.match(r"^/mnt/([a-zA-Z])/(.*)$", value)
    if match:
        return "file:///" + match.group(1).upper() + ":/" + quote(match.group(2), safe="/")
    return path.as_uri()


def display_file_path(path: Path) -> str:
    value = path.resolve().as_posix()
    match = re.match(r"^/mnt/([a-zA-Z])/(.*)$", value)
    if match:
        return match.group(1).upper() + ":\\" + match.group(2).replace("/", "\\")
    return str(path.resolve())


def local_target(href: str, owner: Path, project_root: Path) -> tuple[Path, str] | None:
    value = html.unescape(href)
    parsed = urlsplit(value)
    if value.startswith(("#", "//")) or not parsed.path:
        return None
    if parsed.scheme == "file":
        if parsed.netloc not in ("", "localhost"):
            return None
        name = unquote(parsed.path)
        if re.match(r"^/[a-zA-Z]:/", name):
            name = name[1:]
    elif len(parsed.scheme) == 1 and re.match(r"^[a-zA-Z]:[/\\]", value):
        name = unquote(value.split("#", 1)[0].split("?", 1)[0])
    elif parsed.scheme:
        return None
    else:
        name = unquote(parsed.path)
    drive = re.match(r"^([a-zA-Z]):[/\\](.*)$", name)
    if drive and os.name != "nt":
        name = "/mnt/" + drive.group(1).lower() + "/" + drive.group(2).replace("\\", "/")
    target = (owner.parent / name).resolve()
    if not target.is_relative_to(project_root.resolve()) or not target.exists():
        return None
    suffix = ("?" + parsed.query if parsed.query else "") + (
        "#" + parsed.fragment if parsed.fragment else ""
    )
    return target, suffix


def prepare_document_links(
    body: str,
    input_path: Path,
    project_root: Path,
    render_markdown: Callable[[str], str],
    embed_images: Callable[[str, Path], str],
) -> tuple[str, str, str]:
    """Keep HTML navigation native and provide readable local Markdown previews."""
    input_path = input_path.resolve()
    project_root = project_root.resolve()
    is_index = input_path.name.lower() == "readme.md"
    previews: dict[Path, str] = {}
    rendered: dict[Path, str] = {}
    pending: deque[Path] = deque()

    def register(path: Path) -> str:
        if path not in previews:
            rel = path.relative_to(project_root).as_posix()
            previews[path] = "md-preview-" + hashlib.sha256(rel.encode()).hexdigest()[:12]
            pending.append(path)
        return previews[path]

    # Every direct Markdown link in an index gets an in-page preview.
    # Elsewhere, a paired HTML page is preferred for normal reading navigation.
    for match in ANCHOR.finditer(body):
        resolved = local_target(match.group(2), input_path, project_root)
        if resolved:
            target, _ = resolved
            if target.suffix.lower() == ".md" and target != input_path:
                if is_index or not target.with_suffix(".html").is_file():
                    register(target)

    def rewrite(text: str, owner: Path) -> str:
        def replace(match: re.Match[str]) -> str:
            resolved = local_target(match.group(2), owner, project_root)
            if not resolved:
                return match.group(0)
            target, suffix = resolved
            inner = match.group(4)
            attributes = ""
            if target.suffix.lower() == ".md":
                if target == input_path:
                    url = "#lesson-content"
                elif target in previews:
                    key = previews[target]
                    url = "#" + key
                    attributes = ' data-md-preview="' + key + '"'
                elif target.with_suffix(".html").is_file():
                    url = browser_file_uri(target.with_suffix(".html")) + suffix
                else:
                    key = register(target)
                    url = "#" + key
                    attributes = ' data-md-preview="' + key + '"'
                if attributes and inner.strip() == "打开":
                    inner = "预览"
            elif target.suffix.lower() in {".html", ".htm"}:
                url = browser_file_uri(target) + suffix
            else:
                url = browser_file_uri(target) + ("/" if target.is_dir() else "") + suffix
            closing = match.group(3)
            if attributes:
                closing = closing[:-1] + attributes + ">"
            return match.group(1) + html.escape(url, quote=True) + closing + inner + match.group(5)

        return ANCHOR.sub(replace, text)

    body = rewrite(body, input_path)

    # Follow only Markdown links without an HTML counterpart. This keeps all
    # visible navigation readable without recursively embedding every old lesson.
    while pending:
        target = pending.popleft()
        source = target.read_text(encoding="utf-8")
        preview = embed_images(render_markdown(source), target.parent)
        prefix = previews[target] + "--"
        old_ids = ID.findall(preview)
        for old_id in old_ids:
            preview = preview.replace('id="' + old_id + '"', 'id="' + prefix + old_id + '"')
            preview = preview.replace('url(#' + old_id + ')', 'url(#' + prefix + old_id + ')')
            preview = preview.replace('href="#' + old_id + '"', 'href="#' + prefix + old_id + '"')
        rendered[target] = rewrite(preview, target)

    sections: list[str] = []
    for target, key in previews.items():
        peer = target.with_suffix(".html")
        html_link = (
            '<a class="document-preview-html" href="'
            + html.escape(browser_file_uri(peer), quote=True)
            + '">打开 HTML 阅读版</a>'
            if peer.is_file() else ""
        )
        local_path = html.escape(display_file_path(target))
        sections.append(
            '<main class="document-preview" id="' + key + '" tabindex="-1">'
            '<nav class="document-preview-bar" aria-label="文档预览导航">'
            '<a href="#lesson-content">返回目录</a>'
            '<span class="document-preview-label">Markdown 预览 · '
            + html.escape(target.name) + '</span>' + html_link + '</nav>'
            '<details class="document-preview-path"><summary>本地 Markdown 路径</summary>'
            '<code>' + local_path + '</code></details>'
            '<article>' + rendered[target] + '</article></main>'
        )
    scroll_script = """
<script>
(() => {
  function revealDocument() {
    const id = location.hash.slice(1);
    if (id !== 'lesson-content' && !id.startsWith('md-preview-')) return;
    requestAnimationFrame(() => {
      const target = document.getElementById(id);
      if (target) target.scrollIntoView({block: 'start', behavior: 'instant'});
    });
  }
  window.addEventListener('hashchange', revealDocument);
  window.addEventListener('pageshow', revealDocument);
})();
</script>
"""
    previews_html = "\n".join(sections) + (scroll_script if sections else "")
    return body, previews_html, PREVIEW_CSS if sections else ""
