#!/usr/bin/env python3
"""Telegraph publishing CLI — stdlib only, pipe-friendly.

Usage:
    echo '<p>Hello</p>' | python3 publish.py create --title "My Page"
    python3 publish.py create --title "Page" --file report.md
    python3 publish.py edit --path "Title-03-08" --title "Updated" --file new.html
    python3 publish.py get --path "Title-03-08"
    python3 publish.py list
    python3 publish.py upload --file image.png
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

API_BASE = "https://api.telegra.ph"
TOKEN_PATH = Path(__file__).parent / "token.txt"

# Tags supported by Telegraph
TELEGRAPH_TAGS = frozenset(
    "a aside b blockquote br code em figcaption figure "
    "h3 h4 hr i iframe img li ol p pre s strong u ul".split()
)
# Heading remapping
HEADING_MAP = {"h1": "h3", "h2": "h3", "h5": "h4", "h6": "h4"}
# Tags whose children pass through (unwrapped)
PASSTHROUGH_TAGS = frozenset("div span section article main header footer nav".split())
# Table-related tags (handled separately)
TABLE_TAGS = frozenset("table thead tbody tfoot tr th td caption colgroup col".split())
# Format auto-detection by file extension
FORMAT_BY_EXT = {
    ".md": "markdown", ".markdown": "markdown",
    ".html": "html", ".htm": "html",
    ".txt": "text",
}


# ── Table formatting ─────────────────────────────────────────────────

def _format_table_mono(rows: list[list[str]], header_idx: int = -1) -> str:
    """Format table rows as monospace text with box-drawing borders."""
    if not rows:
        return ""
    n_cols = max(len(r) for r in rows)
    widths = [0] * n_cols
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell.strip()))
    widths = [max(w, 1) for w in widths]

    def sep(left, mid, right, fill="─"):
        return left + mid.join(fill * (w + 2) for w in widths) + right

    lines = [sep("┌", "┬", "┐")]
    for idx, row in enumerate(rows):
        cells = []
        for i in range(n_cols):
            val = row[i].strip() if i < len(row) else ""
            cells.append(f" {val:<{widths[i]}} ")
        lines.append("│" + "│".join(cells) + "│")
        if idx == header_idx:
            lines.append(sep("├", "┼", "┤"))
    lines.append(sep("└", "┴", "┘"))
    return "\n".join(lines)


# ── HTML → Telegraph Nodes ──────────────────────────────────────────

class _NodeBuilder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result: list = []
        self._stack: list[list] = [self.result]
        # Table buffering
        self._in_table = False
        self._table_rows: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []
        self._header_row_idx = -1
        self._in_thead = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        # Table handling — buffer everything inside <table>
        if tag == "table":
            self._in_table = True
            self._table_rows = []
            self._header_row_idx = -1
            self._in_thead = False
            return
        if self._in_table:
            if tag == "thead":
                self._in_thead = True
            elif tag == "tr":
                self._current_row = []
                self._current_cell = []
            elif tag in ("td", "th"):
                self._current_cell = []
                if tag == "th" or self._in_thead:
                    self._header_row_idx = len(self._table_rows)
            return

        tag = HEADING_MAP.get(tag, tag)
        if tag in PASSTHROUGH_TAGS:
            return  # children go to current parent
        if tag in ("br", "hr"):
            self._stack[-1].append({"tag": tag})
            return
        if tag not in TELEGRAPH_TAGS:
            return  # skip unsupported
        node: dict = {"tag": tag}
        attr_dict = {}
        for k, v in attrs:
            if k in ("href", "src") and v:
                attr_dict[k] = v
        if attr_dict:
            node["attrs"] = attr_dict
        node["children"] = []
        self._stack[-1].append(node)
        self._stack.append(node["children"])

    def handle_endtag(self, tag: str):
        if tag == "table" and self._in_table:
            self._in_table = False
            if self._table_rows:
                mono = _format_table_mono(self._table_rows, self._header_row_idx)
                self._stack[-1].append({"tag": "pre", "children": [mono]})
            return
        if self._in_table:
            if tag == "thead":
                self._in_thead = False
            elif tag in ("td", "th"):
                self._current_row.append("".join(self._current_cell))
                self._current_cell = []
            elif tag == "tr":
                if self._current_row:
                    self._table_rows.append(self._current_row)
                self._current_row = []
            return

        tag = HEADING_MAP.get(tag, tag)
        if tag in PASSTHROUGH_TAGS or tag in ("br", "hr"):
            return
        if tag not in TELEGRAPH_TAGS:
            return
        if len(self._stack) > 1:
            self._stack.pop()

    def handle_data(self, data: str):
        if self._in_table:
            self._current_cell.append(data)
            return
        if data:
            self._stack[-1].append(data)


def html_to_nodes(html: str) -> list:
    """Convert HTML string to Telegraph Node array."""
    builder = _NodeBuilder()
    builder.feed(html)
    return _clean_nodes(builder.result)


def _clean_nodes(nodes: list) -> list:
    """Remove empty text nodes and childless elements."""
    cleaned = []
    for node in nodes:
        if isinstance(node, str):
            if node.strip():
                cleaned.append(node)
        elif isinstance(node, dict):
            if "children" in node:
                node["children"] = _clean_nodes(node["children"])
                if not node["children"]:
                    del node["children"]
            cleaned.append(node)
    return cleaned


# ── Markdown → Telegraph Nodes ──────────────────────────────────────

def markdown_to_nodes(md: str) -> list:
    """Convert Markdown to Telegraph Node array via intermediate HTML."""
    html = _md_to_html(md)
    return html_to_nodes(html)


def _md_to_html(md: str) -> str:
    lines = md.strip().split("\n")
    html_parts: list[str] = []
    i = 0
    in_list = None  # "ul" or "ol"

    while i < len(lines):
        line = lines[i]

        # Fenced code blocks
        if line.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code = "\n".join(code_lines)
            _close_list(html_parts, in_list)
            in_list = None
            html_parts.append(f"<pre>{_escape(code)}</pre>")
            continue

        # Pipe table
        if "|" in line and _is_table_start(lines, i):
            _close_list(html_parts, in_list)
            in_list = None
            table_rows = []
            header_idx = -1
            while i < len(lines) and "|" in lines[i]:
                stripped = lines[i].strip()
                if re.match(r"^\|?\s*[-:]+[-| :]*$", stripped):
                    header_idx = len(table_rows) - 1  # previous row was header
                    i += 1
                    continue
                cells = _parse_table_row(stripped)
                table_rows.append(cells)
                i += 1
            mono = _format_table_mono(table_rows, header_idx)
            html_parts.append(f"<pre>{_escape(mono)}</pre>")
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            tag = "h3" if level <= 3 else "h4"
            _close_list(html_parts, in_list)
            in_list = None
            html_parts.append(f"<{tag}>{_inline(m.group(2))}</{tag}>")
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^(-{3,}|_{3,}|\*{3,})\s*$", line):
            _close_list(html_parts, in_list)
            in_list = None
            html_parts.append("<hr>")
            i += 1
            continue

        # Blockquote
        if line.startswith("> "):
            _close_list(html_parts, in_list)
            in_list = None
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:])
                i += 1
            html_parts.append(f"<blockquote>{_inline(' '.join(quote_lines))}</blockquote>")
            continue

        # Unordered list
        m = re.match(r"^[\-\*]\s+(.*)", line)
        if m:
            if in_list != "ul":
                _close_list(html_parts, in_list)
                html_parts.append("<ul>")
                in_list = "ul"
            html_parts.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue

        # Ordered list
        m = re.match(r"^\d+\.\s+(.*)", line)
        if m:
            if in_list != "ol":
                _close_list(html_parts, in_list)
                html_parts.append("<ol>")
                in_list = "ol"
            html_parts.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue

        # Empty line
        if not line.strip():
            _close_list(html_parts, in_list)
            in_list = None
            i += 1
            continue

        # Paragraph (collect consecutive non-empty lines)
        _close_list(html_parts, in_list)
        in_list = None
        para_lines = []
        while i < len(lines) and lines[i].strip() and not _is_block(lines[i]):
            para_lines.append(lines[i])
            i += 1
        html_parts.append(f"<p>{_inline(' '.join(para_lines))}</p>")

    _close_list(html_parts, in_list)
    return "\n".join(html_parts)


def _is_table_start(lines: list[str], i: int) -> bool:
    """Check if current position starts a pipe table (separator on next line)."""
    if i + 1 >= len(lines):
        return False
    return bool(re.match(r"^\|?\s*[-:]+[-| :]*$", lines[i + 1].strip()))


def _parse_table_row(line: str) -> list[str]:
    """Parse pipe-delimited table row into cells."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _is_block(line: str) -> bool:
    """Check if line starts a block element."""
    if line.startswith(("#", ">", "```", "---", "***", "___")):
        return True
    if re.match(r"^[\-\*]\s+", line):
        return True
    if re.match(r"^\d+\.\s+", line):
        return True
    return False


