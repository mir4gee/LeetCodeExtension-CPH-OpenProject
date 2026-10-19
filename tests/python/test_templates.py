"""Generated templates + real solutions must pass LeetCode's own examples, in both languages."""
import pytest

from cph import judge, leetcode, templates

from conftest import CPP_SOLUTIONS, PY_SOLUTIONS, fill_cpp, fill_py, meta, question, write

SUPPORTED = sorted(CPP_SOLUTIONS)
ANY_ORDER = {"group-anagrams"}


@pytest.mark.parametrize("slug", SUPPORTED)
def test_cpp_template_passes_examples(slug, tmp_path):
    q, m = question(slug), meta(slug)
    source = fill_cpp(templates.cpp_template(m, leetcode.snippet(q, "cpp")), CPP_SOLUTIONS[slug])
    binary, errors = judge.compile_cpp(write(tmp_path, "solution.cpp", source), out_dir=str(tmp_path))
    assert errors is None, errors
    results = judge.judge([binary], leetcode.tests_from(q, m), any_order=slug in ANY_ORDER)
    assert results and [r["status"] for r in results] == ["AC"] * len(results), results


@pytest.mark.parametrize("slug", SUPPORTED)
def test_python_template_passes_examples(slug, tmp_path, py):
    q, m = question(slug), meta(slug)
    source = fill_py(templates.python_template(m, leetcode.snippet(q, "python3")), PY_SOLUTIONS[slug])
    path = write(tmp_path, "solution.py", source)
    results = judge.judge([py, path], leetcode.tests_from(q, m), any_order=slug in ANY_ORDER)
    assert results and [r["status"] for r in results] == ["AC"] * len(results), results


def test_unfilled_python_template_runs_and_fails_cleanly(tmp_path, py):
    q, m = question("two-sum"), meta("two-sum")
    path = write(tmp_path, "s.py", templates.python_template(m, leetcode.snippet(q, "python3")))
    results = judge.judge([py, path], leetcode.tests_from(q, m))
    assert {r["status"] for r in results} == {"WA"}  # returns None -> 'null', not a crash


def test_class_design_problem_is_not_supported():
    assert not templates.supported(meta("lru-cache"))
    assert "isn't supported" in templates.cpp_fallback(leetcode.snippet(question("lru-cache"), "cpp"))


def test_types_map_to_cpp():
    assert templates.cpp_type("integer[][]") == "vector<vector<int>>"
    assert templates.cpp_type("list<list<String>>") == "vector<vector<string>>"
    assert templates.cpp_type("ListNode") == "ListNode*"
    with pytest.raises(templates.Unsupported):
        templates.cpp_type("NestedInteger")
