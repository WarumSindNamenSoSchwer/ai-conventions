#!/usr/bin/env bash
# End-to-end test for setup/uninstall with two projects (macOS, Linux).
# Uses a throwaway JCODE_HOME and HOME; never touches the real ones.
# Usage: test/e2e_setup.sh   (from the ai-conventions checkout, committed state)
set -eu
src="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d)"
export HOME="$work/home" JCODE_HOME="$work/home/.jcode" MCS_NO_PLUGINS=1
unset JCODE_SESSION_ID CLAUDE_CODE_SESSION_ID CLAUDECODE || true
mkdir -p "$JCODE_HOME" "$work/bin"
fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok   $*"; }

# A foreign pre_tool hook that exists before setup and must keep working.
cat > "$work/bin/foreign-hook" <<'EOF'
#!/bin/sh
input=$(cat)
case "$input" in *FOREIGN-MARKER*) echo "blocked by foreign hook" >&2; exit 2;; esac
exit 0
EOF
chmod +x "$work/bin/foreign-hook"
cat > "$JCODE_HOME/config.toml" <<EOF
# user config
default_provider = "claude"

[hooks]
pre_tool = "$work/bin/foreign-hook"  # keep me
pre_tool_timeout_ms = 5000

[ambient]
enabled = false
EOF
cp "$JCODE_HOME/config.toml" "$work/config.before"

git config --global user.name "E2E Test" 2>/dev/null || true
git config --global user.email "e2e@example.com"
git config --global protocol.file.allow always

make_project() {
    local p="$work/$1"
    git init -q -b main "$p"
    printf '# Project %s\n\nOwn instructions stay.\n' "$1" > "$p/CLAUDE.md"
    git -C "$p" add -A && git -C "$p" commit -q -m init
    git -C "$p" submodule add -q "$src" .mcs
    git -C "$p" commit -q -m "add .mcs"
    git init -q --bare "$work/$1.remote.git"
    git -C "$p" remote add origin "$work/$1.remote.git"
    git -C "$p" push -q -u origin main
    (cd "$p" && .mcs/setup.sh >/dev/null) || fail "setup $1"
    echo "$p"
}

guard() { # project tool json -> exit code
    printf '%s' "$3" | JCODE_HOOK_TOOL_NAME="$2" JCODE_HOOK_CWD="$1" \
        python3 "$JCODE_HOME/hooks/mcs-dispatch.py" 2>/dev/null && echo 0 || echo $?
}

a="$(make_project a)"; b="$(make_project b)"
ok "setup in two projects"

