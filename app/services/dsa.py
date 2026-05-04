import ast
import json
import os
import random
import re
import textwrap
import uuid
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.services.llm_config import (
    gemini_configured,
    get_gemini_api_key,
    get_groq_api_key,
    get_groq_model,
    groq_configured,
)


def multi_language_starter(
    function_name: str,
    python_body: str,
    java_signature: str,
    cpp_signature: str,
    csharp_signature: str,
) -> dict:
    return {
        "python": python_body,
        "java": java_signature,
        "cpp": cpp_signature,
        "csharp": csharp_signature,
    }


def multi_language_solution(
    python_code: str,
    java_code: str,
    cpp_code: str,
    csharp_code: str,
) -> dict:
    return {
        "python": python_code,
        "java": java_code,
        "cpp": cpp_code,
        "csharp": csharp_code,
    }


DSA_QUESTIONS = [
    {
        "id": "two-sum",
        "title": "Two Sum",
        "difficulty": "Easy",
        "topic": "Array, Hash Map",
        "prompt": "Return indices of two numbers whose sum equals the target.",
        "description": "Use a hash map to track values you have already seen so you can find the complement in O(1).",
        "function_name": "two_sum",
        "class_name": "Solution",
        "method_name": "twoSum",
        "starter_code": multi_language_starter(
            "two_sum",
            "def two_sum(nums, target):\n    # nums: list[int]\n    # target: int\n    # return list[int]\n    pass\n",
            "import java.util.*;\n\npublic class Solution {\n    public static int[] twoSum(int[] nums, int target) {\n        return new int[]{};\n    }\n}\n",
            "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<int> twoSum(vector<int> nums, int target) {\n    return {};\n}\n",
            "using System;\nusing System.Collections.Generic;\n\npublic class Solution {\n    public static int[] TwoSum(int[] nums, int target) {\n        return Array.Empty<int>();\n    }\n}\n",
        ),
        "solution": multi_language_solution(
            "def two_sum(nums, target):\n    seen = {}\n    for index, value in enumerate(nums):\n        need = target - value\n        if need in seen:\n            return [seen[need], index]\n        seen[value] = index\n    return []\n",
            "import java.util.*;\n\npublic class Solution {\n    public static int[] twoSum(int[] nums, int target) {\n        Map<Integer, Integer> seen = new HashMap<>();\n        for (int index = 0; index < nums.length; index++) {\n            int need = target - nums[index];\n            if (seen.containsKey(need)) {\n                return new int[]{seen.get(need), index};\n            }\n            seen.put(nums[index], index);\n        }\n        return new int[]{};\n    }\n}\n",
            "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<int> twoSum(vector<int> nums, int target) {\n    unordered_map<int, int> seen;\n    for (int index = 0; index < (int)nums.size(); index++) {\n        int need = target - nums[index];\n        if (seen.count(need)) {\n            return {seen[need], index};\n        }\n        seen[nums[index]] = index;\n    }\n    return {};\n}\n",
            "using System;\nusing System.Collections.Generic;\n\npublic class Solution {\n    public static int[] TwoSum(int[] nums, int target) {\n        var seen = new Dictionary<int, int>();\n        for (var index = 0; index < nums.Length; index++) {\n            var need = target - nums[index];\n            if (seen.ContainsKey(need)) {\n                return new[] { seen[need], index };\n            }\n            seen[nums[index]] = index;\n        }\n        return Array.Empty<int>();\n    }\n}\n",
        ),
        "tests": [
            {"input": [[2, 7, 11, 15], 9], "expected": [0, 1]},
            {"input": [[3, 2, 4], 6], "expected": [1, 2]},
        ],
    },
    {
        "id": "valid-parentheses",
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "topic": "Stack",
        "prompt": "Check whether brackets are correctly balanced.",
        "description": "Push opening brackets to a stack and validate the expected closing bracket order.",
        "function_name": "is_valid",
        "class_name": "Solution",
        "method_name": "isValid",
        "starter_code": multi_language_starter(
            "is_valid",
            "def is_valid(s):\n    # s: str\n    # return bool\n    pass\n",
            "import java.util.*;\n\npublic class Solution {\n    public static boolean isValid(String s) {\n        return false;\n    }\n}\n",
            "#include <bits/stdc++.h>\nusing namespace std;\n\nbool isValid(string s) {\n    return false;\n}\n",
            "using System;\nusing System.Collections.Generic;\n\npublic class Solution {\n    public static bool IsValid(string s) {\n        return false;\n    }\n}\n",
        ),
        "solution": multi_language_solution(
            "def is_valid(s):\n    pairs = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for ch in s:\n        if ch in pairs.values():\n            stack.append(ch)\n        elif ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n    return not stack\n",
            "import java.util.*;\n\npublic class Solution {\n    public static boolean isValid(String s) {\n        Map<Character, Character> pairs = Map.of(')', '(', ']', '[', '}', '{');\n        Deque<Character> stack = new ArrayDeque<>();\n        for (char ch : s.toCharArray()) {\n            if (pairs.containsValue(ch)) {\n                stack.push(ch);\n            } else if (pairs.containsKey(ch)) {\n                if (stack.isEmpty() || stack.pop() != pairs.get(ch)) {\n                    return false;\n                }\n            }\n        }\n        return stack.isEmpty();\n    }\n}\n",
            "#include <bits/stdc++.h>\nusing namespace std;\n\nbool isValid(string s) {\n    unordered_map<char, char> pairs = {{')', '('}, {']', '['}, {'}', '{'}};\n    vector<char> stack;\n    for (char ch : s) {\n        if (ch == '(' || ch == '[' || ch == '{') {\n            stack.push_back(ch);\n        } else if (pairs.count(ch)) {\n            if (stack.empty() || stack.back() != pairs[ch]) {\n                return false;\n            }\n            stack.pop_back();\n        }\n    }\n    return stack.empty();\n}\n",
            "using System;\nusing System.Collections.Generic;\n\npublic class Solution {\n    public static bool IsValid(string s) {\n        var pairs = new Dictionary<char, char> { [')'] = '(', [']'] = '[', ['}'] = '{' };\n        var stack = new Stack<char>();\n        foreach (var ch in s) {\n            if (ch == '(' || ch == '[' || ch == '{') {\n                stack.Push(ch);\n            } else if (pairs.ContainsKey(ch)) {\n                if (stack.Count == 0 || stack.Pop() != pairs[ch]) {\n                    return false;\n                }\n            }\n        }\n        return stack.Count == 0;\n    }\n}\n",
        ),
        "tests": [
            {"input": ["()[]{}"], "expected": True},
            {"input": ["(]"], "expected": False},
        ],
    },
    {
        "id": "merge-intervals",
        "title": "Merge Intervals",
        "difficulty": "Medium",
        "topic": "Array, Sorting",
        "prompt": "Merge all overlapping intervals and return the simplified list.",
        "description": "Sort by start time and merge into the latest interval when ranges overlap.",
        "function_name": "merge",
        "class_name": "Solution",
        "method_name": "merge",
        "starter_code": multi_language_starter(
            "merge",
            "def merge(intervals):\n    # intervals: list[list[int]]\n    # return list[list[int]]\n    pass\n",
            "import java.util.*;\n\npublic class Solution {\n    public static int[][] merge(int[][] intervals) {\n        return new int[][]{};\n    }\n}\n",
            "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<vector<int>> merge(vector<vector<int>> intervals) {\n    return {};\n}\n",
            "using System;\nusing System.Collections.Generic;\n\npublic class Solution {\n    public static int[][] Merge(int[][] intervals) {\n        return Array.Empty<int[]>();\n    }\n}\n",
        ),
        "solution": multi_language_solution(
            "def merge(intervals):\n    intervals.sort(key=lambda item: item[0])\n    merged = []\n    for start, end in intervals:\n        if not merged or start > merged[-1][1]:\n            merged.append([start, end])\n        else:\n            merged[-1][1] = max(merged[-1][1], end)\n    return merged\n",
            "import java.util.*;\n\npublic class Solution {\n    public static int[][] merge(int[][] intervals) {\n        Arrays.sort(intervals, Comparator.comparingInt(a -> a[0]));\n        List<int[]> merged = new ArrayList<>();\n        for (int[] interval : intervals) {\n            if (merged.isEmpty() || interval[0] > merged.get(merged.size() - 1)[1]) {\n                merged.add(new int[]{interval[0], interval[1]});\n            } else {\n                merged.get(merged.size() - 1)[1] = Math.max(merged.get(merged.size() - 1)[1], interval[1]);\n            }\n        }\n        return merged.toArray(new int[merged.size()][]);\n    }\n}\n",
            "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<vector<int>> merge(vector<vector<int>> intervals) {\n    sort(intervals.begin(), intervals.end());\n    vector<vector<int>> merged;\n    for (auto interval : intervals) {\n        if (merged.empty() || interval[0] > merged.back()[1]) {\n            merged.push_back(interval);\n        } else {\n            merged.back()[1] = max(merged.back()[1], interval[1]);\n        }\n    }\n    return merged;\n}\n",
            "using System;\nusing System.Collections.Generic;\nusing System.Linq;\n\npublic class Solution {\n    public static int[][] Merge(int[][] intervals) {\n        Array.Sort(intervals, (left, right) => left[0].CompareTo(right[0]));\n        var merged = new List<int[]>();\n        foreach (var interval in intervals) {\n            if (merged.Count == 0 || interval[0] > merged[^1][1]) {\n                merged.Add(new[] { interval[0], interval[1] });\n            } else {\n                merged[^1][1] = Math.Max(merged[^1][1], interval[1]);\n            }\n        }\n        return merged.ToArray();\n    }\n}\n",
        ),
        "tests": [
            {"input": [[[1, 3], [2, 6], [8, 10], [15, 18]]], "expected": [[1, 6], [8, 10], [15, 18]]},
            {"input": [[[1, 4], [4, 5]]], "expected": [[1, 5]]},
        ],
    },
    {
        "id": "longest-substring",
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "Medium",
        "topic": "Sliding Window",
        "prompt": "Find the maximum length substring with all unique characters.",
        "description": "Use a sliding window and store the last seen index for each character.",
        "function_name": "length_of_longest_substring",
        "class_name": "Solution",
        "method_name": "lengthOfLongestSubstring",
        "starter_code": multi_language_starter(
            "length_of_longest_substring",
            "def length_of_longest_substring(s):\n    # s: str\n    # return int\n    pass\n",
            "import java.util.*;\n\npublic class Solution {\n    public static int lengthOfLongestSubstring(String s) {\n        return 0;\n    }\n}\n",
            "#include <bits/stdc++.h>\nusing namespace std;\n\nint lengthOfLongestSubstring(string s) {\n    return 0;\n}\n",
            "using System;\nusing System.Collections.Generic;\n\npublic class Solution {\n    public static int LengthOfLongestSubstring(string s) {\n        return 0;\n    }\n}\n",
        ),
        "solution": multi_language_solution(
            "def length_of_longest_substring(s):\n    left = 0\n    best = 0\n    positions = {}\n    for right, ch in enumerate(s):\n        if ch in positions and positions[ch] >= left:\n            left = positions[ch] + 1\n        positions[ch] = right\n        best = max(best, right - left + 1)\n    return best\n",
            "import java.util.*;\n\npublic class Solution {\n    public static int lengthOfLongestSubstring(String s) {\n        Map<Character, Integer> positions = new HashMap<>();\n        int left = 0;\n        int best = 0;\n        for (int right = 0; right < s.length(); right++) {\n            char ch = s.charAt(right);\n            if (positions.containsKey(ch) && positions.get(ch) >= left) {\n                left = positions.get(ch) + 1;\n            }\n            positions.put(ch, right);\n            best = Math.max(best, right - left + 1);\n        }\n        return best;\n    }\n}\n",
            "#include <bits/stdc++.h>\nusing namespace std;\n\nint lengthOfLongestSubstring(string s) {\n    unordered_map<char, int> positions;\n    int left = 0;\n    int best = 0;\n    for (int right = 0; right < (int)s.size(); right++) {\n        char ch = s[right];\n        if (positions.count(ch) && positions[ch] >= left) {\n            left = positions[ch] + 1;\n        }\n        positions[ch] = right;\n        best = max(best, right - left + 1);\n    }\n    return best;\n}\n",
            "using System;\nusing System.Collections.Generic;\n\npublic class Solution {\n    public static int LengthOfLongestSubstring(string s) {\n        var positions = new Dictionary<char, int>();\n        var left = 0;\n        var best = 0;\n        for (var right = 0; right < s.Length; right++) {\n            var ch = s[right];\n            if (positions.ContainsKey(ch) && positions[ch] >= left) {\n                left = positions[ch] + 1;\n            }\n            positions[ch] = right;\n            best = Math.Max(best, right - left + 1);\n        }\n        return best;\n    }\n}\n",
        ),
        "tests": [
            {"input": ["abcabcbb"], "expected": 3},
            {"input": ["bbbbb"], "expected": 1},
        ],
    },
    {
        "id": "product-of-array-except-self",
        "title": "Product of Array Except Self",
        "difficulty": "Medium",
        "topic": "Array, Prefix Sum",
        "prompt": "Return an array where each position contains the product of every other element.",
        "description": "Build prefix and suffix products so each index can be computed without division.",
        "function_name": "product_except_self",
        "class_name": "Solution",
        "method_name": "productExceptSelf",
        "starter_code": multi_language_starter(
            "product_except_self",
            "def product_except_self(nums):\n    # nums: list[int]\n    # return list[int]\n    pass\n",
            "import java.util.*;\n\npublic class Solution {\n    public static int[] productExceptSelf(int[] nums) {\n        return new int[]{};\n    }\n}\n",
            "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<int> productExceptSelf(vector<int> nums) {\n    return {};\n}\n",
            "using System;\n\npublic class Solution {\n    public static int[] ProductExceptSelf(int[] nums) {\n        return Array.Empty<int>();\n    }\n}\n",
        ),
        "solution": multi_language_solution(
            "def product_except_self(nums):\n    result = [1] * len(nums)\n    prefix = 1\n    for index, value in enumerate(nums):\n        result[index] = prefix\n        prefix *= value\n    suffix = 1\n    for index in range(len(nums) - 1, -1, -1):\n        result[index] *= suffix\n        suffix *= nums[index]\n    return result\n",
            "import java.util.*;\n\npublic class Solution {\n    public static int[] productExceptSelf(int[] nums) {\n        int[] result = new int[nums.length];\n        int prefix = 1;\n        for (int index = 0; index < nums.length; index++) {\n            result[index] = prefix;\n            prefix *= nums[index];\n        }\n        int suffix = 1;\n        for (int index = nums.length - 1; index >= 0; index--) {\n            result[index] *= suffix;\n            suffix *= nums[index];\n        }\n        return result;\n    }\n}\n",
            "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<int> productExceptSelf(vector<int> nums) {\n    vector<int> result(nums.size(), 1);\n    int prefix = 1;\n    for (int index = 0; index < (int)nums.size(); index++) {\n        result[index] = prefix;\n        prefix *= nums[index];\n    }\n    int suffix = 1;\n    for (int index = (int)nums.size() - 1; index >= 0; index--) {\n        result[index] *= suffix;\n        suffix *= nums[index];\n    }\n    return result;\n}\n",
            "using System;\n\npublic class Solution {\n    public static int[] ProductExceptSelf(int[] nums) {\n        var result = new int[nums.Length];\n        var prefix = 1;\n        for (var index = 0; index < nums.Length; index++) {\n            result[index] = prefix;\n            prefix *= nums[index];\n        }\n        var suffix = 1;\n        for (var index = nums.Length - 1; index >= 0; index--) {\n            result[index] *= suffix;\n            suffix *= nums[index];\n        }\n        return result;\n    }\n}\n",
        ),
        "tests": [
            {"input": [[1, 2, 3, 4]], "expected": [24, 12, 8, 6]},
            {"input": [[-1, 1, 0, -3, 3]], "expected": [0, 0, 9, 0, 0]},
        ],
    },
]

