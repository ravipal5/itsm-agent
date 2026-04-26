import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


def run_dsa_code(question: dict, user_code: str, language: str) -> dict:
    if language == "python":
        return run_python(question, user_code)
    if language == "java":
        return run_java(question, user_code)
    if language == "cpp":
        return run_cpp(question, user_code)
    if language == "csharp":
        return run_csharp(question, user_code)
    return {"ok": False, "error": f"Unsupported language: {language}", "results": []}


def run_python(question: dict, user_code: str) -> dict:
    test_payload = json.dumps(question["tests"])
    runner_script = textwrap.dedent(
        f"""
        import json

        {user_code}

        tests = json.loads({test_payload!r})
        function_name = {question["function_name"]!r}
        target = globals().get(function_name)
        if target is None:
            raise NameError(f"Function '{{function_name}}' is not defined.")

        results = []
        for index, case in enumerate(tests, start=1):
            actual = target(*case["input"])
            passed = actual == case["expected"]
            results.append({{
                "case": index,
                "passed": passed,
                "expected": case["expected"],
                "actual": actual,
            }})

        print(json.dumps(results))
        """
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "runner.py"
        script_path.write_text(runner_script, encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    return parse_completed(completed)


def run_java(question: dict, user_code: str) -> dict:
    if not shutil.which("javac") or not shutil.which("java"):
        return {"ok": False, "error": "Java compiler/runtime not found. Install JDK and ensure `javac` and `java` are on PATH.", "results": []}

    test_payload = json.dumps(question["tests"])
    driver_code = textwrap.dedent(
        f"""
        import java.util.*;

        public class Main {{
            private static String toJsonValue(Object value) {{
                if (value instanceof int[]) {{
                    return Arrays.toString((int[]) value).replace(" ", "");
                }}
                if (value instanceof int[][]) {{
                    return Arrays.deepToString((int[][]) value).replace(" ", "");
                }}
                if (value instanceof boolean[]) {{
                    return Arrays.toString((boolean[]) value).replace(" ", "");
                }}
                return String.valueOf(value);
            }}

            public static void main(String[] args) {{
                List<Map<String, String>> results = new ArrayList<>();
                String payload = {json.dumps(test_payload)};
                String[][] expected = new String[][] {{
                    {",".join("{" + ",".join(json.dumps(str(v).replace(" ", "")) for v in [case["expected"]]) + "}" for case in question["tests"])}
                }};
                int caseIndex = 1;
        """
    )

    invocations = []
    for case in question["tests"]:
        args_literal = ", ".join(to_java_literal(value) for value in case["input"])
        invocations.append(
            textwrap.dedent(
                f"""
                        {{
                            Object actual = Solution.{question["method_name"]}({args_literal});
                            String actualJson = toJsonValue(actual);
                            String expectedJson = {json.dumps(str(case["expected"]).replace(" ", ""))};
                            boolean passed = actualJson.equals(expectedJson);
                            System.out.println(caseIndex + "|" + passed + "|" + expectedJson + "|" + actualJson);
                            caseIndex++;
                        }}
                """
            )
        )
    driver_code += "".join(invocations) + "\n    }\n}\n"

    with tempfile.TemporaryDirectory() as temp_dir:
        solution_path = Path(temp_dir) / "Solution.java"
        main_path = Path(temp_dir) / "Main.java"
        solution_path.write_text(user_code, encoding="utf-8")
        main_path.write_text(driver_code, encoding="utf-8")
        compile_result = subprocess.run(
            ["javac", str(solution_path), str(main_path)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=temp_dir,
        )
        if compile_result.returncode != 0:
            return {"ok": False, "error": (compile_result.stderr or compile_result.stdout).strip(), "results": []}
        completed = subprocess.run(
            ["java", "Main"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=temp_dir,
        )
    return parse_line_results(completed)


def run_cpp(question: dict, user_code: str) -> dict:
    if not shutil.which("g++"):
        return {"ok": False, "error": "C++ compiler not found. Install g++ and ensure it is on PATH.", "results": []}

    runner_code = textwrap.dedent(
        f"""
        #include <bits/stdc++.h>
        using namespace std;

        {user_code}

        string vectorToString(const vector<int>& values) {{
            stringstream ss;
            ss << "[";
            for (size_t index = 0; index < values.size(); index++) {{
                if (index) ss << ",";
                ss << values[index];
            }}
            ss << "]";
            return ss.str();
        }}

        string matrixToString(const vector<vector<int>>& values) {{
            stringstream ss;
            ss << "[";
            for (size_t row = 0; row < values.size(); row++) {{
                if (row) ss << ",";
                ss << vectorToString(values[row]);
            }}
            ss << "]";
            return ss.str();
        }}

        int main() {{
        """
    )
    invocations = []
    for index, case in enumerate(question["tests"], start=1):
        args_literal = ", ".join(to_cpp_literal(value) for value in case["input"])
        expected_literal = normalized_expected_literal(case["expected"])
        formatter = formatter_for_expected(case["expected"])
        invocations.append(
            textwrap.dedent(
                f"""
                    {{
                        auto actual = {question["method_name"]}({args_literal});
                        string actualValue = {formatter}(actual);
                        string expectedValue = {json.dumps(expected_literal)};
                        bool passed = actualValue == expectedValue;
                        cout << {index} << "|" << (passed ? "true" : "false") << "|" << expectedValue << "|" << actualValue << "\\n";
                    }}
                """
            )
        )
    runner_code += "".join(invocations) + "\n    return 0;\n}\n"

    with tempfile.TemporaryDirectory() as temp_dir:
        cpp_path = Path(temp_dir) / "main.cpp"
        exe_path = Path(temp_dir) / "main.exe"
        cpp_path.write_text(runner_code, encoding="utf-8")
        compile_result = subprocess.run(
            ["g++", "-std=c++17", str(cpp_path), "-o", str(exe_path)],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=temp_dir,
        )
        if compile_result.returncode != 0:
            return {"ok": False, "error": (compile_result.stderr or compile_result.stdout).strip(), "results": []}
        completed = subprocess.run(
            [str(exe_path)],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=temp_dir,
        )
    return parse_line_results(completed)


def run_csharp(question: dict, user_code: str) -> dict:
    dotnet = shutil.which("dotnet")
    if not dotnet:
        return {"ok": False, "error": ".NET SDK not found. Install `dotnet` and ensure it is on PATH.", "results": []}

    program_code = textwrap.dedent(
        f"""
        using System;
        using System.Collections.Generic;
        using System.Linq;

        {user_code}

        public static class Program
        {{
            private static string ToDisplay(object value)
            {{
                if (value is int[] array)
                {{
                    return "[" + string.Join(",", array) + "]";
                }}
                if (value is int[][] matrix)
                {{
                    return "[" + string.Join(",", matrix.Select(row => "[" + string.Join(",", row) + "]")) + "]";
                }}
                if (value is bool flag)
                {{
                    return flag ? "true" : "false";
                }}
                return value?.ToString() ?? string.Empty;
            }}

            public static void Main()
            {{
        """
    )

    invocations = []
    for index, case in enumerate(question["tests"], start=1):
        args_literal = ", ".join(to_csharp_literal(value) for value in case["input"])
        method_name = question["method_name"][0].upper() + question["method_name"][1:]
        expected_literal = normalized_expected_literal(case["expected"])
        invocations.append(
            textwrap.dedent(
                f"""
                        {{
                            var actual = Solution.{method_name}({args_literal});
                            var actualValue = ToDisplay(actual);
                            var expectedValue = {json.dumps(expected_literal)};
                            var passed = actualValue == expectedValue;
                            Console.WriteLine("{index}|" + (passed ? "true" : "false") + "|" + expectedValue + "|" + actualValue);
                        }}
                """
            )
        )
    program_code += "".join(invocations) + "\n    }\n}\n"

    csproj = textwrap.dedent(
        """
        <Project Sdk="Microsoft.NET.Sdk">
          <PropertyGroup>
            <OutputType>Exe</OutputType>
            <TargetFramework>net8.0</TargetFramework>
            <ImplicitUsings>enable</ImplicitUsings>
            <Nullable>enable</Nullable>
          </PropertyGroup>
        </Project>
        """
    ).strip()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        (temp_path / "Runner.csproj").write_text(csproj, encoding="utf-8")
        (temp_path / "Program.cs").write_text(program_code, encoding="utf-8")
        completed = subprocess.run(
            [dotnet, "run", "--project", str(temp_path / "Runner.csproj")],
            capture_output=True,
            text=True,
            timeout=20,
            cwd=temp_dir,
        )
    return parse_line_results(completed)


def parse_completed(completed: subprocess.CompletedProcess) -> dict:
    if completed.returncode != 0:
        return {"ok": False, "error": (completed.stderr or completed.stdout or "Unknown execution error").strip(), "results": []}
    return {"ok": True, "error": "", "results": json.loads(completed.stdout)}


def parse_line_results(completed: subprocess.CompletedProcess) -> dict:
    if completed.returncode != 0:
        return {"ok": False, "error": (completed.stderr or completed.stdout or "Unknown execution error").strip(), "results": []}
    results = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        case_no, passed, expected, actual = line.split("|", 3)
        results.append({"case": int(case_no), "passed": passed == "true", "expected": expected, "actual": actual})
    return {"ok": True, "error": "", "results": results}


def to_java_literal(value):
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        if value and isinstance(value[0], list):
            rows = ", ".join("{" + ", ".join(str(item) for item in row) + "}" for row in value)
            return f"new int[][]{{{rows}}}"
        return "new int[]{" + ", ".join(str(item) for item in value) + "}"
    raise ValueError(f"Unsupported Java literal: {value!r}")


def to_cpp_literal(value):
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        if value and isinstance(value[0], list):
            rows = ", ".join("{" + ", ".join(str(item) for item in row) + "}" for row in value)
            return f"vector<vector<int>>{{{rows}}}"
        return "vector<int>{" + ", ".join(str(item) for item in value) + "}"
    raise ValueError(f"Unsupported C++ literal: {value!r}")


def to_csharp_literal(value):
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        if value and isinstance(value[0], list):
            rows = ", ".join("new[] {" + ", ".join(str(item) for item in row) + "}" for row in value)
            return f"new[] {{ {rows} }}"
        return "new[] {" + ", ".join(str(item) for item in value) + "}"
    raise ValueError(f"Unsupported C# literal: {value!r}")


def normalized_expected_literal(value):
    return json.dumps(value, separators=(",", ":")).replace('"', "")


def formatter_for_expected(value):
    if isinstance(value, bool):
        return "[](bool value){ return value ? string(\"true\") : string(\"false\"); }"
    if isinstance(value, int):
        return "[](int value){ return to_string(value); }"
    if isinstance(value, list) and value and isinstance(value[0], list):
        return "matrixToString"
    return "vectorToString"
