"""Stress testing: random inputs, your solution vs a brute force, until they disagree.

Inputs come from the problem's gen.py, which `cph fetch` pre-fills from the parameter types
and constraint lines ('2 <= nums.length <= 10^4', 'intervals[i].length == 2'). Edit it for
rules types can't express (sorted arrays, a unique answer). It is run with a seed, so any
counterexample can be reproduced.
"""
import re

from . import judge

MAX_LEN = 8
VALUE_SPAN = 20


def _number(text):
    text = text.replace(" ", "").replace("−", "-")
    m = re.fullmatch(r"(-?)(\d+)(?:\^(\d+))?([+-]\d+)?", text)
    if not m:
        return None
    sign, base, exp, shift = m.groups()
    value = int(base) ** int(exp) if exp else int(base)
    value = -value if sign else value
    return value + int(shift) if shift else value


def parse_bounds(constraint_lines):
    """Map names to (lo, hi): 'lo <= a, b <= hi', 'lo <= a <= b <= hi' and 'x == N' lines."""
    bounds = {}
    for line in constraint_lines:
        line = line.replace("≤", "<=").replace("&lt;", "<")
        eq = re.match(r"\s*(.+?)\s*==\s*([-\d^ +]+)\s*$", line)
        if eq and _number(eq.group(2)) is not None:
            n = _number(eq.group(2))
            bounds[eq.group(1).strip()] = (n, n)
            continue
        parts = re.split(r"\s*<=?\s*", line.strip())
        if len(parts) < 3:
            continue
        lo, hi = _number(parts[0]), _number(parts[-1])
        if lo is None or hi is None:
            continue
        for chunk in parts[1:-1]:
            for name in re.split(r"\s*,\s*", chunk):
                bounds[name.strip()] = (lo, hi)
    return bounds


def _clip(lo, hi, span):
    """A small window inside [lo, hi], near 0 when allowed."""
    if hi - lo <= span:
        return lo, hi
    start = min(max(lo, -span // 2), hi - span)
    return start, start + span


def _small(lo, hi):
    lo = max(0, lo)
    return lo, max(lo, min(hi, MAX_LEN))


def _expr(typ, path, bounds, depth=0):
    """Python source that builds one random value of LeetCode type `typ`."""
    t = typ.strip().lower()
    if t in ("listnode", "treenode"):
        val = bounds.get("Node.val", (-VALUE_SPAN, VALUE_SPAN))
        lo, hi = _small(*bounds.get("The number of nodes in the list", bounds.get(
            "The number of nodes in the tree", (0, MAX_LEN))))
        lo_v, hi_v = _clip(*val, VALUE_SPAN)
        return f"{'tree' if t == 'treenode' else 'array'}(lambda: rng.randint({lo_v}, {hi_v}), {lo}, {hi})"
    if t.endswith("[]") or t.startswith("list<"):
        inner = t[:-2] if t.endswith("[]") else t[5:-1]
        lo, hi = _small(*bounds.get(f"{path}.length", (1, MAX_LEN)))
        return f"array(lambda: {_expr(inner, path + '[i]' if depth == 0 else path + '[j]', bounds, depth + 1)}, {lo}, {hi})"
    if t in ("integer", "long"):
        lo, hi = _clip(*bounds.get(path, _element(bounds, path)), VALUE_SPAN)
        return f"rng.randint({lo}, {hi})"
    if t == "double":
        return f"round(rng.uniform({-VALUE_SPAN}, {VALUE_SPAN}), 2)"
    if t == "boolean":
        return "rng.random() < 0.5"
    if t == "character":
        return "rng.choice(LETTERS)"
    if t == "string":
        lo, hi = _small(*bounds.get(f"{path}.length", (1, MAX_LEN)))
        return f"word({lo}, {hi})"
    raise ValueError(f"can't generate values of type '{typ}'")


def _element(bounds, path):
    """Bounds for an element like nums[i] or intervals[i][j], falling back to a small default."""
    root = path.split("[", 1)[0]
    for key, value in bounds.items():
        if key.startswith(root + "[") and ".length" not in key:
            return value
    return (-VALUE_SPAN, VALUE_SPAN)


GEN_HEADER = '''"""Random test generator for stress testing (python gen.py SEED).

Prints one JSON value per parameter, one per line. Pre-filled from the problem's types and
constraints; edit it for rules they can't express (sort an array, guarantee one answer).
"""
import json
import random
import sys

rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else None)
LETTERS = "abc"


def array(make, lo, hi):
    return [make() for _ in range(rng.randint(lo, hi))]


def word(lo, hi):
    return "".join(rng.choice(LETTERS) for _ in range(rng.randint(lo, hi)))


def tree(make, lo, hi):
    """Level-order list with some nulls, LeetCode style."""
    values = array(make, lo, hi)
    return [v if k == 0 or rng.random() > 0.2 else None for k, v in enumerate(values)]

'''


def generator_source(meta, constraint_lines, letters=None):
    bounds = parse_bounds(constraint_lines)
    header = GEN_HEADER.replace('LETTERS = "abc"', f"LETTERS = {letters or 'abc'!r}")
    lines = [header]
    for p in meta["params"]:
        lines.append(f"{p['name']} = {_expr(p['type'], p['name'], bounds)}")
    lines.append("")
    for p in meta["params"]:
        lines.append(f"print(json.dumps({p['name']}, separators=(',', ':')))")
    return "\n".join(lines) + "\n"


def stress(solution_cmd, brute_cmd, gen_cmd, rounds=200, first_seed=1,
           time_limit_s=2.0, memory_mb=256, any_order=False):
    """Returns {'rounds_run', 'mismatch': {...} | None, 'error': str | None}."""
    for k in range(rounds):
        seed = first_seed + k
        gen = judge.run_once(gen_cmd + [str(seed)], "", 10, 512)
        if gen["status"] != judge.Verdict.AC:
            return {"rounds_run": k, "mismatch": None, "error": f"gen.py failed (seed {seed}): {gen['stderr'][-800:]}"}
        stdin_text = gen["stdout"]
        lines = stdin_text.strip("\n").split("\n")
        brute = judge.run_once(brute_cmd, stdin_text, time_limit_s * 5, memory_mb)
        if brute["status"] != judge.Verdict.AC:
            return {"rounds_run": k + 1, "mismatch": None,
                    "error": f"Brute force failed ({brute['status']}) on seed {seed}: {brute['stderr'][-800:]}",
                    "input": lines}
        sol = judge.run_once(solution_cmd, stdin_text, time_limit_s, memory_mb)
        expected = brute["stdout"].strip()
        if sol["status"] != judge.Verdict.AC or not judge.outputs_match(expected, sol["stdout"], any_order):
            return {"rounds_run": k + 1, "error": None, "mismatch": {
                "seed": seed, "input": lines, "expected": expected,
                "got": sol["stdout"].strip()[:5000],
                "status": judge.Verdict.WA if sol["status"] == judge.Verdict.AC else sol["status"],
                "stderr": sol["stderr"][-2000:]}}
    return {"rounds_run": rounds, "mismatch": None, "error": None}
