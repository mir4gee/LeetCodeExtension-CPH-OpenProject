# CPH for LeetCode

A VS Code extension for practising LeetCode offline-style: fetch a problem, write only the `Solution` method exactly as on LeetCode, and judge it locally like an online judge. When the examples pass, stress test against a brute force to find the input that breaks you.

## What it does

- **Fetch** any public problem by slug or URL (`two-sum` or `https://leetcode.com/problems/two-sum/`) through LeetCode's GraphQL API. It creates `leetcode/<slug>/` in your workspace with:

  | File | What it is |
  | --- | --- |
  | `solution.cpp`, `solution.py` | LeetCode's starter code plus a generated harness: it reads one JSON value per parameter from stdin, calls your method, and prints the result. You never write I/O. |
  | `tests.json` | The problem's examples. Add your own; re-fetching never overwrites your files. |
  | `brute.cpp`, `brute.py` | A second copy of the template for a slow, obviously-correct solution. |
  | `gen.py` | A random test generator pre-filled from the parameter types and constraints. Edit it for rules types can't express (sorted input, a unique answer). |

- **Judge** (`Ctrl+Alt+B`) with real verdicts per test: **AC, WA, TLE, MLE, RE, OLE** or **CE**, with CPU time and peak memory.
  - Each run gets its own process group, so a timeout kills everything the program forked.
  - CPU and address-space limits are set with `setrlimit` in the child; TLE also has a wall-clock kill.
  - Output is capped. Comparison parses JSON, allows a 1e-5 float tolerance, and can ignore list order.
- **Stress test** your solution against `brute.*` on hundreds of random inputs from `gen.py`. It stops at the first difference and shows a small counterexample, its seed, and a button to save it as a test.
- **Types supported by the harness:** integers, doubles, booleans, strings, characters, arrays and nested lists of these, `ListNode` and `TreeNode` (LeetCode's level-order format), and in-place `void` methods. Class-design problems (like LRU Cache) get the starter code and their examples, without the generated harness or stress testing.

## Requirements

- VS Code 1.96+
- Python 3.9+ (standard library only)
- `g++` with C++17 for C++ solutions
- Time and memory limits are enforced on Linux and macOS. On Windows, tests run without them.

## Use

1. Open a folder in VS Code.
2. Run **LeetCode: Open problem** from the Command Palette and enter a slug or URL.
3. Write your method in `solution.cpp` (or `solution.py`) above the generated harness line.
4. Press **Run tests** in the panel, or `Ctrl+Alt+B` in the editor.
5. For stress testing: write a brute force in `brute.cpp`, check `gen.py`, then press **Stress test**.

Settings (`cphLeetcode.*`): `pythonPath`, `cppCompiler`, `timeLimitMs` (default 2000), `memoryLimitMb` (default 256), `stressRounds` (default 200).

## How it works

```
VS Code extension (TypeScript)                Python package `cph` (python/cph)
  commands + webview panel  ── execFile ──>   python -m cph fetch|run|stress   (one JSON line out)
  (argument array, no shell)                    leetcode.py   GraphQL fetch, examples, constraints
                                                templates.py  C++/Python harness generation
                                                judge.py      compile, sandboxed runs, verdicts, comparison
                                                stress.py     gen.py generation, solution vs brute loop
```

The panel renders everything from LeetCode or your program as text (never HTML) under a strict Content-Security-Policy.

## Development

```bash
npm install
npm run compile
python3 -m pytest -q     # judge, templates, stress, CLI: 66 tests, offline (saved LeetCode fixtures)
npm test                 # runs the extension inside VS Code; fetches two-sum from LeetCode
```

Press `F5` to open an Extension Development Host.

## History

Started at Tinkering Lab, IIT Roorkee (Dec 2024 – Jan 2025) as a prototype that scraped examples, compiled with `g++` and compared trimmed output. Rebuilt in Oct 2026: the generated harness, sandboxed judging with verdicts and limits, stress testing, and safe process handling.
