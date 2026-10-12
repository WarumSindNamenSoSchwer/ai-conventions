"""Tests for bin/mcs. Run: python -m unittest discover -s bin -p 'test_*.py'"""

import importlib.machinery
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "guard"))
import plans  # noqa: E402

loader = importlib.machinery.SourceFileLoader("mcs", str(HERE / "mcs"))
spec = importlib.util.spec_from_loader("mcs", loader)
mcs = importlib.util.module_from_spec(spec)
loader.exec_module(mcs)

GOOD_BODY = """# Plan: feature x

## Goal
Do x.

## Brainstorming
Options A and B, chose A.

## Existing code (improve)
Module y does z.

## Simplification (ponytail)
Dropped option B.

## Architecture (archify)
Single component, no diagram: one function in one file.

## Quality review (thermo-nuclear)
No findings.
"""


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class McsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q", "-b", "feature/x")
        git(self.root, "config", "user.name", "Test Human")
        git(self.root, "config", "user.email", "t@example.com")
        git(self.root, "commit", "-q", "--allow-empty", "-m", "init")
        (self.root / "Docs" / "Plans").mkdir(parents=True)
        self.cwd = os.getcwd()
        os.chdir(self.root)
        self.saved_env = {k: os.environ.pop(k) for k in list(os.environ)
                          if k in ("CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "JCODE_SESSION_ID")}

    def tearDown(self):
        os.environ.update(self.saved_env)
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def write_plan(self, name, body=GOOD_BODY, meta=None):
        path = self.root / "Docs" / "Plans" / f"{name}.md"
        text = body if meta is None else plans.join_front_matter(meta, body)
        path.write_text(text, encoding="utf-8")
        return path

    def run_mcs(self, *args, answer=""):
        out, err = io.StringIO(), io.StringIO()
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(answer + "\n")
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = mcs.main(list(args))
        finally:
            sys.stdin = old_stdin
        return code, out.getvalue() + err.getvalue()

    # approve ---------------------------------------------------------------

    def test_approve_writes_metadata_and_valid_hash(self):
        path = self.write_plan("x")
        code, out = self.run_mcs("approve", "x", answer="x")
        self.assertEqual(code, 0, out)
        meta, _ = plans.split_front_matter(path.read_text(encoding="utf-8"))
        self.assertEqual(meta["status"], "approved")
        self.assertEqual(meta["approved_by"], "Test Human")
        self.assertEqual(meta["branch"], "feature/x")
        self.assertTrue(meta["approved_at"])
        self.assertTrue(plans.is_valid_approval(path.read_text(encoding="utf-8"), "feature/x"))

    def test_approve_accepts_path_and_md_suffix(self):
        self.write_plan("x")
        code, out = self.run_mcs("approve", "Docs/Plans/x.md", answer="x")
        self.assertEqual(code, 0, out)

    def test_refuses_wrong_typed_name(self):
        path = self.write_plan("x")
        code, out = self.run_mcs("approve", "x", answer="y")
        self.assertEqual(code, 1)
        self.assertNotIn("approved", path.read_text(encoding="utf-8"))

    def test_refuses_empty_answer(self):
        self.write_plan("x")
        code, _ = self.run_mcs("approve", "x", answer="")
        self.assertEqual(code, 1)

    def test_refuses_missing_section(self):
        self.write_plan("x", GOOD_BODY.replace("## Simplification (ponytail)\nDropped option B.\n", ""))
        code, out = self.run_mcs("approve", "x", answer="x")
        self.assertEqual(code, 1)
        self.assertIn("Simplification (ponytail)", out)

    def test_refuses_empty_section(self):
        self.write_plan("x", GOOD_BODY.replace("Module y does z.", ""))
        code, out = self.run_mcs("approve", "x", answer="x")
        self.assertEqual(code, 1)
        self.assertIn("empty section", out)

    def test_refuses_missing_archify_file(self):
        body = GOOD_BODY.replace("Single component, no diagram: one function in one file.",
                                 "[Diagram](x.architecture.html)")
        self.write_plan("x", body)
        code, out = self.run_mcs("approve", "x", answer="x")
        self.assertEqual(code, 1)
        self.assertIn("not found", out)

    def test_accepts_existing_archify_file(self):
        body = GOOD_BODY.replace("Single component, no diagram: one function in one file.",
                                 "[Diagram](x.architecture.html)")
        self.write_plan("x", body)
        (self.root / "Docs" / "Plans" / "x.architecture.html").write_text("<html></html>")
        code, out = self.run_mcs("approve", "x", answer="x")
        self.assertEqual(code, 0, out)

    def test_refuses_archify_without_link_or_reason(self):
        self.write_plan("x", GOOD_BODY.replace("Single component, no diagram: one function in one file.", "TBD"))
        code, out = self.run_mcs("approve", "x", answer="x")
        self.assertEqual(code, 1)
        self.assertIn("Single component, no diagram:", out)

    def test_refuses_unknown_plan(self):
        code, out = self.run_mcs("approve", "nope", answer="nope")
        self.assertEqual(code, 1)
        self.assertIn("not found", out)

    def test_refuses_detached_head(self):
        self.write_plan("x")
        git(self.root, "checkout", "-q", "--detach")
        code, out = self.run_mcs("approve", "x", answer="x")
        self.assertEqual(code, 1)
        self.assertIn("branch", out)

    def test_refuses_inside_agent_session(self):
        self.write_plan("x")
        for var in ("CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "JCODE_SESSION_ID"):
            os.environ[var] = "1"
            try:
                code, out = self.run_mcs("approve", "x", answer="x")
            finally:
                del os.environ[var]
            self.assertEqual(code, 1, var)
            self.assertIn("agent", out)

    def test_supersedes_older_plan_on_same_branch(self):
        old = self.write_plan("old")
        self.assertEqual(self.run_mcs("approve", "old", answer="old")[0], 0)
        other = self.write_plan("other", meta={"status": "approved", "branch": "feature/y"})
        self.write_plan("new")
        self.assertEqual(self.run_mcs("approve", "new", answer="new")[0], 0)
        old_meta, _ = plans.split_front_matter(old.read_text(encoding="utf-8"))
        other_meta, _ = plans.split_front_matter(other.read_text(encoding="utf-8"))
        self.assertEqual(old_meta["status"], "superseded")
        self.assertEqual(other_meta["status"], "approved")

    def test_reapprove_after_edit(self):
        path = self.write_plan("x")
        self.run_mcs("approve", "x", answer="x")
        path.write_text(path.read_text(encoding="utf-8") + "\nOne more line.\n", encoding="utf-8")
        self.assertFalse(plans.is_valid_approval(path.read_text(encoding="utf-8"), "feature/x"))
        code, out = self.run_mcs("approve", "x", answer="x")
        self.assertEqual(code, 0, out)
        self.assertTrue(plans.is_valid_approval(path.read_text(encoding="utf-8"), "feature/x"))

    # status ----------------------------------------------------------------

    def test_status_writes_index(self):
        self.write_plan("a")
        self.run_mcs("approve", "a", answer="a")
        path_b = self.write_plan("b", meta={"status": "approved", "branch": "feature/x",
                                            "approval_hash": "0" * 64})
        self.write_plan("c")
        code, out = self.run_mcs("status")
        self.assertEqual(code, 0)
        index = (self.root / "Docs" / "Plans" / "index.md").read_text(encoding="utf-8")
        self.assertIn("[a](a.md)", index)
        self.assertRegex(index, r"\| \[a\]\(a\.md\) \| approved \|")
        self.assertRegex(index, r"\| \[b\]\(b\.md\) \| changed after approval \|")
        self.assertRegex(index, r"\| \[c\]\(c\.md\) \| draft \|")
        self.assertIn("changed after approval", out)
        self.assertTrue(path_b.exists())

    def test_status_index_ignored_as_plan(self):
        self.run_mcs("status")
        code, _ = self.run_mcs("status")
        index = (self.root / "Docs" / "Plans" / "index.md").read_text(encoding="utf-8")
        self.assertNotIn("[index]", index)
        self.assertEqual(code, 0)

    # check -----------------------------------------------------------------

    def test_check_reports_missing_setup(self):
        code, out = self.run_mcs("check")
        self.assertEqual(code, 1)
        self.assertIn("setup", out)

    def test_check_session_start_never_fails(self):
        code, _ = self.run_mcs("check", "--session-start")
        self.assertEqual(code, 0)

    def test_check_reports_guard_errors(self):
        (self.root / ".mcs-guard.log").write_text("2026-10-12T10:00:00 Traceback boom\n")
        _, out = self.run_mcs("check")
        self.assertIn("guard error", out)

    def test_check_machine_lists_projects(self):
        home = self.root / "home"
        state = home / ".jcode" / "hooks" / "mcs-dispatch.json"
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({"projects": [str(self.root), str(self.root / "gone")]}))
        os.environ["JCODE_HOME"] = str(home / ".jcode")
        try:
            code, out = self.run_mcs("check", "--machine")
        finally:
            del os.environ["JCODE_HOME"]
        self.assertEqual(code, 0)
        self.assertIn(str(self.root), out)
        self.assertIn("gone", out)
        self.assertIn("missing", out)


if __name__ == "__main__":
    unittest.main()