# Cookie-backed sessions cannot safely hold full generated question payloads.
# Keep per-user generated questions server-side to avoid cookie size overflows.
_GENERATED_DSA_BY_USER: dict[int, list[dict]] = {}
_DSA_SUBMISSIONS_BY_USER: dict[int, list[dict]] = {}


def get_dsa_question(question_id: str, custom_questions: list[dict] | None = None) -> dict | None:
    for question in get_all_dsa_questions(custom_questions):
        if question["id"] == question_id:
            return question
    return None


def get_all_dsa_questions(custom_questions: list[dict] | None = None) -> list[dict]:
    return DSA_QUESTIONS + (custom_questions or [])


def get_generated_dsa_questions_for_user(user_id: int) -> list[dict]:
    return _GENERATED_DSA_BY_USER.get(user_id, [])


def save_generated_dsa_questions_for_user(user_id: int, questions: list[dict]) -> None:
    _GENERATED_DSA_BY_USER[user_id] = questions


def add_dsa_submission_for_user(user_id: int, submission: dict) -> None:
    items = _DSA_SUBMISSIONS_BY_USER.get(user_id, [])
    items.insert(0, submission)
    _DSA_SUBMISSIONS_BY_USER[user_id] = items[:80]


def get_dsa_submissions_for_user(user_id: int, question_id: str | None = None) -> list[dict]:
    items = _DSA_SUBMISSIONS_BY_USER.get(user_id, [])
    if not question_id:
        return items
    return [item for item in items if item.get("question_id") == question_id]


