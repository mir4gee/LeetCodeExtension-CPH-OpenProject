import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
FIXTURES = ROOT / "tests" / "fixtures"


def question(slug):
    return json.loads((FIXTURES / f"{slug}.json").read_text())["data"]["question"]


def meta(slug):
    return json.loads(question(slug)["metaData"])


# Correct solutions, written the way a user would fill in LeetCode's method body.
CPP_SOLUTIONS = {
    "two-sum": """unordered_map<int, int> seen;
        for (int i = 0; i < (int)nums.size(); ++i) {
            auto it = seen.find(target - nums[i]);
            if (it != seen.end()) return {it->second, i};
            seen[nums[i]] = i;
        }
        return {};""",
    "merge-intervals": """sort(intervals.begin(), intervals.end());
        vector<vector<int>> out;
        for (auto& iv : intervals) {
            if (!out.empty() && iv[0] <= out.back()[1]) out.back()[1] = max(out.back()[1], iv[1]);
            else out.push_back(iv);
        }
        return out;""",
    "valid-parentheses": """string st;
        for (char c : s) {
            if (c == '(' || c == '[' || c == '{') st += c;
            else {
                if (st.empty()) return false;
                char o = st.back(); st.pop_back();
                if ((c == ')' && o != '(') || (c == ']' && o != '[') || (c == '}' && o != '{')) return false;
            }
        }
        return st.empty();""",
    "reverse-linked-list": """ListNode* prev = nullptr;
        while (head) { ListNode* next = head->next; head->next = prev; prev = head; head = next; }
        return prev;""",
    "maximum-depth-of-binary-tree": """return root ? 1 + max(maxDepth(root->left), maxDepth(root->right)) : 0;""",
    "rotate-array": """int n = nums.size(); k %= n;
        reverse(nums.begin(), nums.end());
        reverse(nums.begin(), nums.begin() + k);
        reverse(nums.begin() + k, nums.end());""",
    "median-of-two-sorted-arrays": """vector<int> all(nums1);
        all.insert(all.end(), nums2.begin(), nums2.end());
        sort(all.begin(), all.end());
        int n = all.size();
        return n % 2 ? all[n / 2] : (all[n / 2 - 1] + all[n / 2]) / 2.0;""",
    "group-anagrams": """map<string, vector<string>> groups;
        for (auto& s : strs) { string k = s; sort(k.begin(), k.end()); groups[k].push_back(s); }
        vector<vector<string>> out;
        for (auto& [k, v] : groups) out.push_back(v);
        return out;""",
}

PY_SOLUTIONS = {
    "two-sum": """seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i""",
    "merge-intervals": """out = []
        for a, b in sorted(intervals):
            if out and a <= out[-1][1]:
                out[-1][1] = max(out[-1][1], b)
            else:
                out.append([a, b])
        return out""",
    "valid-parentheses": """pairs, st = {")": "(", "]": "[", "}": "{"}, []
        for c in s:
            if c in pairs:
                if not st or st.pop() != pairs[c]:
                    return False
            else:
                st.append(c)
        return not st""",
    "reverse-linked-list": """prev = None
        while head:
            head.next, prev, head = prev, head, head.next
        return prev""",
    "maximum-depth-of-binary-tree": """return 1 + max(self.maxDepth(root.left), self.maxDepth(root.right)) if root else 0""",
    "rotate-array": """k %= len(nums)
        nums[:] = nums[-k:] + nums[:-k] if k else nums""",
    "median-of-two-sorted-arrays": """a = sorted(nums1 + nums2)
        n = len(a)
        return a[n // 2] if n % 2 else (a[n // 2 - 1] + a[n // 2]) / 2""",
    "group-anagrams": """groups = {}
        for s in strs:
            groups.setdefault("".join(sorted(s)), []).append(s)
        return list(groups.values())""",
}


def fill_cpp(source, body):
    marker = "{\n        \n    }"
    assert marker in source, "LeetCode's empty C++ method body not found"
    return source.replace(marker, "{\n        " + body + "\n    }", 1)


def fill_py(source, body):
    assert "        pass\n" in source
    return source.replace("        pass\n", "        " + body + "\n", 1)


@pytest.fixture
def py():
    return sys.executable


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


__all__ = ["question", "meta", "CPP_SOLUTIONS", "PY_SOLUTIONS", "fill_cpp", "fill_py", "write", "os"]
