import json

import pytest

from cph import __main__ as cli
from cph import leetcode

from conftest import CPP_SOLUTIONS, fill_cpp, question


def call(capsys, *argv):
    code = cli.main(list(argv))
    return code, json.loads(capsys.readouterr().out)


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(leetcode, "fetch", lambda slug: question(slug))


@pytest.mark.parametrize("text, slug", [
    ("two-sum", "two-sum"),
    ("https://leetcode.com/problems/two-sum/description/", "two-sum"),
    ("  Merge-Intervals ", "merge-intervals"),
])
def test_slug_from(text, slug):
    assert leetcode.slug_from(text) == slug


@pytest.mark.parametrize("bad", ['two-sum"; rm -rf ~', "../etc", "", "a b"])
def test_rejects_unsafe_slugs(bad):
    with pytest.raises(leetcode.ProblemError):
        leetcode.slug_from(bad)


def test_fetch_creates_files_and_never_overwrites(tmp_path, capsys, offline):
    code, out = call(capsys, "fetch", "two-sum", str(tmp_path))
    assert code == 0 and out["problem"]["supported"]
    assert sorted(out["created"]) == ["brute.cpp", "brute.py", "gen.py", "solution.cpp", "solution.py", "tests.json"]
    folder = tmp_path / "leetcode" / "two-sum"
    (folder / "solution.cpp").write_text("// my work")
    tests = json.loads((folder / "tests.json").read_text())
    tests.append({"input": ["[1,1]", "2"], "output": "[0,1]"})
    (folder / "tests.json").write_text(json.dumps(tests))

    code, out = call(capsys, "fetch", "two-sum", str(tmp_path))
    assert out["created"] == []
    assert (folder / "solution.cpp").read_text() == "// my work"
    assert len(out["tests"]) == 4  # the custom test survives a re-fetch


def test_run_reports_results_and_compile_errors(tmp_path, capsys, offline):
    call(capsys, "fetch", "two-sum", str(tmp_path))
    folder = tmp_path / "leetcode" / "two-sum"
    _, out = call(capsys, "run", str(folder), "cpp")
    # The unfilled method falls off the end of a non-void function: UB, which -O2 turns into a trap.
    assert out["compile_error"] is None and {r["status"] for r in out["results"]} == {"RE"}

    source = (folder / "solution.cpp").read_text()
    (folder / "solution.cpp").write_text(fill_cpp(source, CPP_SOLUTIONS["two-sum"]))
    _, out = call(capsys, "run", str(folder), "cpp")
    assert [r["status"] for r in out["results"]] == ["AC", "AC", "AC"]

    (folder / "solution.cpp").write_text("int main() { syntax error }")
    _, out = call(capsys, "run", str(folder), "cpp")
    assert out["compile_error"] and out["results"] == []


def test_unsupported_problem_gets_fallback_and_no_gen(tmp_path, capsys, offline):
    _, out = call(capsys, "fetch", "lru-cache", str(tmp_path))
    assert out["problem"]["supported"] is False and "gen.py" not in out["created"]
    _, out = call(capsys, "stress", str(tmp_path / "leetcode" / "lru-cache"), "python")
    assert "no gen.py" in out["error"]


def test_errors_are_json(tmp_path, capsys, monkeypatch):
    def boom(slug):
        raise leetcode.ProblemError("No LeetCode problem called 'nope'.")
    monkeypatch.setattr(leetcode, "fetch", boom)
    code, out = call(capsys, "fetch", "nope", str(tmp_path))
    assert code == 1 and out == {"error": "No LeetCode problem called 'nope'."}