def _close_list(parts: list, tag: str | None):
    if tag:
        parts.append(f"</{tag}>")


def _inline(text: str) -> str:
    """Convert inline Markdown to HTML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # Images before links (![...] vs [...])
    text = re.sub(r"!\[([^\]]*)\]\((.+?)\)", r'<img src="\2">', text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Text → Telegraph Nodes ──────────────────────────────────────────

def text_to_nodes(text: str) -> list:
    """Convert plain text to Telegraph nodes (paragraphs)."""
    nodes = []
    for para in text.strip().split("\n\n"):
        lines = para.strip().replace("\n", " ")
        if lines:
            nodes.append({"tag": "p", "children": [lines]})
    return nodes


# ── Image upload ─────────────────────────────────────────────────────

def upload_image(file_path: str) -> str:
    """Upload image to Telegraph, return full URL."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    boundary = f"----TelegraphBoundary{os.urandom(8).hex()}"
    mime = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp", ".mp4": "video/mp4",
    }.get(path.suffix.lower(), "application/octet-stream")

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        "https://telegra.ph/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())

    if isinstance(result, list) and result:
        return "https://telegra.ph" + result[0]["src"]
    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError(result["error"])
    raise RuntimeError("Unexpected upload response")


# ── Auto-split ───────────────────────────────────────────────────────

