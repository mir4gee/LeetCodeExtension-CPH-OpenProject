"""Compile and run a solution against test cases, like an online judge.

Each run gets its own process group, a CPU-time and address-space limit (POSIX), a wall-clock
timeout that kills the whole group, and an output cap. Resource usage comes from wait4().
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time

OUTPUT_CAP = 16 * 1024 * 1024
COMPILE_TIMEOUT = 60
POSIX = os.name == "posix"
if POSIX:
    import resource


class Verdict:
    AC, WA, TLE, MLE, RE, CE, OLE = "AC", "WA", "TLE", "MLE", "RE", "CE", "OLE"


def compile_cpp(source, compiler="g++", out_dir=None):
    """Returns (path_to_binary, None) or (None, compiler_errors)."""
    out_dir = out_dir or tempfile.mkdtemp(prefix="cph-")
    binary = os.path.join(out_dir, "solution")
    cmd = [compiler, "-std=c++17", "-O2", "-o", binary, source]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=COMPILE_TIMEOUT)
    except FileNotFoundError:
        return None, f"Compiler '{compiler}' not found. Install g++ or set cphLeetcode.cppCompiler."
    except subprocess.TimeoutExpired:
        return None, f"Compilation took longer than {COMPILE_TIMEOUT}s."
    if proc.returncode != 0:
        return None, proc.stderr[-20000:]
    return binary, None


def command_for(lang, source, binary=None, python="python3"):
    return [binary] if lang == "cpp" else [python, source]


def _limits(time_limit_s, memory_mb):
    """Runs in the child between fork and exec."""
    cpu = max(1, int(time_limit_s + 1))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
    if memory_mb:
        mem = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _kill_group(pid):
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


_floor_kb = None


def memory_floor_kb():
    """Peak-RSS reading of a do-nothing process spawned the same way.

    Linux keeps ru_maxrss across exec, so a child forked from this (Python) process reports
    max(our size at fork time, its real peak). Readings at or below this floor mean "smaller
    than the floor", not a real number.
    """
    global _floor_kb
    if _floor_kb is None:
        _floor_kb = 0
        if POSIX and os.path.exists("/bin/true"):
            _floor_kb = run_once(["/bin/true"], "", 2, 0)["memory_kb"] or 0
    return _floor_kb


def run_once(cmd, stdin_text, time_limit_s=2.0, memory_mb=256):
    """Run one process. Returns dict(status, stdout, stderr, time_ms, memory_kb, exit, signal)."""
    kwargs = {}
    if POSIX:
        kwargs = {"start_new_session": True, "preexec_fn": lambda: _limits(time_limit_s, memory_mb)}
    start = time.monotonic()
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, **kwargs)
    except OSError as exc:
        return {"status": Verdict.RE, "stdout": "", "stderr": f"Couldn't start {cmd[0]}: {exc}",
                "time_ms": 0, "memory_kb": 0, "exit": None, "signal": None}

    out, err = bytearray(), bytearray()
    flags = {"timeout": False, "overflow": False}

    def pump(stream, buf, cap):
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            if len(buf) + len(chunk) > cap:
                buf += chunk[: cap - len(buf)]
                flags["overflow"] = True
                _kill_group(proc.pid) if POSIX else proc.kill()
                break
            buf += chunk

    def feed():
        try:
            proc.stdin.write(stdin_text.encode())
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass  # the program exited without reading all input

    def on_timeout():
        flags["timeout"] = True
        _kill_group(proc.pid) if POSIX else proc.kill()

    threads = [threading.Thread(target=feed, daemon=True),
               threading.Thread(target=pump, args=(proc.stdout, out, OUTPUT_CAP), daemon=True),
               threading.Thread(target=pump, args=(proc.stderr, err, 64 * 1024), daemon=True)]
    for t in threads:
        t.start()
    timer = threading.Timer(time_limit_s, on_timeout)
    timer.start()

    if POSIX:
        _, status, usage = os.wait4(proc.pid, 0)
        proc.returncode = os.waitstatus_to_exitcode(status)
        memory_kb = usage.ru_maxrss // (1024 if sys.platform == "darwin" else 1)  # macOS reports bytes
        cpu_s = usage.ru_utime + usage.ru_stime
    else:
        proc.wait()
        memory_kb, cpu_s = 0, None
    elapsed = time.monotonic() - start
    timer.cancel()
    _kill_group(proc.pid) if POSIX else None  # reap anything the solution forked
    for t in threads:
        t.join(timeout=1)

    code = proc.returncode
    sig = -code if code is not None and code < 0 else None
    stderr = err.decode(errors="replace")
    result = {"stdout": out.decode(errors="replace"), "stderr": stderr,
              "time_ms": round((cpu_s if cpu_s is not None else elapsed) * 1000),
              "memory_kb": memory_kb, "exit": code,
              "signal": signal.Signals(sig).name if sig else None}

    hit_memory = memory_mb and memory_kb >= memory_mb * 1024 * 0.95
    if flags["overflow"]:
        result["status"] = Verdict.OLE
    elif flags["timeout"] or sig == getattr(signal, "SIGXCPU", None):
        result["status"] = Verdict.TLE
        result["time_ms"] = max(result["time_ms"], round(time_limit_s * 1000))
    elif code != 0 and (hit_memory or "bad_alloc" in stderr or "MemoryError" in stderr):
        result["status"] = Verdict.MLE
    elif code != 0:
        result["status"] = Verdict.RE
    else:
        result["status"] = Verdict.AC  # provisional: the caller compares output
    return result


# --- Output comparison ---------------------------------------------------------------

def _parse(text):
    try:
        return json.loads(text)
    except ValueError:
        return text.split()


def _sort_deep(v):
    if isinstance(v, list):
        items = [_sort_deep(x) for x in v]
        return sorted(items, key=lambda x: json.dumps(x, sort_keys=True))
    return v


def _equal(a, b, tol):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol * max(1.0, abs(a), abs(b))
    if isinstance(a, str) and isinstance(b, str):
        try:
            return _equal(float(a), float(b), tol) if a != b else True
        except ValueError:
            return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_equal(x, y, tol) for x, y in zip(a, b))
    return a == b


def outputs_match(expected, got, any_order=False, tol=1e-5):
    """Compare as JSON values (float tolerance, optional order-insensitivity); else as tokens."""
    if expected is None:
        return True  # no expected output known: only checks that the program runs
    exp, act = _parse(expected.strip()), _parse(got.strip())
    if any_order:
        exp, act = _sort_deep(exp), _sort_deep(act)
    return _equal(exp, act, tol)


def judge(cmd, tests, time_limit_s=2.0, memory_mb=256, any_order=False):
    floor = memory_floor_kb()
    results = []
    for k, test in enumerate(tests, 1):
        stdin_text = "\n".join(test["input"]) + "\n"
        r = run_once(cmd, stdin_text, time_limit_s, memory_mb)
        got = r["stdout"].strip()
        if r["status"] == Verdict.AC and not outputs_match(test.get("output"), got, any_order):
            r["status"] = Verdict.WA
        measured = r["memory_kb"] > floor * 1.05
        results.append({"test": k, "status": r["status"], "time_ms": r["time_ms"],
                        "memory_kb": r["memory_kb"] if measured else None, "memory_floor_kb": floor,
                        "input": test["input"],
                        "expected": test.get("output"), "got": got[:5000],
                        "stderr": r["stderr"][-3000:], "signal": r["signal"]})
    return results


if __name__ == "__main__":
    print("Use: python -m cph run ...", file=sys.stderr)
    sys.exit(2)
