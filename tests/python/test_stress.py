import json

import pytest

from cph import leetcode, stress, templates

from conftest import PY_SOLUTIONS, fill_py, meta, question, write


@pytest.mark.parametrize("line, expected", [
    ("2 <= nums.length <= 10^4", {"nums.length": (2, 10000)}),
    ("-2^31 <= nums[i] <= 2^31 - 1", {"nums[i]": (-2**31, 2**31 - 1)}),
    ("-10^6 <= nums1[i], nums2[i] <= 10^6", {"nums1[i]": (-10**6, 10**6), "nums2[i]": (-10**6, 10**6)}),
    ("0 <= starti <= endi <= 10^4", {"starti": (0, 10**4), "endi": (0, 10**4)}),
    ("intervals[i].length == 2", {"intervals[i].length": (2, 2)}),
    ("s consists of parentheses only", {}),
])
def test_parse_bounds(line, expected):
    assert stress.parse_bounds([line]) == expected


@pytest.mark.parametrize("slug", ["two-sum", "merge-intervals", "valid-parentheses", "reverse-linked-list",
                                  "maximum-depth-of-binary-tree", "group-anagrams"])
def test_generated_gen_py_prints_valid_input(slug, tmp_path, py):
    import subprocess
    q, m = question(slug), meta(slug)
    gen = write(tmp_path, "gen.py", stress.generator_source(m, leetcode.constraints(q["content"]),
                                                           leetcode.alphabet(q["content"])))
    for seed in range(20):
        out = subprocess.run([py, gen, str(seed)], capture_output=True, text=True, check=True).stdout
        values = [json.loads(line) for line in out.strip().split("\n")]
        assert len(values) == len(m["params"])
    again = subprocess.run([py, gen, "5"], capture_output=True, text=True).stdout
    assert again == subprocess.run([py, gen, "5"], capture_output=True, text=True).stdout  # reproducible


def test_merge_intervals_generates_pairs(tmp_path, py):
    import subprocess
    q, m = question("merge-intervals"), meta("merge-intervals")
    gen = write(tmp_path, "gen.py", stress.generator_source(m, leetcode.constraints(q["content"])))
    intervals = json.loads(subprocess.run([py, gen, "3"], capture_output=True, text=True).stdout)
    assert intervals and all(len(iv) == 2 for iv in intervals)


def _setup_two_sum(tmp_path, solution_body):
    q, m = question("two-sum"), meta("two-sum")
    template = templates.python_template(m, leetcode.snippet(q, "python3"))
    brute_body = """for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []"""
    sol = write(tmp_path, "solution.py", fill_py(template, solution_body))
    brute = write(tmp_path, "brute.py", fill_py(template, brute_body))
    gen = write(tmp_path, "gen.py", stress.generator_source(m, leetcode.constraints(q["content"])))
    return sol, brute, gen


def test_stress_finds_a_planted_bug(tmp_path, py):
    buggy = """for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target and nums[i] >= 0:   # bug: skips negatives
                    return [i, j]
        return []"""
    sol, brute, gen = _setup_two_sum(tmp_path, buggy)
    result = stress.stress([py, sol], [py, brute], [py, gen], rounds=300)
    m = result["mismatch"]
    assert m is not None and m["status"] == "WA"
    assert any(int(x) < 0 for x in json.loads(m["input"][0]))  # the counterexample involves a negative
    assert "seed" in m


def test_stress_passes_a_correct_solution(tmp_path, py):
    sol, brute, gen = _setup_two_sum(tmp_path, """for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []""")
    result = stress.stress([py, sol], [py, brute], [py, gen], rounds=50)
    assert result == {"rounds_run": 50, "mismatch": None, "error": None}