def _split_nodes(nodes: list, max_bytes: int = 60_000) -> list[list]:
    """Split node list into chunks fitting within max_bytes when serialized."""
    if len(json.dumps(nodes).encode()) <= max_bytes:
        return [nodes]

    chunks = []
    current: list = []
    current_size = 2  # for '[]'

    for node in nodes:
        node_size = len(json.dumps(node).encode()) + 1  # +1 for comma
        if current and current_size + node_size > max_bytes:
            chunks.append(current)
            current = []
            current_size = 2
        current.append(node)
        current_size += node_size

    if current:
        chunks.append(current)
    return chunks


def _add_nav_links(chunks: list[list], urls: list[str]):
    """Append navigation links to each chunk (mutates in place)."""
    for idx, chunk in enumerate(chunks):
        nav: list = []
        if idx > 0:
            nav.append({"tag": "a", "attrs": {"href": urls[idx - 1]},
                         "children": [f"\u2190 \u0427\u0430\u0441\u0442\u044c {idx}"]})
        if idx < len(chunks) - 1:
            if nav:
                nav.append("  \u00b7  ")
            nav.append({"tag": "a", "attrs": {"href": urls[idx + 1]},
                         "children": [f"\u0427\u0430\u0441\u0442\u044c {idx + 2} \u2192"]})
        if nav:
            chunk.append({"tag": "hr"})
            chunk.append({"tag": "p", "children": nav})


# ── Telegraph API ────────────────────────────────────────────────────

