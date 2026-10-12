"""Tests for guard.py. Run: python -m unittest discover -s guard -v

Every case runs twice: once as a Claude Code payload and once as a Jcode
payload, through the real command-line entry point.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD = HERE / "guard.py"
sys.path.insert(0, str(HERE))
import plans  # noqa: E402

PLAN_TEMPLATE = """---
title: test plan
status: proposed
---

# Test plan

## Brainstorming
Goal stated.

## Existing code (improve)
Survey done.

## Simplification (ponytail)
Nothing to cut.

## Architecture (archify)
Single component, no diagram: one file change.

## Quality review (thermo-nuclear)
No findings.
"""


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class Repo:
    """A real git repository with a bare remote and upstream branches."""

    def __init__(self):
        self.root_dir = Path(tempfile.mkdtemp(prefix="mcs-guard-"))
        self.remote = self.root_dir / "remote.git"
        self.path = self.root_dir / "work"
        git(self.root_dir, "init", "-q", "--bare", str(self.remote))
        git(self.root_dir, "init", "-q", "-b", "main", str(self.path))
        git(self.path, "config", "user.email", "test@example.com")
        git(self.path, "config", "user.name", "Test")
        (self.path / "Docs" / "Plans").mkdir(parents=True)
        (self.path / ".mcs").mkdir()
        git(self.path, "commit", "-q", "--allow-empty", "-m", "init")
        git(self.path, "remote", "add", "origin", str(self.remote))
        git(self.path, "push", "-q", "-u", "origin", "main")
        git(self.path, "checkout", "-q", "-b", "feature/x")
        git(self.path, "push", "-q", "-u", "origin", "feature/x")

    def checkout(self, branch):
        git(self.path, "checkout", "-q", branch)

    def write_plan(self, name="p1", approve=False, branch="feature/x", crlf=False, tamper=False):
        text = PLAN_TEMPLATE
        if approve:
            text = plans.approve_text(text, approver="Test", branch=branch, when="2026-10-12T00:00:00Z")
        if tamper:
            text = text.replace("Nothing to cut.", "Nothing to cut. Changed later.")
        if crlf:
            text = text.replace("\n", "\r\n")
        (self.path / "Docs" / "Plans" / f"{name}.md").write_bytes(text.encode())

    def clear_plans(self):
        for f in (self.path / "Docs" / "Plans").glob("*.md"):
            f.unlink()

    def close(self):
        shutil.rmtree(self.root_dir, ignore_errors=True)


def run_guard(agent, tool_kind, cwd, command=None, path=None, content=None):
    if agent == "claude-code":
        name = {"shell": "Bash", "edit": "Edit", "write": "Write", "other": "Read"}[tool_kind]
        tool_input = {}
        if command is not None:
            tool_input["command"] = command
        if path is not None:
            tool_input["file_path"] = path
        if content is not None:
            tool_input["new_string" if tool_kind == "edit" else "content"] = content
        payload = {"tool_name": name, "tool_input": tool_input, "cwd": str(cwd)}
        env = dict(os.environ)
    else:
        name = {"shell": "bash", "edit": "edit", "write": "write", "other": "read"}[tool_kind]
        payload = {}
        if command is not None:
            payload["command"] = command
        if path is not None:
            payload["file_path"] = path
        if content is not None:
            payload["new_string" if tool_kind == "edit" else "content"] = content
        env = dict(os.environ, JCODE_HOOK_TOOL_NAME=name, JCODE_HOOK_CWD=str(cwd))
    proc = subprocess.run(
        [sys.executable, str(GUARD), "--agent", agent],
        input=json.dumps(payload), capture_output=True, text=True, env=env, cwd=str(cwd),
    )
    if agent == "claude-code":
        if proc.returncode != 0:
            raise AssertionError(f"claude-code adapter must exit 0, got {proc.returncode}: {proc.stderr}")
        if proc.stdout.strip():
            decision = json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"]
            return decision == "deny"
        return False
    if proc.returncode not in (0, 2):
        raise AssertionError(f"unexpected exit {proc.returncode}: {proc.stderr}")
    return proc.returncode == 2


AGENTS = ("claude-code", "jcode")


class GuardCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repo()

    @classmethod
    def tearDownClass(cls):
        cls.repo.close()

    def check(self, blocked, kind, command=None, path=None, content=None, branch="feature/x"):
        self.repo.checkout(branch)
        for agent in AGENTS:
            with self.subTest(agent=agent, command=command, path=path):
                got = run_guard(agent, kind, self.repo.path, command=command, path=path, content=content)
                self.assertEqual(got, blocked, f"{agent}: {command or path} expected blocked={blocked}")


class FlashRules(GuardCase):
    BLOCKED = [
        "JLinkExe -device EFM32GG11 -if SWD",
        "JLinkGDBServerCLExe -port 2331",
        "JLinkRemoteServer",
        "docker exec debug-tools JLinkExe -IP host.docker.internal -CommanderScript s.jlink",
        "openocd -s cfg -f openocd.tcl -c 'program fw.hex verify reset exit'",
        "pyocd flash fw.hex",
        "probe-rs download fw.elf",
        "nrfjprog --program fw.hex",
        "commander flash fw.s37",
        "st-flash write fw.bin 0x8000000",
        "./Scripts/flash.sh",
        "bash Scripts/flash.sh --app AIDAPT",
        "sh -c 'Scripts/erase.sh'",
        "./Scripts/run.sh",
        "./Scripts/debug.sh",
        "./Scripts/dev-env.sh up",
        "make flash",
        "cmake --build build --target flash",
        "cd Scripts && ./erase.sh",
        "pwsh -c Scripts/flash.ps1",
    ]
    ALLOWED = [
        "./Scripts/build.sh AIDAPT_TrialsTest debug",
        "cmake --build build",
        "make -j8",
        "grep -rn flash src/",
        "cat Scripts/flash.sh",
        "echo flashing is done by a human",
        "git log --oneline -- Scripts/flash.sh",
    ]

    def test_blocked(self):
        for cmd in self.BLOCKED:
            self.check(True, "shell", command=cmd)

    def test_allowed(self):
        for cmd in self.ALLOWED:
            self.check(False, "shell", command=cmd)


class GitRules(GuardCase):
    def test_bare_push_on_main_with_upstream_blocked(self):
        self.check(True, "shell", command="git push", branch="main")

    def test_push_origin_without_refspec_on_main_blocked(self):
        self.check(True, "shell", command="git push origin", branch="main")

    def test_push_origin_head_on_main_blocked(self):
        self.check(True, "shell", command="git push origin HEAD", branch="main")

    def test_explicit_refspecs_blocked(self):
        for cmd in [
            "git push origin main",
            "git push origin HEAD:main",
            "git push origin feature/x:develop",
            "git push origin +HEAD:release/1.2",
            "git push origin feature/x:refs/heads/main",
            "git push -u origin develop",
            "git push --force-with-lease origin develop",
            "git push -f origin main",
            "git push --all origin",
            "git push --mirror origin",
            "git -C . push origin main",
            "cd sub && git push origin main",
            "gh pr merge 12 --squash",
        ]:
            self.check(True, "shell", command=cmd)

    def test_rebase_on_protected_blocked(self):
        self.check(True, "shell", command="git rebase origin/feature/x", branch="main")

    def test_feature_pushes_allowed(self):
        for cmd in [
            "git push",
            "git push origin",
            "git push origin HEAD",
            "git push origin feature/x",
            "git push -u origin feature/y",
            "git push --force-with-lease origin feature/x",
            "git push origin --tags",
            "git status",
            "git rebase origin/main",
            "gh pr create --fill",
            "gh pr view 12",
        ]:
            self.check(False, "shell", command=cmd)


class PlanRules(GuardCase):
    def setUp(self):
        self.repo.clear_plans()

    def test_code_edit_without_plan_blocked(self):
        for p in ["src/a.c", "src\\a.c", "include/b.h", "app/lib/main.dart", "tools/x.py"]:
            self.check(True, "edit", path=p, content="x")
            self.check(True, "write", path=p, content="x")

    def test_absolute_paths_normalized(self):
        self.check(True, "edit", path=str(self.repo.path / "src" / "a.c"), content="x")

    def test_docs_and_config_always_allowed(self):
        for p in ["Docs/Plans/new.md", "README.md", "AGENTS.md", ".gitignore", "notes.txt", "CMakePresets.json"]:
            self.check(False, "edit", path=p, content="x")

    def test_shell_writes_to_code_blocked(self):
        for cmd in ["echo 1 > src/a.c", "printf x >> include/b.h", "sed -i 's/a/b/' src/a.c", "cat x | tee src/a.c"]:
            self.check(True, "shell", command=cmd)

    def test_shell_writes_elsewhere_allowed(self):
        for cmd in ["echo 1 > /tmp/x.c", "echo 1 > build.log", "ls > files.txt"]:
            self.check(False, "shell", command=cmd)

    def test_approved_plan_allows_code(self):
        self.repo.write_plan(approve=True)
        self.check(False, "edit", path="src/a.c", content="x")

    def test_approved_plan_crlf_still_valid(self):
        self.repo.write_plan(approve=True, crlf=True)
        self.check(False, "edit", path="src/a.c", content="x")

    def test_tampered_plan_blocks(self):
        self.repo.write_plan(approve=True, tamper=True)
        self.check(True, "edit", path="src/a.c", content="x")

    def test_plan_for_other_branch_blocks(self):
        self.repo.write_plan(approve=True, branch="feature/other")
        self.check(True, "edit", path="src/a.c", content="x")

    def test_proposed_plan_blocks(self):
        self.repo.write_plan(approve=False)
        self.check(True, "edit", path="src/a.c", content="x")


class ApproveRules(GuardCase):
    def test_mcs_approve_blocked(self):
        for cmd in [
            "mcs approve p1",
            "python .mcs/bin/mcs approve p1",
            ".mcs/bin/mcs   approve p1",
            "py -3 .mcs\\bin\\mcs approve p1",
            "echo y | mcs approve p1",
        ]:
            self.check(True, "shell", command=cmd)

    def test_mcs_status_allowed(self):
        for cmd in ["mcs status", "python .mcs/bin/mcs check"]:
            self.check(False, "shell", command=cmd)

    def test_writing_approved_status_blocked(self):
        self.check(True, "edit", path="Docs/Plans/p1.md", content="status: approved")
        self.check(True, "write", path="Docs/Plans/p1.md", content="---\nstatus: approved\n---\n")
        self.check(True, "shell", command="sed -i 's/status: proposed/status: approved/' Docs/Plans/p1.md")

    def test_writing_proposed_plan_allowed(self):
        self.check(False, "write", path="Docs/Plans/p2.md", content="---\nstatus: proposed\n---\n")


class OtherTools(GuardCase):
    def test_read_always_allowed(self):
        self.check(False, "other", path="src/a.c")


class Robustness(unittest.TestCase):
    def test_garbage_input_allows_and_logs(self):
        tmp = Path(tempfile.mkdtemp(prefix="mcs-guard-garbage-"))
        try:
            env = dict(os.environ, JCODE_HOOK_TOOL_NAME="bash", JCODE_HOOK_CWD=str(tmp))
            proc = subprocess.run([sys.executable, str(GUARD), "--agent", "jcode"],
                                  input="{not json", capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_speed(self):
        import time
        repo = Repo()
        try:
            start = time.perf_counter()
            for _ in range(20):
                run_guard("jcode", "shell", repo.path, command="git push origin main")
            avg_ms = (time.perf_counter() - start) * 1000 / 20
            self.assertLess(avg_ms, 500, f"average {avg_ms:.0f} ms per call")
        finally:
            repo.close()


if __name__ == "__main__":
    unittest.main()
