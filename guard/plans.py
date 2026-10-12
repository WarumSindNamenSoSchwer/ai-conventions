"""Plan files: parsing, mandatory sections, approval hash.

Shared by guard.py (is there an approved plan for this branch?) and bin/mcs
(approve, status). Standard library only.
"""

import hashlib
import re
from pathlib import Path

MANDATORY_SECTIONS = (
    "## Brainstorming",
    "## Existing code (improve)",
    "## Simplification (ponytail)",
    "## Architecture (archify)",
    "## Quality review (thermo-nuclear)",
)
NO_DIAGRAM_MARKER = "Single component, no diagram:"
APPROVAL_KEYS = ("status", "approved_by", "approved_at", "branch", "approval_hash")


def normalize(text):
    """LF line endings, no trailing whitespace. Makes the hash platform-neutral."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n")).strip("\n") + "\n"


def split_front_matter(text):
    """Return (front_matter_dict, body) for a '---' delimited header."""
    text = normalize(text)
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    header = text[4:end]
    body = text[end + 5:]
    meta = {}
    for line in header.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, body


def join_front_matter(meta, body):
    lines = [f"{k}: {v}" for k, v in meta.items()]
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def body_hash(text):
    _, body = split_front_matter(text)
    return hashlib.sha256(normalize(body).encode("utf-8")).hexdigest()


def section_bodies(body):
    """Map '## Heading' -> text until the next '## ' heading."""
    result = {}
    current = None
    for line in body.split("\n"):
        if line.startswith("## "):
            current = line.strip()
            result[current] = []
        elif current is not None:
            result[current].append(line)
    return {k: "\n".join(v).strip() for k, v in result.items()}


def missing_sections(text, plan_path=None):
    """Return a list of problems that prevent approval. Empty list = ok."""
    _, body = split_front_matter(text)
    sections = section_bodies(body)
    problems = []
    for name in MANDATORY_SECTIONS:
        if name not in sections:
            problems.append(f"missing section '{name}'")
        elif not sections[name]:
            problems.append(f"empty section '{name}'")
    arch = sections.get("## Architecture (archify)", "")
    if arch and NO_DIAGRAM_MARKER not in arch:
        links = re.findall(r"\(([^)\s]+\.html)\)", arch)
        if not links:
            problems.append("archify section links no .html diagram and has no "
                            f"'{NO_DIAGRAM_MARKER}' reason")
        elif plan_path is not None:
            for link in links:
                if not (Path(plan_path).parent / link).exists():
                    problems.append(f"archify diagram not found: {link}")
    return problems


def approve_text(text, approver, branch, when):
    meta, body = split_front_matter(text)
    meta["status"] = "approved"
    meta["approved_by"] = approver
    meta["approved_at"] = when
    meta["branch"] = branch
    meta["approval_hash"] = hashlib.sha256(normalize(body).encode("utf-8")).hexdigest()
    return join_front_matter(meta, body)


def is_valid_approval(text, branch):
    meta, _ = split_front_matter(text)
    return (
        meta.get("status") == "approved"
        and meta.get("branch") == branch
        and meta.get("approval_hash") == body_hash(text)
    )


def plans_dir(root):
    return Path(root) / "Docs" / "Plans"


def list_plans(root):
    d = plans_dir(root)
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("*.md") if p.name.lower() != "index.md")


def approved_plan_for(root, branch):
    for path in list_plans(root):
        try:
            if is_valid_approval(path.read_text(encoding="utf-8", errors="replace"), branch):
                return path
        except OSError:
            continue
    return None
