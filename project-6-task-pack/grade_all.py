"""Run every task's reference solution through its checker.

This is the pack's regression test: a task ships only if its reference
scores 100/100 under its own checker, with the checker on an
independent solution path. Exit code 0 iff the whole pack passes.
"""
import subprocess
import sys
from pathlib import Path

TASKS = sorted(p for p in (Path(__file__).parent / "tasks").iterdir()
               if p.is_dir())


def run(cmd, cwd):
    r = subprocess.run([sys.executable, cmd], cwd=cwd,
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main() -> int:
    failures = 0
    for t in TASKS:
        rc, out = run("reference_solution.py", t)
        if rc != 0:
            print(f"[{t.name}] reference solution FAILED to run:\n{out}")
            failures += 1
            continue
        rc, out = run("checker.py", t)
        filtered = "\n".join(l for l in out.splitlines()
                             if "Process 0" not in l)
        print(f"[{t.name}]\n{filtered}\n")
        failures += rc != 0
    print(f"pack result: {len(TASKS) - failures}/{len(TASKS)} tasks pass")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