def build_submission_entry(question: dict, language: str, run_result: dict) -> dict:
    results = run_result.get("results", []) if isinstance(run_result, dict) else []
    passed_count = sum(1 for item in results if item.get("passed"))
    total_count = len(results)
    return {
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.get("id"),
        "question_title": question.get("title"),
        "language": language,
        "ok": bool(run_result.get("ok")),
        "passed_count": passed_count,
        "total_count": total_count,
        "error": str(run_result.get("error", "")).strip(),
    }


def gemini_dsa_configured() -> bool:
    return groq_configured() or gemini_configured()


def build_generated_dsa_question(topic: str = "Array", difficulty: str = "Medium", refresh_token: str = "") -> tuple[dict | None, str]:
    ai_question, ai_error = generate_ai_dsa_question(topic, difficulty, refresh_token=refresh_token)
    if ai_question:
        return ai_question, ""
    return None, ai_error or "Gemini could not generate a valid question for the selected topic. Please try again."


def _clean_generated_code(code: str) -> str:
    cleaned = str(code or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[\w#+-]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = textwrap.dedent(cleaned).strip("\n")
    if not cleaned:
        return ""
    return cleaned + "\n"


def _normalize_code_map(code_map: dict, required_languages: set[str]) -> dict:
    return {language: _clean_generated_code(code_map.get(language, "")) for language in required_languages}


def build_fallback_generated_dsa_question(topic: str, difficulty: str) -> dict:
    fallback_bank = [
        {
            "title": "Count Even Numbers",
            "prompt": "Count how many numbers in the array are even and return that count.",
            "description": "Iterate once through the array and track how many values are divisible by 2.",
            "function_name": "count_even_numbers",
            "method_name": "countEvenNumbers",
            "tests": [
                {"input": [[1, 2, 3, 4, 6]], "expected": 3},
                {"input": [[1, 3, 5]], "expected": 0},
            ],
            "starter_code": {
                "python": "def count_even_numbers(nums):\n    # nums: list[int]\n    # return int\n    pass\n",
                "java": "public class Solution {\n    public static int countEvenNumbers(int[] nums) {\n        return 0;\n    }\n}\n",
                "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nint countEvenNumbers(vector<int> nums) {\n    return 0;\n}\n",
                "csharp": "using System;\n\npublic class Solution {\n    public static int CountEvenNumbers(int[] nums) {\n        return 0;\n    }\n}\n",
            },
            "solution_code": {
                "python": "def count_even_numbers(nums):\n    return sum(1 for value in nums if value % 2 == 0)\n",
                "java": "public class Solution {\n    public static int countEvenNumbers(int[] nums) {\n        int count = 0;\n        for (int value : nums) {\n            if (value % 2 == 0) {\n                count++;\n            }\n        }\n        return count;\n    }\n}\n",
                "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nint countEvenNumbers(vector<int> nums) {\n    int count = 0;\n    for (int value : nums) {\n        if (value % 2 == 0) {\n            count++;\n        }\n    }\n    return count;\n}\n",
                "csharp": "using System;\n\npublic class Solution {\n    public static int CountEvenNumbers(int[] nums) {\n        var count = 0;\n        foreach (var value in nums) {\n            if (value % 2 == 0) {\n                count++;\n            }\n        }\n        return count;\n    }\n}\n",
            },
        },
        {
            "title": "Sum Of Positive Values",
            "prompt": "Return the sum of all positive numbers in the array.",
            "description": "Ignore zeros and negatives while aggregating only positive values.",
            "function_name": "sum_positive_values",
            "method_name": "sumPositiveValues",
            "tests": [
                {"input": [[-2, 4, 0, 3, -1]], "expected": 7},
                {"input": [[-5, -3]], "expected": 0},
            ],
            "starter_code": {
                "python": "def sum_positive_values(nums):\n    # nums: list[int]\n    # return int\n    pass\n",
                "java": "public class Solution {\n    public static int sumPositiveValues(int[] nums) {\n        return 0;\n    }\n}\n",
                "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nint sumPositiveValues(vector<int> nums) {\n    return 0;\n}\n",
                "csharp": "using System;\n\npublic class Solution {\n    public static int SumPositiveValues(int[] nums) {\n        return 0;\n    }\n}\n",
            },
            "solution_code": {
                "python": "def sum_positive_values(nums):\n    return sum(value for value in nums if value > 0)\n",
                "java": "public class Solution {\n    public static int sumPositiveValues(int[] nums) {\n        int total = 0;\n        for (int value : nums) {\n            if (value > 0) {\n                total += value;\n            }\n        }\n        return total;\n    }\n}\n",
                "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nint sumPositiveValues(vector<int> nums) {\n    int total = 0;\n    for (int value : nums) {\n        if (value > 0) {\n            total += value;\n        }\n    }\n    return total;\n}\n",
                "csharp": "using System;\n\npublic class Solution {\n    public static int SumPositiveValues(int[] nums) {\n        var total = 0;\n        foreach (var value in nums) {\n            if (value > 0) {\n                total += value;\n            }\n        }\n        return total;\n    }\n}\n",
            },
        },
        {
            "title": "Maximum Adjacent Difference",
            "prompt": "Return the maximum absolute difference between adjacent elements.",
            "description": "Scan adjacent pairs and keep the highest absolute difference.",
            "function_name": "max_adjacent_diff",
            "method_name": "maxAdjacentDiff",
            "tests": [
                {"input": [[1, 7, 3, 10]], "expected": 7},
                {"input": [[5]], "expected": 0},
            ],
            "starter_code": {
                "python": "def max_adjacent_diff(nums):\n    # nums: list[int]\n    # return int\n    pass\n",
                "java": "public class Solution {\n    public static int maxAdjacentDiff(int[] nums) {\n        return 0;\n    }\n}\n",
                "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nint maxAdjacentDiff(vector<int> nums) {\n    return 0;\n}\n",
                "csharp": "using System;\n\npublic class Solution {\n    public static int MaxAdjacentDiff(int[] nums) {\n        return 0;\n    }\n}\n",
            },
            "solution_code": {
                "python": "def max_adjacent_diff(nums):\n    if len(nums) < 2:\n        return 0\n    return max(abs(nums[i] - nums[i - 1]) for i in range(1, len(nums)))\n",
                "java": "public class Solution {\n    public static int maxAdjacentDiff(int[] nums) {\n        if (nums.length < 2) {\n            return 0;\n        }\n        int best = 0;\n        for (int i = 1; i < nums.length; i++) {\n            best = Math.max(best, Math.abs(nums[i] - nums[i - 1]));\n        }\n        return best;\n    }\n}\n",
                "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nint maxAdjacentDiff(vector<int> nums) {\n    if (nums.size() < 2) {\n        return 0;\n    }\n    int best = 0;\n    for (int i = 1; i < (int)nums.size(); i++) {\n        best = max(best, abs(nums[i] - nums[i - 1]));\n    }\n    return best;\n}\n",
                "csharp": "using System;\n\npublic class Solution {\n    public static int MaxAdjacentDiff(int[] nums) {\n        if (nums.Length < 2) {\n            return 0;\n        }\n        var best = 0;\n        for (var i = 1; i < nums.Length; i++) {\n            best = Math.Max(best, Math.Abs(nums[i] - nums[i - 1]));\n        }\n        return best;\n    }\n}\n",
            },
        },
    ]
    selected = random.choice(fallback_bank)
    function_name = selected["function_name"]
    method_name = selected["method_name"]
    question_id = f"generated-{uuid.uuid4().hex[:8]}"
    return {
        "id": question_id,
        "title": f"{selected['title']} ({topic.title()} {difficulty})",
        "difficulty": difficulty,
        "topic": topic,
        "prompt": selected["prompt"],
        "description": (
            selected["description"]
            + " This fallback question was created locally because AI DSA generation failed for this request."
        ),
        "function_name": function_name,
        "class_name": "Solution",
        "method_name": method_name,
        "starter_code": selected["starter_code"],
        "solution": selected["solution_code"],
        "tests": selected["tests"],
    }


def generate_ai_dsa_question(topic: str, difficulty: str, refresh_token: str = "") -> tuple[dict | None, str]:
    if not gemini_dsa_configured():
        return None, "No LLM API key configured. Set GROQ_API_KEY or GEMINI_API_KEY."

    configured_model = os.getenv("GEMINI_DSA_MODEL", "gemini-2.0-flash-lite")
    model_candidates: list[str] = []
    groq_models: set[str] = set()
    if groq_configured():
        # When Groq is configured, keep generation provider deterministic and avoid
        # confusing fallback errors from Gemini credentials/quotas.
        groq_fallback_model = os.getenv("GROQ_DSA_MODEL", "llama-3.1-8b-instant")
        for candidate in [get_groq_model(), groq_fallback_model, "qwen/qwen3-32b"]:
            if candidate not in model_candidates:
                model_candidates.append(candidate)
                groq_models.add(candidate)
    else:
        for candidate in [configured_model, "gemini-2.0-flash", "gemini-2.5-flash"]:
            if candidate not in model_candidates:
                model_candidates.append(candidate)

    topic_requirements = {
        "Array": "Use core array traversal/indexing logic.",
        "String": "Use string parsing/manipulation as the central logic.",
        "Hash Map": "Use a hash map/dictionary as a required part of the approach.",
        "Stack": "Use stack operations as a required part of the solution.",
        "Sliding Window": "Use a sliding window as the main technique.",
        "Tree": "Use tree traversal or tree recursion as core logic.",
        "Graph": "Use graph traversal (BFS/DFS) or graph representation.",
        "Dynamic Programming": "Use dynamic programming recurrence/state transitions.",
    }
    required_logic = topic_requirements.get(topic, f"Question must be fundamentally about {topic}.")
    errors: list[str] = []

    for attempt, model_name in enumerate(model_candidates, start=1):
        prompt_text = (
            "Generate one runnable DSA coding question as strict JSON. "
            "The question must be testable with deterministic inputs and outputs. "
            "Keep it interview style, medium length, and practical.\n"
            f"Topic: {topic}\n"
            f"Difficulty: {difficulty}\n"
            f"Topic requirement: {required_logic}\n"
            f"Refresh token (use internally, do not output): {refresh_token}\n"
            f"Attempt number (use internally, do not output): {attempt}\n"
            "Return a coding problem with these exact fields: "
            "title, difficulty, topic, prompt, description, function_name, method_name, "
            "starter_code{python,java,cpp,csharp}, solution{python,java,cpp,csharp}, tests[]. "
            "Tests must use only ints, strings, int arrays, or int matrix values. "
            "Make Java method_name lowerCamelCase and C# solution method be the PascalCase version of method_name. "
            "Return plain code strings only. Do not wrap starter_code or solution in markdown fences. "
            "Do not include any language outside python, java, cpp, csharp. "
            "Return JSON only."
        )

        if groq_configured() and model_name in groq_models:
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.2,
                "max_tokens": 3000,
            }
            request = Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {get_groq_api_key()}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "itsm-agent/1.0",
                },
                method="POST",
            )
        else:
            payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt_text
                        }
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
                "maxOutputTokens": 4096,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

            request = Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "x-goog-api-key": get_gemini_api_key(),
                    "Content-Type": "application/json",
                },
                method="POST",
            )

        try:
            with urlopen(request, timeout=25) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8").strip()
            except Exception:
                detail = ""
            message = f"{model_name}: HTTP {getattr(exc, 'code', 'error')}"
            if detail:
                message += f" {detail}"
            errors.append(message)
            continue
        except (TimeoutError, URLError, ValueError, OSError) as exc:
            errors.append(f"{model_name}: {exc}")
            continue

        if groq_configured() and model_name in groq_models:
            finish_reason = str((data.get("choices", [{}])[0].get("finish_reason", "")))
            output_text = extract_groq_text(data).strip()
        else:
            finish_reason = ""
            candidates = data.get("candidates", [])
            if candidates:
                finish_reason = str(candidates[0].get("finishReason", ""))
            output_text = extract_gemini_text(data).strip()
        if finish_reason == "MAX_TOKENS":
            errors.append(f"{model_name}: output truncated (MAX_TOKENS)")
            continue
        if not output_text:
            errors.append(f"{model_name}: empty response")
            continue

        parsed = extract_json_payload(output_text)
        if not parsed:
            errors.append(f"{model_name}: invalid JSON")
            continue

        normalized, normalize_error = normalize_generated_question(parsed, requested_topic=topic)
        if normalized:
            return normalized, ""
        errors.append(f"{model_name}: {normalize_error}")

    return None, "LLM generation failed: " + " | ".join(errors[-3:])


