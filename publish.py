#!/usr/bin/env python3
"""Telegraph publishing CLI — stdlib only, pipe-friendly.

Usage:
    echo '<p>Hello</p>' | python3 publish.py create --title "My Page"
    python3 publish.py create --title "Page" --file report.html
    python3 publish.py create --title "Page" --format markdown --file notes.md
    python3 publish.py edit --path "Title-03-08" --title "Updated" --file new.html
    python3 publish.py get --path "Title-03-08"
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


# ── HTML → Telegraph Nodes ──────────────────────────────────────────

class _NodeBuilder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result: list = []
        self._stack: list[list] = [self.result]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        tag = HEADING_MAP.get(tag, tag)
        if tag in PASSTHROUGH_TAGS:
            return  # children go to current parent
        if tag == "br":
            self._stack[-1].append({"tag": "br"})
            return
        if tag == "hr":
            self._stack[-1].append({"tag": "hr"})
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
        tag = HEADING_MAP.get(tag, tag)
        if tag in PASSTHROUGH_TAGS or tag in ("br", "hr"):
            return
        if tag not in TELEGRAPH_TAGS:
            return
        if len(self._stack) > 1:
            self._stack.pop()

    def handle_data(self, data: str):
        text = data
        if text:
            self._stack[-1].append(text)


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
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", text)
    # Strikethrough
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)
    # Code
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # Links
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    # Images
    text = re.sub(r"!\[([^\]]*)\]\((.+?)\)", r'<img src="\2">', text)
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
    p_create.add_argument("--format", default="html", choices=["html", "markdown", "text"])
    p_create.add_argument("--file", help="Read content from file instead of stdin")
    p_create.add_argument("--author-name", default="Claude Code")
    p_create.add_argument("--author-url", default=None)

    # edit
    p_edit = sub.add_parser("edit", help="Edit existing page")
    p_edit.add_argument("--path", required=True, help="Page path from URL")
    p_edit.add_argument("--title", required=True)
    p_edit.add_argument("--format", default="html", choices=["html", "markdown", "text"])
    p_edit.add_argument("--file", help="Read content from file instead of stdin")

    # get
    p_get = sub.add_parser("get", help="Get page info")
    p_get.add_argument("--path", required=True)
    p_get.add_argument("--return-content", action="store_true")

    args = parser.parse_args()

    try:
        if args.command == "create":
            content = Path(args.file).read_text() if args.file else sys.stdin.read()
            nodes = convert_content(content, args.format)
            # Check 64KB limit
            serialized = json.dumps(nodes)
            if len(serialized.encode()) > 64 * 1024:
                print(json.dumps({"ok": False, "error": "Content exceeds 64KB limit"}))
                sys.exit(1)
            token = ensure_token()
            page = api_call(
                "createPage",
                access_token=token,
                title=args.title,
                content=nodes,
                author_name=args.author_name,
                author_url=args.author_url,
                return_content="false",
            )
            print(json.dumps({"ok": True, "url": page["url"], "path": page["path"]}))

        elif args.command == "edit":
            content = Path(args.file).read_text() if args.file else sys.stdin.read()
            nodes = convert_content(content, args.format)
            token = ensure_token()
            page = api_call(
                "editPage",
                access_token=token,
                path=args.path,
                title=args.title,
                content=nodes,
                return_content="false",
            )
            print(json.dumps({"ok": True, "url": page["url"], "path": page["path"]}))

        elif args.command == "get":
            page = api_call(
                "getPage",
                path=args.path,
                return_content="true" if args.return_content else "false",
            )
            print(json.dumps({"ok": True, "page": page}))

    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
