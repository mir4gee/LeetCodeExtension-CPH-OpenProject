"""Judge verdicts against deliberately misbehaving programs."""
import os
import time

import pytest

from cph import judge

from conftest import write

TEST = [{"input": ["[1,2]"], "output": "3"}]


def run(tmp_path, py, code, tests=TEST, **kw):
    return judge.judge([py, write(tmp_path, "p.py", code)], tests, **kw)[0]


def test_accepted_and_wrong_answer(tmp_path, py):
    assert run(tmp_path, py, "import json; print(sum(json.loads(input())))")["status"] == "AC"
    r = run(tmp_path, py, "print(4)")
    assert r["status"] == "WA" and r["expected"] == "3" and r["got"] == "4"


def test_infinite_loop_is_killed_as_tle(tmp_path, py):
    start = time.monotonic()
    r = run(tmp_path, py, "while True: pass", time_limit_s=0.5)
    assert r["status"] == "TLE"
    assert time.monotonic() - start < 5


def test_tle_kills_forked_grandchildren(tmp_path, py):
    pid_file = tmp_path / "child.pid"
    code = f"""
import subprocess, sys, time
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
open({str(pid_file)!r}, "w").write(str(child.pid))
time.sleep(60)
"""
    r = run(tmp_path, py, code, time_limit_s=1)
    assert r["status"] == "TLE"
    child = int(pid_file.read_text())
    time.sleep(0.2)
    with pytest.raises(ProcessLookupError):
        os.kill(child, 0)  # the whole process group was killed, not just the direct child


def test_memory_limit(tmp_path, py):
    r = run(tmp_path, py, "x = bytearray(1024 * 1024 * 1024)\nprint(3)", memory_mb=128)
    assert r["status"] == "MLE"


def test_runtime_error_and_signal(tmp_path, py):
    assert run(tmp_path, py, "raise SystemExit(3)")["status"] == "RE"
    r = run(tmp_path, py, "import os, signal; os.kill(os.getpid(), signal.SIGSEGV)")
    assert r["status"] == "RE" and r["signal"] == "SIGSEGV"


def test_output_limit(tmp_path, py):
    r = run(tmp_path, py, "import sys\nwhile True: sys.stdout.write('x' * 65536)", time_limit_s=10)
    assert r["status"] == "OLE"


def test_program_that_ignores_stdin(tmp_path, py):
    big = [{"input": ["[" + ",".join(["1"] * 200000) + "]"], "output": "3"}]
    assert run(tmp_path, py, "print(3)", tests=big)["status"] == "AC"


def test_compile_error(tmp_path):
    binary, errors = judge.compile_cpp(write(tmp_path, "bad.cpp", "int main() { return x; }"), out_dir=str(tmp_path))
    assert binary is None and "x" in errors


def test_missing_compiler(tmp_path):
    binary, errors = judge.compile_cpp(write(tmp_path, "a.cpp", "int main(){}"), "no-such-g++", str(tmp_path))
    assert binary is None and "not found" in errors


def test_cpp_segfault_is_runtime_error(tmp_path):
    binary, _ = judge.compile_cpp(write(tmp_path, "s.cpp", "int main(){ volatile int* p = nullptr; return *p; }"),
                                  out_dir=str(tmp_path))
    r = judge.judge([binary], TEST)[0]
    assert r["status"] == "RE" and r["signal"] == "SIGSEGV"


@pytest.mark.parametrize("expected, got, any_order, ok", [
    ("3", "3", False, True),
    ("2.00000", "2.0", False, True),          # float tolerance
    ("2.50000", "2.49", False, False),
    ("[0,1]", "[0, 1]", False, True),         # whitespace inside JSON
    ('[["bat"],["nat","tan"]]', '[["tan","nat"],["bat"]]', True, True),   # any order, nested
    ('[["bat"],["nat","tan"]]', '[["tan","nat"],["bat"]]', False, False),
    ("true", "True", False, False),
    ("abc def", "abc  def\n", False, True),   # non-JSON falls back to tokens
    (None, "anything", False, True),          # no expected output: only checks it runs
])
def test_outputs_match(expected, got, any_order, ok):
    assert judge.outputs_match(expected, got, any_order) is ok


def test_memory_reading_below_floor_is_reported_as_none(tmp_path, py):
    r = run(tmp_path, py, "print(3)")
    assert r["memory_floor_kb"] > 0
    assert r["memory_kb"] is None or r["memory_kb"] > r["memory_floor_kb"]


def test_large_allocation_is_measured(tmp_path, py):
    r = run(tmp_path, py, "x = bytearray(300 * 1024 * 1024)\nfor i in range(0, len(x), 4096): x[i] = 1\nprint(3)",
            memory_mb=1024)
    assert r["status"] == "AC" and r["memory_kb"] > 300 * 1024
