"""Fetch a LeetCode problem over GraphQL and turn its examples into test cases.

Inputs come from `exampleTestcaseList` (one JSON literal per parameter per line), which is
structured; only the expected outputs have to be read from the statement HTML.
"""
import html
import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

GRAPHQL = "https://leetcode.com/graphql"
QUERY = """
query problem($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId title titleSlug difficulty isPaidOnly content
    exampleTestcaseList metaData
    codeSnippets { lang langSlug code }
  }
}
"""
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ProblemError(Exception):
    """A problem the user can fix (bad slug, premium problem, network down)."""


def slug_from(text):
    """Accept 'two-sum' or any leetcode.com/problems/two-sum/... URL."""
    text = text.strip()
    m = re.search(r"leetcode\.com/problems/([^/?#]+)", text)
    slug = (m.group(1) if m else text).lower()
    if not SLUG.match(slug):
        raise ProblemError(f"'{text}' is not a problem slug like 'two-sum' or a LeetCode problem URL.")
    return slug


def fetch(slug, timeout=20):
    body = json.dumps({"query": QUERY, "variables": {"titleSlug": slug}}).encode()
    req = urllib.request.Request(GRAPHQL, data=body, headers={
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "User-Agent": "cph-leetcode-vscode",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProblemError(f"Couldn't reach LeetCode: {exc}") from exc
    question = (data.get("data") or {}).get("question")
    if not question:
        raise ProblemError(f"No LeetCode problem called '{slug}'.")
    if question.get("isPaidOnly") and not question.get("content"):
        raise ProblemError(f"'{question['title']}' is a premium problem; its statement isn't public.")
    return question


class _Text(HTMLParser):
    """HTML -> plain text, keeping line breaks at block boundaries."""

    BLOCK = {"p", "pre", "div", "li", "br", "ul", "ol"}

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCK:
            self.parts.append("\n")
        elif tag == "sup":
            self.parts.append("^")  # 10<sup>4</sup> -> 10^4, so constraint bounds survive

    def handle_endtag(self, tag):
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def statement_text(content_html):
    parser = _Text()
    parser.feed(content_html or "")
    text = html.unescape("".join(parser.parts)).replace("\xa0", " ")
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


OUTPUT = re.compile(r"Output:?\s*(.+?)\s*(?=\n|Explanation:|$)", re.S)


def example_outputs(content_html):
    return [m.group(1).strip() for m in OUTPUT.finditer(statement_text(content_html))]


def constraints(content_html):
    text = statement_text(content_html)
    _, _, tail = text.partition("Constraints:")
    lines = [l.strip(" .•\t") for l in tail.splitlines()]
    return [l for l in lines if any(op in l for op in ("<", "≤", "=="))]


def alphabet(content_html):
    """Characters strings are made of, from a 'consists of ...' constraint, if it names them."""
    _, _, tail = statement_text(content_html).partition("Constraints:")
    for line in tail.splitlines():
        if "consist" not in line:
            continue
        quoted = re.findall(r"'([^']+)'", line)
        if quoted:
            return "".join(dict.fromkeys("".join(quoted)))  # keep order, drop duplicates
        if "digit" in line and "letter" not in line:
            return "0123456789"
    return None


def tests_from(question, meta):
    """Pair each example input with its output. Inputs are split into one line per parameter."""
    n_params = len(meta.get("params", []))
    raw = question.get("exampleTestcaseList") or []
    outputs = example_outputs(question.get("content"))
    tests = []
    for i, block in enumerate(raw):
        lines = block.split("\n")
        if n_params and len(lines) != n_params:
            continue  # class-design problems pack calls differently; handled by the caller
        tests.append({"input": lines, "output": outputs[i] if i < len(outputs) else None})
    return tests


def snippet(question, lang_slug):
    for s in question.get("codeSnippets") or []:
        if s["langSlug"] == lang_slug:
            return s["code"]
    return None
