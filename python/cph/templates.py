"""Solution templates: LeetCode's own snippet + a generated harness that reads one JSON value
per parameter from stdin, calls the method, and prints the result as JSON.

You only write the Solution method, exactly as on LeetCode.
"""
import re

SCALARS = {
    "integer": ("int", "int"),
    "long": ("long long", "int"),
    "double": ("double", "float"),
    "boolean": ("bool", "bool"),
    "string": ("string", "str"),
    "character": ("char", "str"),
}
NODES = {"listnode": "ListNode*", "treenode": "TreeNode*"}


class Unsupported(Exception):
    pass


def norm(t):
    return t.strip().lower()


def cpp_type(t):
    t = norm(t)
    if t.endswith("[]"):
        return f"vector<{cpp_type(t[:-2])}>"
    m = re.fullmatch(r"list<(.+)>", t)
    if m:
        return f"vector<{cpp_type(m.group(1))}>"
    if t in SCALARS:
        return SCALARS[t][0]
    if t in NODES:
        return NODES[t]
    raise Unsupported(f"type '{t}'")


def nodes_used(meta):
    types = [p["type"] for p in meta["params"]] + [meta["return"]["type"]]
    text = " ".join(norm(t) for t in types)
    return {"listnode": "listnode" in text, "treenode": "treenode" in text}


def supported(meta):
    """Function-style problems with known types get a harness; class-design ones don't."""
    if "classname" in meta or "params" not in meta or "return" not in meta:
        return False
    try:
        for p in meta["params"]:
            cpp_type(p["type"])
        if norm(meta["return"]["type"]) != "void":
            cpp_type(meta["return"]["type"])
    except Unsupported:
        return False
    return True


# --- C++ ---------------------------------------------------------------------------

CPP_PRELUDE = """#include <bits/stdc++.h>
using namespace std;
"""

CPP_LISTNODE = """struct ListNode {
    int val;
    ListNode *next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode *next) : val(x), next(next) {}
};
"""

CPP_TREENODE = """struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
};
"""

CPP_HARNESS_CORE = r"""namespace cph {
struct Reader {
    const string& s;
    size_t i = 0;
    explicit Reader(const string& line) : s(line) {}
    void ws() { while (i < s.size() && isspace((unsigned char)s[i])) ++i; }
    bool eat(char c) { ws(); if (i < s.size() && s[i] == c) { ++i; return true; } return false; }
    void expect(char c) { if (!eat(c)) throw runtime_error(string("cph: expected '") + c + "' in input line: " + s); }
    bool null() { ws(); if (s.compare(i, 4, "null") == 0) { i += 4; return true; } return false; }
    string token() { ws(); size_t j = i; while (i < s.size() && !strchr(",]} \t\r\n", s[i])) ++i; return s.substr(j, i - j); }
    string str() {
        expect('"');
        string out;
        while (i < s.size() && s[i] != '"') {
            if (s[i] == '\\' && i + 1 < s.size()) { char c = s[++i]; out += c == 'n' ? '\n' : c == 't' ? '\t' : c; }
            else out += s[i];
            ++i;
        }
        expect('"');
        return out;
    }
};
inline void read(Reader& r, int& x) { x = stoi(r.token()); }
inline void read(Reader& r, long long& x) { x = stoll(r.token()); }
inline void read(Reader& r, double& x) { x = stod(r.token()); }
inline void read(Reader& r, bool& x) { x = r.token() == "true"; }
inline void read(Reader& r, string& x) { x = r.str(); }
inline void read(Reader& r, char& x) { string t = r.str(); x = t.empty() ? '\0' : t[0]; }
inline void print(ostream& o, int x) { o << x; }
inline void print(ostream& o, long long x) { o << x; }
inline void print(ostream& o, double x) { o << fixed << setprecision(5) << x; }
inline void print(ostream& o, bool x) { o << (x ? "true" : "false"); }
inline void print(ostream& o, const string& x) {
    o << '"';
    for (char c : x) { if (c == '"' || c == '\\') o << '\\'; o << c; }
    o << '"';
}
inline void print(ostream& o, char x) { print(o, string(1, x)); }
"""

