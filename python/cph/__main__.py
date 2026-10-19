"""CLI used by the VS Code extension. Every command prints exactly one JSON object on stdout.

  python -m cph fetch  <slug-or-url> <workspace_dir>
  python -m cph run    <problem_dir> cpp|python [--file solution|brute]
  python -m cph stress <problem_dir> cpp|python [--rounds N]
"""
import argparse
import json
import os
import sys
import tempfile

from . import judge, leetcode, stress, templates


def _write_new(path, text):
    """Never overwrite: the user's code and custom tests live in these files."""
    if os.path.exists(path):
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return True


def fetch(args):
    slug = leetcode.slug_from(args.slug)
    question = leetcode.fetch(slug)
    meta = json.loads(question.get("metaData") or "{}")
    supported = templates.supported(meta)
    tests = leetcode.tests_from(question, meta) if supported else [
        {"input": block.split("\n"), "output": out} for block, out in
        zip(question.get("exampleTestcaseList") or [], leetcode.example_outputs(question.get("content")))]
    constraint_lines = leetcode.constraints(question.get("content"))

    folder = os.path.join(args.workspace, "leetcode", slug)
    os.makedirs(folder, exist_ok=True)
    problem = {
        "slug": slug, "id": question["questionId"], "title": question["title"],
        "difficulty": question["difficulty"], "url": f"https://leetcode.com/problems/{slug}/",
        "supported": supported, "meta": meta, "constraints": constraint_lines, "anyOrder": False,
        "statement": leetcode.statement_text(question.get("content")),
    }
    with open(os.path.join(folder, "problem.json"), "w", encoding="utf-8") as f:
        json.dump(problem, f, indent=2)

    cpp, py = leetcode.snippet(question, "cpp"), leetcode.snippet(question, "python3")
    if supported:
        cpp_src, py_src = templates.cpp_template(meta, cpp), templates.python_template(meta, py)
    else:
        cpp_src, py_src = templates.cpp_fallback(cpp), templates.python_fallback(py)
    created = [name for name, text in [
        ("tests.json", json.dumps(tests, indent=2)),
        ("solution.cpp", cpp_src), ("solution.py", py_src),
        ("brute.cpp", cpp_src), ("brute.py", py_src),
    ] if _write_new(os.path.join(folder, name), text)]
    if supported and _write_new(os.path.join(folder, "gen.py"), stress.generator_source(
            meta, constraint_lines, leetcode.alphabet(question.get("content")))):
        created.append("gen.py")
    with open(os.path.join(folder, "tests.json"), encoding="utf-8") as f:
        tests = json.load(f)
    return {"folder": folder, "problem": problem, "tests": tests, "created": created}


def _load(problem_dir):
    with open(os.path.join(problem_dir, "problem.json"), encoding="utf-8") as f:
        problem = json.load(f)
    with open(os.path.join(problem_dir, "tests.json"), encoding="utf-8") as f:
        tests = json.load(f)
    return problem, tests


def _command(args, problem_dir, name, build_dir):
    """Returns (cmd, None) or (None, compile_errors) for solution/brute in the chosen language."""
    if args.lang == "cpp":
        binary, errors = judge.compile_cpp(os.path.join(problem_dir, f"{name}.cpp"), args.compiler,
                                           os.path.join(build_dir, name))
        return ([binary], None) if binary else (None, errors)
    return [args.python, os.path.join(problem_dir, f"{name}.py")], None


def run(args):
    problem, tests = _load(args.problem_dir)
    with tempfile.TemporaryDirectory(prefix="cph-build-") as build:
        os.makedirs(os.path.join(build, args.file))
        cmd, errors = _command(args, args.problem_dir, args.file, build)
        if errors:
            return {"compile_error": errors, "results": []}
        results = judge.judge(cmd, tests, args.time_limit / 1000, args.memory_limit,
                              problem.get("anyOrder", False))
    return {"compile_error": None, "results": results}


def stress_cmd(args):
    problem, _ = _load(args.problem_dir)
    gen = os.path.join(args.problem_dir, "gen.py")
    if not os.path.exists(gen):
        return {"error": "This problem has no gen.py (its input format isn't supported for stress tests)."}
    with tempfile.TemporaryDirectory(prefix="cph-build-") as build:
        cmds = {}
        for name in ("solution", "brute"):
            os.makedirs(os.path.join(build, name))
            cmd, errors = _command(args, args.problem_dir, name, build)
            if errors:
                return {"error": f"{name}.{'cpp' if args.lang == 'cpp' else 'py'} doesn't compile:\n{errors}"}
            cmds[name] = cmd
        return stress.stress(cmds["solution"], cmds["brute"], [args.python, gen], args.rounds,
                             time_limit_s=args.time_limit / 1000, memory_mb=args.memory_limit,
                             any_order=problem.get("anyOrder", False))


def main(argv=None):
    p = argparse.ArgumentParser(prog="cph")
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch")
    f.add_argument("slug")
    f.add_argument("workspace")
    f.set_defaults(handler=fetch)

    for name, handler in (("run", run), ("stress", stress_cmd)):
        s = sub.add_parser(name)
        s.add_argument("problem_dir")
        s.add_argument("lang", choices=["cpp", "python"])
        s.add_argument("--time-limit", type=int, default=2000, help="milliseconds")
        s.add_argument("--memory-limit", type=int, default=256, help="megabytes")
        s.add_argument("--compiler", default="g++")
        s.add_argument("--python", default=sys.executable)
        s.set_defaults(handler=handler)
    sub.choices["run"].add_argument("--file", choices=["solution", "brute"], default="solution")
    sub.choices["stress"].add_argument("--rounds", type=int, default=200)

    args = p.parse_args(argv)
    try:
        result = args.handler(args)
    except leetcode.ProblemError as exc:
        result = {"error": str(exc)}
    except Exception as exc:  # report, don't crash the extension with a traceback on stdout
        print(f"cph: {type(exc).__name__}: {exc}", file=sys.stderr)
        result = {"error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result))
    return 1 if "error" in result and result["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
