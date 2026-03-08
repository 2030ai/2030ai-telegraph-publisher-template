"""Tests for publish.py — converters, split, format detection."""
import json
import unittest

from publish import (
    _format_table_mono,
    _split_large_node,
    _split_nodes,
    _add_nav_links,
    convert_content,
    detect_format,
    html_to_nodes,
    markdown_to_nodes,
    text_to_nodes,
)


class TestMarkdownLiteralHTML(unittest.TestCase):
    """Literal HTML in markdown should be escaped, not parsed as tags."""

    def test_literal_div_in_paragraph(self):
        nodes = markdown_to_nodes("Use <div> for layout")
        text = nodes[0]["children"][0]
        self.assertIn("<div>", text)
        self.assertNotIn({"tag": "div"}, nodes)

    def test_literal_script_tag(self):
        nodes = markdown_to_nodes("Inject <script>alert(1)</script> here")
        text = nodes[0]["children"][0]
        self.assertIn("<script>", text)

    def test_angle_brackets_in_heading(self):
        nodes = markdown_to_nodes("## Array<String> type")
        self.assertEqual(nodes[0]["tag"], "h3")
        text = nodes[0]["children"][0]
        self.assertIn("<String>", text)

    def test_angle_brackets_in_list(self):
        nodes = markdown_to_nodes("- Use <b> tag carefully")
        li = nodes[0]["children"][0]  # ul > li
        text = li["children"][0]
        self.assertIn("<b>", text)

    def test_ampersand_in_text(self):
        nodes = markdown_to_nodes("Tom & Jerry")
        text = nodes[0]["children"][0]
        self.assertIn("&", text)
        self.assertNotIn("&amp;", text)  # final nodes have decoded text

    def test_link_with_ampersand(self):
        nodes = markdown_to_nodes("[search](https://x.com?a=1&b=2)")
        a = nodes[0]["children"][0]
        self.assertEqual(a["tag"], "a")
        self.assertEqual(a["attrs"]["href"], "https://x.com?a=1&b=2")


class TestMarkdownInline(unittest.TestCase):
    def test_bold(self):
        nodes = markdown_to_nodes("This is **bold** text")
        children = nodes[0]["children"]
        self.assertTrue(any(
            isinstance(c, dict) and c.get("tag") == "b"
            for c in children
        ))

    def test_italic(self):
        nodes = markdown_to_nodes("This is *italic* text")
        children = nodes[0]["children"]
        self.assertTrue(any(
            isinstance(c, dict) and c.get("tag") == "i"
            for c in children
        ))

    def test_strikethrough(self):
        nodes = markdown_to_nodes("This is ~~deleted~~ text")
        children = nodes[0]["children"]
        self.assertTrue(any(
            isinstance(c, dict) and c.get("tag") == "s"
            for c in children
        ))

    def test_inline_code(self):
        nodes = markdown_to_nodes("Run `npm install` now")
        children = nodes[0]["children"]
        self.assertTrue(any(
            isinstance(c, dict) and c.get("tag") == "code"
            for c in children
        ))

    def test_image_before_link(self):
        nodes = markdown_to_nodes("![alt](img.png) and [text](url)")
        children = nodes[0]["children"]
        tags = [c["tag"] for c in children if isinstance(c, dict)]
        self.assertIn("img", tags)
        self.assertIn("a", tags)


class TestMarkdownBlocks(unittest.TestCase):
    def test_code_block(self):
        md = "```\nprint('hello')\n```"
        nodes = markdown_to_nodes(md)
        self.assertEqual(nodes[0]["tag"], "pre")
        self.assertIn("print", nodes[0]["children"][0])

    def test_blockquote(self):
        nodes = markdown_to_nodes("> Important note")
        self.assertEqual(nodes[0]["tag"], "blockquote")

    def test_horizontal_rule(self):
        nodes = markdown_to_nodes("---")
        self.assertEqual(nodes[0]["tag"], "hr")

    def test_unordered_list(self):
        nodes = markdown_to_nodes("- one\n- two\n- three")
        self.assertEqual(nodes[0]["tag"], "ul")
        self.assertEqual(len(nodes[0]["children"]), 3)

    def test_ordered_list(self):
        nodes = markdown_to_nodes("1. first\n2. second")
        self.assertEqual(nodes[0]["tag"], "ol")
        self.assertEqual(len(nodes[0]["children"]), 2)

    def test_heading_levels(self):
        nodes = markdown_to_nodes("# H1\n## H2\n### H3\n#### H4\n##### H5")
        tags = [n["tag"] for n in nodes]
        self.assertEqual(tags, ["h3", "h3", "h3", "h4", "h4"])