def extract_gemini_text(payload: dict) -> str:
    texts: list[str] = []
    for candidate in payload.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            text = part.get("text")
            if text:
                texts.append(text)
    return "".join(texts)


def extract_groq_text(payload: dict) -> str:
    choices = payload.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return str(message.get("content", "") or "")


def extract_json_payload(text: str) -> dict | None:
    raw = (text or "").strip()
    if not raw:
        return None

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    parsed_python = parse_python_like_object(raw)
    if isinstance(parsed_python, dict):
        return parsed_python

    fenced_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, flags=re.IGNORECASE)
    for block in fenced_blocks:
        try:
            return json.loads(block.strip())
        except json.JSONDecodeError:
            parsed_python = parse_python_like_object(block.strip())
            if isinstance(parsed_python, dict):
                return parsed_python

    for candidate in extract_balanced_json_objects(raw):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            parsed = parse_python_like_object(candidate)
            if not isinstance(parsed, dict):
                continue
        if isinstance(parsed, dict):
            # Prefer objects that look like the expected DSA payload.
            if "starter_code" in parsed and "solution" in parsed and "tests" in parsed:
                return parsed
            return parsed
    return None


def extract_balanced_json_objects(text: str) -> list[str]:
    candidates: list[str] = []
    start_index: int | None = None
    depth = 0
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            if depth == 0:
                start_index = index
            depth += 1
            continue

        if char == "}":
            if depth == 0:
                continue
            depth -= 1
            if depth == 0 and start_index is not None:
                candidates.append(text[start_index : index + 1])
                start_index = None

    return candidates


