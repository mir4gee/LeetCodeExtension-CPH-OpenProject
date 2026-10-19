# Changelog

## 1.0.0 (Oct 2026)

- Write only the `Solution` method: generated C++/Python harness for LeetCode's types, including `ListNode` and `TreeNode`.
- Judge with AC/WA/TLE/MLE/RE/OLE/CE verdicts, CPU time and memory; process-group kill and `setrlimit` limits.
- Stress testing against a brute force with a generated, editable `gen.py`.
- Problems live in `leetcode/<slug>/` in your workspace; re-fetching never overwrites your files.
- No shell commands, escaped webview content with a CSP, no hard-coded paths.

## 0.0.1 (Jan 2025)

- Prototype: fetch examples, compile with g++, compare trimmed output.