# --- what setup wrote
grep -q '@.mcs/AGENTS.md' "$a/CLAUDE.md" || fail "CLAUDE.md import"
grep -q 'Own instructions stay.' "$a/CLAUDE.md" || fail "CLAUDE.md own content kept"
grep -q 'Hard rules' "$a/.jcode/prompt-overlay.md" || fail "jcode overlay"
[ -f "$a/.jcode/skills/mcs-plan/SKILL.md" ] || fail "jcode skill copy"
grep -qx 'Docs/Plans/\*.md text eol=lf' "$a/.gitattributes" || fail ".gitattributes"
python3 - "$a/.claude/settings.json" <<'EOF' || fail "settings.json content"
import json, sys
s = json.load(open(sys.argv[1]))
assert s["extraKnownMarketplaces"]["mcs"]["source"] == {"source": "directory", "path": ".mcs"}
assert s["enabledPlugins"]["mcs@mcs"] and s["enabledPlugins"]["superpowers@mcs"]
assert "hookify@mcs" not in s["enabledPlugins"]
assert "Bash(gh pr merge *)" in s["permissions"]["deny"]
assert s["env"]["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] == "70"
assert "guard.py" in s["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
EOF
grep -q 'mcs-dispatch.py' "$JCODE_HOME/config.toml" || fail "dispatcher in config.toml"
[ "$(grep -c '^pre_tool = ' "$JCODE_HOME/config.toml")" = 1 ] || fail "exactly one pre_tool line"
ok "project files and machine dispatcher written"

# --- idempotent
(cd "$a" && .mcs/setup.sh >/dev/null)
cp -R "$a" "$work/a.copy"
(cd "$a" && .mcs/setup.sh >/dev/null)
diff -r -x .git "$a" "$work/a.copy" >/dev/null || fail "setup not idempotent"
(cd "$a" && .mcs/bin/mcs check >/dev/null) || fail "mcs check after setup"
python3 - "$a/.claude/settings.json" <<'EOF'
import json, sys
p = sys.argv[1]; s = json.load(open(p))
s["permissions"]["deny"].remove("Bash(gh pr merge *)")
open(p, "w").write(json.dumps(s, indent=2) + "\n")
EOF
(cd "$a" && .mcs/bin/mcs check >/dev/null) && fail "mcs check missed a removed deny rule"
(cd "$a" && .mcs/setup.sh >/dev/null && .mcs/bin/mcs check >/dev/null) || fail "setup did not restore deny rule"
ok "setup idempotent, mcs check clean"

# --- guard through the installed dispatcher, both projects
for p in "$a" "$b"; do
    [ "$(guard "$p" bash '{"command":"git push origin main"}')" = 2 ] || fail "push main not blocked in $p"
    [ "$(guard "$p" bash '{"command":"git push"}')" = 2 ] || fail "bare push on main not blocked in $p"
    [ "$(guard "$p" bash '{"command":"./Scripts/flash.sh"}')" = 2 ] || fail "flash not blocked in $p"
    [ "$(guard "$p" write '{"file_path":"src/a.c","content":"x"}')" = 2 ] || fail "code edit without plan in $p"
    [ "$(guard "$p" bash '{"command":"ls"}')" = 0 ] || fail "ls blocked in $p"
done
[ "$(guard "$a" bash '{"command":"echo FOREIGN-MARKER"}')" = 2 ] || fail "foreign hook not chained"
[ "$(guard "$work" bash '{"command":"git push origin main"}')" = 0 ] || fail "non-MCS dir blocked"
ok "guard blocks in both projects, foreign hook chained, non-MCS dirs allowed"

# --- Claude Code hook command as configured
cmd=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['hooks']['PreToolUse'][0]['hooks'][0]['command'])" "$a/.claude/settings.json")
out=$(printf '{"tool_name":"Bash","tool_input":{"command":"git push origin main"},"cwd":"%s"}' "$a" \
    | CLAUDE_PROJECT_DIR="$a" sh -c "$(echo "$cmd" | sed "s|\${CLAUDE_PROJECT_DIR}|$a|g")")
echo "$out" | grep -q '"permissionDecision": "deny"' || fail "claude hook command: $out"
ok "Claude Code hook command denies push to main"

# --- plan flow: approve as a human, then code edits pass
git -C "$a" checkout -q -b feature/x
cat > "$a/Docs/Plans/x.md" <<'EOF'
# Plan x

## Brainstorming
b

## Existing code (improve)
e

## Simplification (ponytail)
s

## Architecture (archify)
Single component, no diagram: test.

## Quality review (thermo-nuclear)
q
EOF
(cd "$a" && echo x | .mcs/bin/mcs approve x >/dev/null) || fail "approve"
[ "$(guard "$a" write '{"file_path":"src/a.c","content":"x"}')" = 0 ] || fail "edit with approved plan"
[ "$(guard "$a" bash '{"command":".mcs/bin/mcs approve x"}')" = 2 ] || fail "agent approve not blocked"
ok "approve by human enables edits, agent approve blocked"

# --- uninstall a: dispatcher stays for b
git -C "$a" checkout -q main
git -C "$a" stash -q -u 2>/dev/null || true
(cd "$a" && .mcs/uninstall.sh >/dev/null) || fail "uninstall a"
grep -q 'mcs-dispatch.py' "$JCODE_HOME/config.toml" || fail "dispatcher removed while b uses it"
[ "$(guard "$b" bash '{"command":"git push origin main"}')" = 2 ] || fail "b lost guard"
[ -z "$(git -C "$a" status --porcelain)" ] || { git -C "$a" status --porcelain; fail "a not clean after uninstall"; }
grep -q 'Own instructions stay.' "$a/CLAUDE.md" || fail "a own CLAUDE.md content lost"
ok "uninstall a: project clean, dispatcher kept for b"

# --- uninstall b: dispatcher removed, config.toml byte-identical
(cd "$b" && .mcs/uninstall.sh >/dev/null) || fail "uninstall b"
cmp "$JCODE_HOME/config.toml" "$work/config.before" || { diff "$work/config.before" "$JCODE_HOME/config.toml"; fail "config.toml differs"; }
[ ! -e "$JCODE_HOME/hooks/mcs-dispatch.py" ] || fail "dispatcher file left"
[ -z "$(git -C "$b" status --porcelain)" ] || { git -C "$b" status --porcelain; fail "b not clean after uninstall"; }
ok "uninstall b: dispatcher removed, config.toml identical, project clean"

# --- fresh machine: no config.toml before setup
rm -f "$JCODE_HOME/config.toml"
(cd "$b" && .mcs/setup.sh >/dev/null && .mcs/uninstall.sh >/dev/null)
[ ! -e "$JCODE_HOME/config.toml" ] || { cat "$JCODE_HOME/config.toml"; fail "config.toml created and left behind"; }
[ -z "$(git -C "$b" status --porcelain)" ] || fail "b not clean after second round"
ok "fresh machine: setup + uninstall leave no config.toml"

# --- Claude Code plugins at project scope (needs the claude CLI, network)
if command -v claude >/dev/null 2>&1 && [ "${E2E_PLUGINS:-1}" = 1 ]; then
    unset MCS_NO_PLUGINS
    (cd "$b" && .mcs/setup.sh >/dev/null) || fail "setup with plugins"
    n=$(cd "$b" && claude plugin list 2>/dev/null | grep -c '@mcs')
    [ "$n" = 12 ] || fail "expected 12 enabled-by-default plugins, got $n"
    [ ! -e "$HOME/.claude/settings.json" ] || ! grep -q '@mcs' "$HOME/.claude/settings.json" || fail "user settings touched"
    (cd "$b" && .mcs/uninstall.sh >/dev/null) || fail "uninstall with plugins"
    n=$(cd "$b" && claude plugin list 2>/dev/null | grep -c '@mcs' || true)
    [ "$n" = 0 ] || fail "$n plugins left after uninstall"
    [ -z "$(git -C "$b" status --porcelain)" ] || fail "b not clean after plugin round"
    ok "Claude Code: 12 plugins installed at project scope, user settings untouched, uninstall removes them"
else
    echo "skip Claude Code plugin step (no claude CLI or E2E_PLUGINS=0)"
fi

echo "ALL PASSED ($work)"