def api_call(method: str, **params) -> dict:
    """Call Telegraph API method."""
    data = urllib.parse.urlencode(
        {k: v if isinstance(v, str) else json.dumps(v) for k, v in params.items() if v is not None}
    ).encode()
    req = urllib.request.Request(f"{API_BASE}/{method}", data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown Telegraph API error"))
    return result["result"]


def load_token() -> str | None:
    """Load token from file."""
    if TOKEN_PATH.exists():
        token = TOKEN_PATH.read_text().strip()
        if token:
            return token
    return os.environ.get("TELEGRAPH_ACCESS_TOKEN")


def save_token(token: str):
    """Save token to file."""
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(token + "\n")


def ensure_token() -> str:
    """Load or create token."""
    token = load_token()
    if token:
        return token
    account = api_call("createAccount", short_name="claude_code", author_name="Claude Code")
    token = account["access_token"]
    save_token(token)
    print(json.dumps({"event": "account_created", "short_name": "claude_code"}), file=sys.stderr)
    return token


# ── Content conversion ───────────────────────────────────────────────

def detect_format(file_path: str | None, explicit_format: str | None) -> str:
    """Detect content format from file extension or use explicit format."""
    if explicit_format:
        return explicit_format
    if file_path:
        ext = Path(file_path).suffix.lower()
        fmt = FORMAT_BY_EXT.get(ext)
        if fmt:
            return fmt
    return "html"


def convert_content(content: str, fmt: str) -> list:
    """Convert content string to Telegraph nodes."""
    if fmt == "html":
        return html_to_nodes(content)
    elif fmt == "markdown":
        return markdown_to_nodes(content)
    elif fmt == "text":
        return text_to_nodes(content)
    else:
        raise ValueError(f"Unknown format: {fmt}. Use html, markdown, or text.")


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Publish to telegra.ph")
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Create a new page")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--format", default=None, choices=["html", "markdown", "text"],
                          help="Content format (auto-detected from --file extension if omitted)")
    p_create.add_argument("--file", help="Read content from file instead of stdin")
    p_create.add_argument("--author-name", default="Claude Code")
    p_create.add_argument("--author-url", default=None)

    # edit
    p_edit = sub.add_parser("edit", help="Edit existing page")
    p_edit.add_argument("--path", required=True, help="Page path from URL")
    p_edit.add_argument("--title", required=True)
    p_edit.add_argument("--format", default=None, choices=["html", "markdown", "text"],
                        help="Content format (auto-detected from --file extension if omitted)")
    p_edit.add_argument("--file", help="Read content from file instead of stdin")
    p_edit.add_argument("--author-name", default=None)
    p_edit.add_argument("--author-url", default=None)

    # get
    p_get = sub.add_parser("get", help="Get page info")
    p_get.add_argument("--path", required=True)
    p_get.add_argument("--return-content", action="store_true")

    # list
    p_list = sub.add_parser("list", help="List created pages")
    p_list.add_argument("--offset", type=int, default=0)
    p_list.add_argument("--limit", type=int, default=50)

    # upload
    p_upload = sub.add_parser("upload", help="Upload image to Telegraph")
    p_upload.add_argument("--file", required=True, help="Image file path")

    args = parser.parse_args()

    try:
        if args.command == "create":
            content = Path(args.file).read_text() if args.file else sys.stdin.read()
            fmt = detect_format(args.file, args.format)
            nodes = convert_content(content, fmt)

            # Auto-split if content exceeds 64KB
            chunks = _split_nodes(nodes)
            token = ensure_token()

            if len(chunks) == 1:
                page = api_call(
                    "createPage",
                    access_token=token,
                    title=args.title,
                    content=chunks[0],
                    author_name=args.author_name,
                    author_url=args.author_url,
                    return_content="false",
                )
                print(json.dumps({"ok": True, "url": page["url"], "path": page["path"]}))
            else:
                # Multi-part: create all pages, then add navigation links
                pages = []
                for idx, chunk in enumerate(chunks, 1):
                    part_title = f"{args.title} ({idx}/{len(chunks)})"
                    page = api_call(
                        "createPage",
                        access_token=token,
                        title=part_title,
                        content=chunk,
                        author_name=args.author_name,
                        author_url=args.author_url,
                        return_content="false",
                    )
                    pages.append(page)
                urls = [p["url"] for p in pages]
                _add_nav_links(chunks, urls)
                for idx, page in enumerate(pages):
                    api_call(
                        "editPage",
                        access_token=token,
                        path=page["path"],
                        title=page["title"],
                        content=chunks[idx],
                        return_content="false",
                    )
                print(json.dumps({
                    "ok": True,
                    "parts": len(pages),
                    "url": pages[0]["url"],
                    "urls": urls,
                }))

        elif args.command == "edit":
            content = Path(args.file).read_text() if args.file else sys.stdin.read()
            fmt = detect_format(args.file, args.format)
            nodes = convert_content(content, fmt)
            token = ensure_token()
            edit_params = dict(
                access_token=token,
                path=args.path,
                title=args.title,
                content=nodes,
                return_content="false",
            )
            if args.author_name:
                edit_params["author_name"] = args.author_name
            if args.author_url:
                edit_params["author_url"] = args.author_url
            page = api_call("editPage", **edit_params)
            print(json.dumps({"ok": True, "url": page["url"], "path": page["path"]}))

        elif args.command == "get":
            page = api_call(
                "getPage",
                path=args.path,
                return_content="true" if args.return_content else "false",
            )
            print(json.dumps({"ok": True, "page": page}))

        elif args.command == "list":
            token = ensure_token()
            result = api_call(
                "getPageList",
                access_token=token,
                offset=str(args.offset),
                limit=str(args.limit),
            )
            pages = result.get("pages", [])
            print(json.dumps({
                "ok": True,
                "total_count": result.get("total_count", 0),
                "pages": [
                    {"title": p["title"], "url": p["url"], "path": p["path"],
                     "views": p.get("views", 0)}
                    for p in pages
                ],
            }))

        elif args.command == "upload":
            url = upload_image(args.file)
            print(json.dumps({"ok": True, "url": url}))

    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