CPP_HARNESS_LIST = r"""inline void read(Reader& r, ListNode*& head) {
    r.expect('[');
    ListNode dummy;
    ListNode* tail = &dummy;
    if (!r.eat(']')) {
        do { int x; read(r, x); tail = tail->next = new ListNode(x); } while (r.eat(','));
        r.expect(']');
    }
    head = dummy.next;
}
inline void print(ostream& o, ListNode* head) {
    o << '[';
    for (bool first = true; head; head = head->next, first = false) { if (!first) o << ','; o << head->val; }
    o << ']';
}
"""

CPP_HARNESS_TREE = r"""inline void read(Reader& r, TreeNode*& root) {
    vector<TreeNode*> nodes;
    r.expect('[');
    if (!r.eat(']')) {
        do {
            if (r.null()) nodes.push_back(nullptr);
            else { int x; read(r, x); nodes.push_back(new TreeNode(x)); }
        } while (r.eat(','));
        r.expect(']');
    }
    root = nodes.empty() ? nullptr : nodes[0];
    size_t child = 1;  // level order: children of each non-null node, left to right
    for (size_t k = 0; k < nodes.size() && child < nodes.size(); ++k) {
        if (!nodes[k]) continue;
        nodes[k]->left = nodes[child++];
        if (child < nodes.size()) nodes[k]->right = nodes[child++];
    }
}
inline void print(ostream& o, TreeNode* root) {
    vector<string> out;
    queue<TreeNode*> q;
    q.push(root);
    while (!q.empty()) {
        TreeNode* n = q.front(); q.pop();
        if (!n) { out.push_back("null"); continue; }
        out.push_back(to_string(n->val));
        q.push(n->left);
        q.push(n->right);
    }
    while (!out.empty() && out.back() == "null") out.pop_back();
    o << '[';
    for (size_t k = 0; k < out.size(); ++k) { if (k) o << ','; o << out[k]; }
    o << ']';
}
"""

CPP_HARNESS_VECTOR = r"""template <class T> void read(Reader& r, vector<T>& v) {
    v.clear();
    r.expect('[');
    if (r.eat(']')) return;
    do { T x; read(r, x); v.push_back(x); } while (r.eat(','));
    r.expect(']');
}
template <class T> void print(ostream& o, const vector<T>& v) {
    o << '[';
    for (size_t k = 0; k < v.size(); ++k) { if (k) o << ','; print(o, (T)v[k]); }
    o << ']';
}
template <class T> T parse(const string& line) { Reader r(line); T x; read(r, x); return x; }
}  // namespace cph
"""

HARNESS_MARK = "===== cph harness (generated) — write your code above this line ====="


def _cpp_snippet(snippet):
    # LeetCode's snippet carries the node definitions as a comment; ours are real code above it.
    return snippet.strip() + "\n"


def cpp_template(meta, snippet):
    used = nodes_used(meta)
    head = CPP_PRELUDE
    head += CPP_LISTNODE if used["listnode"] else ""
    head += CPP_TREENODE if used["treenode"] else ""
    body = _cpp_snippet(snippet)

    harness = CPP_HARNESS_CORE
    harness += CPP_HARNESS_LIST if used["listnode"] else ""
    harness += CPP_HARNESS_TREE if used["treenode"] else ""
    harness += CPP_HARNESS_VECTOR

    lines = ["int main() {", "    string line;"]
    for k, p in enumerate(meta["params"]):
        lines.append(f"    getline(cin, line); auto p{k} = cph::parse<{cpp_type(p['type'])}>(line);")
    args = ", ".join(f"p{k}" for k in range(len(meta["params"])))
    lines.append("    Solution solution;")
    call = f"solution.{meta['name']}({args})"
    out_index = (meta.get("output") or {}).get("paramindex")
    if norm(meta["return"]["type"]) == "void":
        lines.append(f"    {call};")
        lines.append(f"    cph::print(cout, p{out_index});" if out_index is not None else '    cout << "null";')
    else:
        lines.append(f"    auto result = {call};")
        lines.append("    cph::print(cout, result);")
    lines += ["    cout << '\\n';", "}"]
    return f"{head}\n{body}\n// {HARNESS_MARK}\n{harness}\n" + "\n".join(lines) + "\n"