class TestMarkdownTable(unittest.TestCase):
    def test_pipe_table_to_pre(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        nodes = markdown_to_nodes(md)
        self.assertEqual(nodes[0]["tag"], "pre")
        text = nodes[0]["children"][0]
        self.assertIn("┌", text)
        self.assertIn("│", text)
        self.assertIn("┘", text)

    def test_table_header_separator(self):
        md = "| Name | Age |\n|------|-----|\n| Alice | 30 |"
        nodes = markdown_to_nodes(md)
        text = nodes[0]["children"][0]
        self.assertIn("├", text)  # header separator present
        self.assertIn("┼", text)

    def test_table_preserves_content(self):
        md = "| X | Y |\n|---|---|\n| hello | world |"
        nodes = markdown_to_nodes(md)
        text = nodes[0]["children"][0]
        self.assertIn("hello", text)
        self.assertIn("world", text)


class TestHTMLTable(unittest.TestCase):
    def test_simple_table(self):
        html = "<table><tr><td>A</td><td>B</td></tr></table>"
        nodes = html_to_nodes(html)
        self.assertEqual(nodes[0]["tag"], "pre")
        self.assertIn("A", nodes[0]["children"][0])

    def test_table_with_thead(self):
        html = ("<table><thead><tr><th>H1</th><th>H2</th></tr></thead>"
                "<tbody><tr><td>a</td><td>b</td></tr></tbody></table>")
        nodes = html_to_nodes(html)
        text = nodes[0]["children"][0]
        self.assertIn("├", text)  # header separator
        self.assertIn("H1", text)
        self.assertIn("a", text)


class TestHTMLHeadingRemap(unittest.TestCase):
    def test_h1_to_h3(self):
        nodes = html_to_nodes("<h1>Title</h1>")
        self.assertEqual(nodes[0]["tag"], "h3")

    def test_h6_to_h4(self):
        nodes = html_to_nodes("<h6>Small</h6>")
        self.assertEqual(nodes[0]["tag"], "h4")


class TestHTMLPassthrough(unittest.TestCase):
    def test_div_unwrapped(self):
        nodes = html_to_nodes("<div><p>Hello</p></div>")
        self.assertEqual(nodes[0]["tag"], "p")
        self.assertEqual(nodes[0]["children"], ["Hello"])


class TestTextToNodes(unittest.TestCase):
    def test_paragraphs(self):
        nodes = text_to_nodes("First para\n\nSecond para")
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0]["tag"], "p")
        self.assertEqual(nodes[1]["children"], ["Second para"])

    def test_empty_input(self):
        nodes = text_to_nodes("")
        self.assertEqual(nodes, [])


class TestFormatDetection(unittest.TestCase):
    def test_md_extension(self):
        self.assertEqual(detect_format("report.md", None), "markdown")

    def test_markdown_extension(self):
        self.assertEqual(detect_format("report.markdown", None), "markdown")

    def test_html_extension(self):
        self.assertEqual(detect_format("page.html", None), "html")

    def test_htm_extension(self):
        self.assertEqual(detect_format("page.htm", None), "html")

    def test_txt_extension(self):
        self.assertEqual(detect_format("notes.txt", None), "text")

    def test_unknown_extension_defaults_html(self):
        self.assertEqual(detect_format("data.csv", None), "html")

    def test_no_file_defaults_html(self):
        self.assertEqual(detect_format(None, None), "html")

    def test_explicit_overrides_extension(self):
        self.assertEqual(detect_format("file.md", "html"), "html")


class TestTableFormatMono(unittest.TestCase):
    def test_basic_table(self):
        result = _format_table_mono([["A", "B"], ["1", "2"]])
        self.assertIn("┌", result)
        self.assertIn("└", result)
        self.assertNotIn("├", result)  # no header

    def test_with_header(self):
        result = _format_table_mono([["Name", "Age"], ["Alice", "30"]], header_idx=0)
        self.assertIn("├", result)
        self.assertIn("┼", result)

    def test_empty_rows(self):
        result = _format_table_mono([])
        self.assertEqual(result, "")

    def test_uneven_columns(self):
        result = _format_table_mono([["A", "B", "C"], ["1", "2"]])
        lines = result.split("\n")
        # All lines should have same length (proper padding)
        lengths = {len(line) for line in lines}
        self.assertEqual(len(lengths), 1)


