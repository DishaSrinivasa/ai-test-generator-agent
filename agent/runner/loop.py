"""Run pytest on generated tests; feed failures back to Ollama for revision."""
import subprocess
import tempfile
import textwrap
from pathlib import Path
import ollama

MODEL = "llama3.2"
MAX_ITERATIONS = 3

FIX_SYSTEM_PROMPT = """\
You are an expert Python test engineer. You will be given a pytest test file and \
the pytest failure output. Fix only the failing tests. Return the COMPLETE corrected \
Python file — no markdown fences, no explanation.
"""


def _run_pytest(test_path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["python", "-m", "pytest", str(test_path), "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )
    passed = result.returncode == 0
    output = result.stdout + result.stderr
    return passed, output


def run_and_fix(test_code: str) -> tuple[str, bool, list[str]]:
    """
    Run test_code, fix failures with Ollama, repeat up to MAX_ITERATIONS.
    Returns (final_code, all_passed, iteration_logs).
    """
    logs: list[str] = []

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(test_code)
        test_path = Path(f.name)

    current_code = test_code

    for iteration in range(1, MAX_ITERATIONS + 1):
        test_path.write_text(current_code)
        passed, output = _run_pytest(test_path)
        logs.append(f"--- Iteration {iteration} ---\n{output}")

        if passed:
            test_path.unlink(missing_ok=True)
            return current_code, True, logs

        # Ask Ollama to fix
        prompt = (
            f"Here is the test file:\n\n{current_code}\n\n"
            f"Here is the pytest failure output:\n\n{output}\n\n"
            "Fix the failing tests and return the complete corrected file."
        )
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": FIX_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        fixed = response["message"]["content"].strip()
        if fixed.startswith("```"):
            lines = fixed.splitlines()
            fixed = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        current_code = fixed

    test_path.unlink(missing_ok=True)
    return current_code, False, logs