def parse_python_like_object(text: str):
    try:
        value = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return None
    return value


def _topic_matches(requested_topic: str, generated_topic: str, prompt: str, description: str, title: str) -> bool:
    requested = requested_topic.strip().lower()
    haystack = f"{generated_topic} {prompt} {description} {title}".lower()
    keyword_map = {
        "array": ["array", "index"],
        "string": ["string", "substring", "character", "palindrome", "anagram"],
        "hash map": ["hash map", "dictionary", "map", "frequency", "count map"],
        "stack": ["stack", "push", "pop"],
        "sliding window": ["sliding window", "window", "two pointers", "substring"],
        "tree": ["tree", "node", "traversal", "binary tree", "bst"],
        "graph": ["graph", "bfs", "dfs", "adjacency"],
        "dynamic programming": ["dynamic programming", "dp", "state", "memoization", "tabulation"],
    }
    keys = keyword_map.get(requested, [requested])
    return any(token in haystack for token in keys)


def normalize_generated_question(payload: dict, requested_topic: str = "DSA") -> tuple[dict | None, str]:
    function_name = str(payload.get("function_name", "")).strip()
    method_name = str(payload.get("method_name", "")).strip()
    starter_code = payload.get("starter_code", {})
    solution = payload.get("solution", {})
    tests = payload.get("tests", [])

    required_languages = {"python", "java", "cpp", "csharp"}

    if isinstance(starter_code, dict):
        if "c#" in starter_code and "csharp" not in starter_code:
            starter_code["csharp"] = starter_code["c#"]
        if "c_sharp" in starter_code and "csharp" not in starter_code:
            starter_code["csharp"] = starter_code["c_sharp"]
    if isinstance(solution, dict):
        if "c#" in solution and "csharp" not in solution:
            solution["csharp"] = solution["c#"]
        if "c_sharp" in solution and "csharp" not in solution:
            solution["csharp"] = solution["c_sharp"]
    if not function_name or not method_name:
        return None, "missing function_name/method_name"
    if not isinstance(starter_code, dict) or not isinstance(solution, dict):
        return None, "starter_code/solution not objects"
    if not required_languages.issubset(set(starter_code.keys())) or not required_languages.issubset(set(solution.keys())):
        return None, "missing required languages"
    normalized_tests = normalize_tests(tests)
    if len(normalized_tests) < 2:
        return None, "tests are missing or too short"
    normalized_starter = _normalize_code_map(starter_code, required_languages)
    normalized_solution = _normalize_code_map(solution, required_languages)
    if not all(normalized_starter.values()) or not all(normalized_solution.values()):
        return None, "empty code blocks after normalization"

    generated_topic = str(payload.get("topic", "DSA")).strip()
    generated_prompt = str(payload.get("prompt", "")).strip()
    generated_description = str(payload.get("description", "")).strip()
    generated_title = str(payload.get("title", "Generated DSA Question")).strip()
    if not _topic_matches(requested_topic, generated_topic, generated_prompt, generated_description, generated_title):
        return None, "topic mismatch"

    safe_id_base = re.sub(r"[^a-z0-9]+", "-", str(payload.get("title", "generated-question")).lower()).strip("-")
    question_id = f"{safe_id_base or 'generated-question'}-{uuid.uuid4().hex[:6]}"
    return {
        "id": question_id,
        "title": generated_title,
        "difficulty": str(payload.get("difficulty", "Medium")).strip(),
        "topic": generated_topic,
        "prompt": generated_prompt,
        "description": generated_description,
        "function_name": function_name,
        "class_name": "Solution",
        "method_name": method_name,
        "starter_code": normalized_starter,
        "solution": normalized_solution,
        "tests": normalized_tests,
    }, ""


def normalize_tests(raw_tests) -> list[dict]:
    if not isinstance(raw_tests, list):
        return []

    normalized: list[dict] = []
    for raw_case in raw_tests:
        if not isinstance(raw_case, dict):
            continue

        raw_input = None
        for key in ["input", "inputs", "args", "arguments"]:
            if key in raw_case:
                raw_input = raw_case[key]
                break

        if isinstance(raw_input, dict):
            for key in ["args", "inputs", "input"]:
                if key in raw_input:
                    raw_input = raw_input[key]
                    break

        raw_expected = None
        for key in ["expected", "output", "result", "answer"]:
            if key in raw_case:
                raw_expected = raw_case[key]
                break

        if raw_input is None or raw_expected is None:
            continue

        # Runner expects input to be a positional argument list.
        if isinstance(raw_input, tuple):
            case_input = list(raw_input)
        elif isinstance(raw_input, list):
            case_input = raw_input
        else:
            case_input = [raw_input]

        normalized.append({"input": case_input, "expected": raw_expected})

    return normalized