class TestSplitNodes(unittest.TestCase):
    def test_small_content_no_split(self):
        nodes = [{"tag": "p", "children": ["Hello"]}]
        chunks = _split_nodes(nodes)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], nodes)

    def test_large_content_splits(self):
        nodes = [{"tag": "p", "children": ["x" * 1000]} for _ in range(100)]
        chunks = _split_nodes(nodes, max_bytes=30_000)
        self.assertGreater(len(chunks), 1)
        # Each chunk should be under the limit
        for chunk in chunks:
            self.assertLessEqual(len(json.dumps(chunk).encode()), 30_000)

    def test_all_nodes_preserved(self):
        nodes = [{"tag": "p", "children": [f"node-{i}"]} for i in range(50)]
        chunks = _split_nodes(nodes, max_bytes=5_000)
        recombined = []
        for chunk in chunks:
            recombined.extend(chunk)
        self.assertEqual(len(recombined), len(nodes))


class TestSplitLargeNode(unittest.TestCase):
    def test_split_large_pre(self):
        text = "\n".join(f"line {i}: {'x' * 100}" for i in range(1000))
        node = {"tag": "pre", "children": [text]}
        parts = _split_large_node(node, max_bytes=10_000)
        self.assertGreater(len(parts), 1)
        # All parts should be pre tags
        for part in parts:
            self.assertEqual(part["tag"], "pre")
        # Reassembled text should match (minus joins)
        all_lines = []
        for part in parts:
            all_lines.extend(part["children"][0].split("\n"))
        self.assertEqual(len(all_lines), 1000)

    def test_small_node_unchanged(self):
        node = {"tag": "pre", "children": ["small text"]}
        parts = _split_large_node(node, max_bytes=60_000)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], node)

    def test_non_pre_node_unchanged(self):
        node = {"tag": "p", "children": ["x" * 100_000]}
        parts = _split_large_node(node, max_bytes=1_000)
        self.assertEqual(len(parts), 1)  # can't split non-pre


class TestNavLinks(unittest.TestCase):
    def test_nav_links_added(self):
        chunks = [
            [{"tag": "p", "children": ["part 1"]}],
            [{"tag": "p", "children": ["part 2"]}],
            [{"tag": "p", "children": ["part 3"]}],
        ]
        urls = ["url1", "url2", "url3"]
        _add_nav_links(chunks, urls)

        # First chunk: only "next" link
        nav_first = chunks[0][-1]
        self.assertEqual(nav_first["tag"], "p")
        # Has link to part 2
        links = [c for c in nav_first["children"] if isinstance(c, dict)]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["attrs"]["href"], "url2")

        # Middle chunk: both links
        nav_mid = chunks[1][-1]
        links = [c for c in nav_mid["children"] if isinstance(c, dict)]
        self.assertEqual(len(links), 2)

        # Last chunk: only "prev" link
        nav_last = chunks[2][-1]
        links = [c for c in nav_last["children"] if isinstance(c, dict)]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["attrs"]["href"], "url2")

    def test_single_chunk_no_nav(self):
        chunks = [[{"tag": "p", "children": ["only part"]}]]
        urls = ["url1"]
        original_len = len(chunks[0])
        _add_nav_links(chunks, urls)
        self.assertEqual(len(chunks[0]), original_len)  # nothing added


class TestConvertContent(unittest.TestCase):
    def test_html_format(self):
        nodes = convert_content("<p>Hello</p>", "html")
        self.assertEqual(nodes[0]["tag"], "p")

    def test_markdown_format(self):
        nodes = convert_content("**bold**", "markdown")
        self.assertTrue(any(
            isinstance(c, dict) and c.get("tag") == "b"
            for c in nodes[0]["children"]
        ))

    def test_text_format(self):
        nodes = convert_content("Just text", "text")
        self.assertEqual(nodes[0]["tag"], "p")

    def test_unknown_format_raises(self):
        with self.assertRaises(ValueError):
            convert_content("content", "xml")


if __name__ == "__main__":
    unittest.main()