def cpp_fallback(snippet):
    note = ("// This problem's format isn't supported by the generated harness (class design or an\n"
            "// unusual type). Read the input lines from stdin and print the answer in LeetCode's format.\n")
    return CPP_PRELUDE + "\n" + note + "\n" + (snippet or "").strip() + "\n\nint main() {\n    \n}\n"


# --- Python ------------------------------------------------------------------------

PY_PRELUDE = """from typing import *  # noqa: F401,F403  (LeetCode signatures use List, Optional, ...)
"""

PY_LISTNODE = """class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
"""

PY_TREENODE = """class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
"""

PY_HARNESS = r'''import json as _json
import sys as _sys


def _cph_build(value, typ):
    typ = typ.strip().lower()
    if value is None:
        return None
    if typ == "listnode":
        head = tail = ListNode()
        for x in value:
            tail.next = ListNode(x)
            tail = tail.next
        return head.next
    if typ == "treenode":
        nodes = [None if x is None else TreeNode(x) for x in value]
        child = 1
        for node in nodes:
            if child >= len(nodes):
                break
            if node is None:
                continue
            node.left = nodes[child]
            child += 1
            if child < len(nodes):
                node.right = nodes[child]
                child += 1
        return nodes[0] if nodes else None
    if typ.endswith("[]") or typ.startswith("list<"):
        inner = typ[:-2] if typ.endswith("[]") else typ[5:-1]
        return [_cph_build(x, inner) for x in value]
    return value


def _cph_plain(value, typ):
    typ = typ.strip().lower()
    if value is None:
        return [] if typ in ("listnode", "treenode") else None  # an empty list/tree is None
    if typ == "listnode":
        out = []
        while value:
            out.append(value.val)
            value = value.next
        return out
    if typ == "treenode":
        out, queue = [], [value]
        while queue:
            node = queue.pop(0)
            if node is None:
                out.append(None)
                continue
            out.append(node.val)
            queue += [node.left, node.right]
        while out and out[-1] is None:
            out.pop()
        return out
    if typ.endswith("[]") or typ.startswith("list<"):
        inner = typ[:-2] if typ.endswith("[]") else typ[5:-1]
        return [_cph_plain(x, inner) for x in value]
    return value


def _cph_dump(value, typ):
    if typ.strip().lower() == "double" and value is not None:
        return f"{value:.5f}"
    return _json.dumps(_cph_plain(value, typ), separators=(",", ":"))
'''


def _py_snippet(snippet):
    # LeetCode's snippet stops where the method body starts (after the def line or a docstring).
    return snippet.rstrip() + "\n        pass\n"


def python_template(meta, snippet):
    used = nodes_used(meta)
    head = PY_PRELUDE
    head += ("\n\n" + PY_LISTNODE) if used["listnode"] else ""
    head += ("\n\n" + PY_TREENODE) if used["treenode"] else ""
    lines = ['if __name__ == "__main__":',
             '    _lines = _sys.stdin.read().split("\\n")']
    types = [p["type"] for p in meta["params"]]
    lines.append(f"    _types = {types!r}")
    lines.append("    _args = [_cph_build(_json.loads(_lines[k]), t) for k, t in enumerate(_types)]")
    lines.append(f"    _result = Solution().{meta['name']}(*_args)")
    out_index = (meta.get("output") or {}).get("paramindex")
    ret = meta["return"]["type"]
    if norm(ret) == "void":
        if out_index is not None:
            lines.append(f"    print(_cph_dump(_args[{out_index}], _types[{out_index}]))")
        else:
            lines.append('    print("null")')
    else:
        lines.append(f"    print(_cph_dump(_result, {ret!r}))")
    return (f"{head}\n\n{_py_snippet(snippet)}\n\n# {HARNESS_MARK}\n{PY_HARNESS}\n\n"
            + "\n".join(lines) + "\n")


def python_fallback(snippet):
    note = ("# This problem's format isn't supported by the generated harness (class design or an\n"
            "# unusual type). Read the input lines from stdin and print the answer in LeetCode's format.\n")
    return note + "\n" + (snippet or "").rstrip() + "\n"
