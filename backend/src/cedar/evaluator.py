"""
Kalaa Setu — Cedar-compatible policy evaluator.

Why this exists
---------------
BRAIN.md and the task file require that Cedar policies be the source of truth
for the two MUST rules and two SHOULD rules — not duplicated app-code ifs.
The real Cedar engine ships as a Rust binary / library. For a hackathon demo
on LocalStack with no external runtime, we implement the exact same semantics
in Python, load the same .cedar files, and log which policy files were loaded.

If the real Cedar engine becomes available, only this file changes — every
handler that calls is_authorized() keeps working unchanged.

Semantics implemented (matching Cedar):
  - Default deny.
  - Any matching `forbid` overrides any matching `permit`.
  - A policy "matches" when principal type, action, resource type, and its
    `when` conditions all evaluate to true.

CEDAR_MODE:
  - "mock" (default): use this Python evaluator
  - "engine":      call out to a real Cedar engine (stub; raises if not present)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("kalaa.cedar")
log.setLevel(logging.INFO)
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[cedar] %(levelname)s %(message)s"))
    log.addHandler(_h)


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------

@dataclass
class Request:
    principal_type: str           # e.g. "Seller", "Buyer", "TouchpointAdmin"
    principal_attrs: dict         # e.g. {"seller_id": "...", "touchpoint_id": "..."}
    action: str                   # e.g. "editListing"
    resource_type: str            # e.g. "Listing", "Contribution", "LedgerEntry"
    resource_attrs: dict = field(default_factory=dict)  # e.g. {"seller_id": "..."}


# ---------------------------------------------------------------------------
# Loaded policy representation
# ---------------------------------------------------------------------------

@dataclass
class Decision:
    allowed: bool
    policy_file: str | None = None
    reason: str | None = None


@dataclass
class LoadedPolicy:
    source_file: str
    effect: str                   # "permit" or "forbid"
    principal_type: str
    actions: list[str]            # actions this policy applies to
    resource_type: str
    condition_text: str           # raw text of the `when { ... }` block


_LOADED: list[LoadedPolicy] = []
_LOADED_FILES: list[str] = []


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _policy_path() -> str:
    return os.environ.get("CEDAR_POLICY_PATH", "./policies")


def _cedar_mode() -> str:
    return os.environ.get("CEDAR_MODE", "mock").lower()


def load_policies(path: str | None = None) -> None:
    """
    Load all .cedar files from the policy path into memory.

    This implementation does not re-parse Cedar's grammar in full; it extracts
    the effect, principal type, actions, resource type, and the raw `when`
    text so the evaluator can apply the same conditions.
    """
    global _LOADED, _LOADED_FILES
    _LOADED = []
    _LOADED_FILES = []

    root = path or _policy_path()
    if not os.path.isdir(root):
        log.warning("CEDAR_POLICY_PATH %s does not exist; no policies loaded", root)
        return

    for name in sorted(os.listdir(root)):
        if not name.endswith(".cedar"):
            continue
        full = os.path.join(root, name)
        with open(full, "r", encoding="utf-8") as f:
            text = f.read()
        _LOADED.extend(_parse_policies(text, source_file=full))
        _LOADED_FILES.append(full)

    log.info("loaded %d policy file(s): %s", len(_LOADED_FILES), ", ".join(_LOADED_FILES))
    for p in _LOADED:
        log.info("  policy from %s: %s %s on %s", p.source_file, p.effect, p.actions, p.resource_type)


def loaded_files() -> list[str]:
    return list(_LOADED_FILES)


def loaded_policy_count() -> int:
    return len(_LOADED)


def _parse_policies(text: str, source_file: str) -> list[LoadedPolicy]:
    """
    Extract permit/forbid blocks from a .cedar file.
    Intentionally simple: finds `permit (` or `forbid (` and reads the
    head block, action list, resource type, and the trailing `when { ... }`.
    """
    policies: list[LoadedPolicy] = []
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        effect = None
        if line.startswith("permit"):
            effect = "permit"
        elif line.startswith("forbid"):
            effect = "forbid"

        if effect is None:
            i += 1
            continue

        # Collect the whole block up to the terminating `;`
        block_lines: list[str] = []
        while i < n:
            block_lines.append(lines[i])
            if lines[i].strip().endswith(";"):
                i += 1
                break
            i += 1

        block = "\n".join(block_lines)
        principal_type = _extract_principal_type(block)
        actions = _extract_actions(block)
        resource_type = _extract_resource_type(block)
        condition_text = _extract_when(block)

        if principal_type and actions and resource_type:
            policies.append(
                LoadedPolicy(
                    source_file=source_file,
                    effect=effect,
                    principal_type=principal_type,
                    actions=actions,
                    resource_type=resource_type,
                    condition_text=condition_text,
                )
            )
    return policies


def _extract_principal_type(block: str) -> str | None:
    for raw in block.splitlines():
        s = raw.strip()
        if s.startswith("principal is "):
            return s[len("principal is "):].rstrip(", ")
    return None


def _extract_actions(block: str) -> list[str]:
    """
    Handles both:
        action == Action::"editListing"
        action in [ Action::"a", Action::"b" ]
    """
    actions: list[str] = []
    for raw in block.splitlines():
        s = raw.strip()
        if s.startswith("action == "):
            a = _action_from_literal(s[len("action == "):].rstrip(",; "))
            if a:
                actions.append(a)
        elif s.startswith("action in ["):
            # Gather the bracket list, possibly spanning one line
            inner = s[len("action in ["):].rstrip("], ")
            for piece in inner.split(","):
                a = _action_from_literal(piece.strip())
                if a:
                    actions.append(a)
    return actions


def _action_from_literal(text: str) -> str | None:
    text = text.strip().rstrip(",;").strip()
    marker = 'Action::"'
    if marker in text:
        start = text.index(marker) + len(marker)
        end = text.index('"', start)
        return text[start:end]
    return None


def _extract_resource_type(block: str) -> str | None:
    for raw in block.splitlines():
        s = raw.strip()
        if s.startswith("resource is "):
            return s[len("resource is "):].rstrip(", ")
    return None


def _extract_when(block: str) -> str:
    marker = "when {"
    idx = block.find(marker)
    if idx == -1:
        return ""
    rest = block[idx + len(marker):]
    end = rest.rfind("}")
    if end == -1:
        return rest.strip()
    return rest[:end].strip()


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _match_condition(condition_text: str, req: Request) -> bool:
    """
    Evaluate a Cedar `when { ... }` condition against a request.
    Supports the exact subset used in this project's policies:
      - principal.<attr> == resource.<attr>
      - principal.<attr> != resource.<attr>
      - resource.<attr> == true / false
      - resource.<attr> < N   /   > N   (numeric)
      - resource.<attr> < N || resource.<attr> > N
    """
    if not condition_text:
        # No `when` clause → condition is trivially true.
        return True

    # Flatten to single-line to simplify matching
    text = " ".join(condition_text.split())

    # OR of two simple comparisons (used in the percentage bounds check)
    if "||" in text:
        parts = [p.strip() for p in text.split("||")]
        return any(_match_simple(p, req) for p in parts)

    return _match_simple(text, req)


def _match_simple(expr: str, req: Request) -> bool:
    expr = expr.strip().rstrip(";").strip()

    for op in ("==", "!=", "<=", ">=", "<", ">"):
        if op in expr:
            left, right = expr.split(op, 1)
            return _compare(op, left.strip(), right.strip(), req)
    return False


def _resolve(token: str, req: Request) -> Any:
    token = token.strip()
    if token == "true":
        return True
    if token == "false":
        return False
    if token.startswith("principal."):
        return req.principal_attrs.get(token[len("principal."):])
    if token.startswith("resource."):
        return req.resource_attrs.get(token[len("resource."):])
    try:
        if "." in token:
            return float(token)
        return int(token)
    except ValueError:
        return token


def _compare(op: str, left: str, right: str, req: Request) -> bool:
    lv = _resolve(left, req)
    rv = _resolve(right, req)

    try:
        if op == "==":
            return lv == rv
        if op == "!=":
            return lv != rv
        if op == "<":
            return lv is not None and rv is not None and lv < rv
        if op == ">":
            return lv is not None and rv is not None and lv > rv
        if op == "<=":
            return lv is not None and rv is not None and lv <= rv
        if op == ">=":
            return lv is not None and rv is not None and lv >= rv
    except TypeError:
        return False
    return False


def authorize(req: Request) -> Decision:
    """Return the Cedar decision plus the matching policy/reason for diagnostics."""
    if _cedar_mode() == "engine":
        raise RuntimeError(
            "CEDAR_MODE=engine requested but no Cedar engine binary is wired in. "
            "Set CEDAR_MODE=mock or integrate the real engine here."
        )
    if not _LOADED:
        log.warning("authorize called with no policies loaded — denying")
        return Decision(False, reason="no policies loaded")

    matched_permit = None
    for policy in _LOADED:
        if not _policy_applies(policy, req) or not _match_condition(policy.condition_text, req):
            continue
        if policy.effect == "forbid":
            reason = "matching forbid policy"
            log.info("DENY by %s on %s.%s (policy %s)", policy.effect, req.resource_type, req.action, os.path.basename(policy.source_file))
            return Decision(False, os.path.basename(policy.source_file), reason)
        if matched_permit is None:
            matched_permit = policy

    if matched_permit:
        log.info("ALLOW %s.%s (policy %s)", req.resource_type, req.action, os.path.basename(matched_permit.source_file))
        return Decision(True, os.path.basename(matched_permit.source_file), "matching permit policy")

    log.info("DENY %s.%s (no permit matched)", req.resource_type, req.action)
    return Decision(False, reason="no permit policy matched")


def is_authorized(req: Request) -> bool:
    """Backward-compatible bool-only Cedar decision API."""
    return authorize(req).allowed


def _policy_applies(p: LoadedPolicy, req: Request) -> bool:
    if p.principal_type != req.principal_type:
        return False
    if p.resource_type != req.resource_type:
        return False
    if p.actions and req.action not in p.actions:
        return False
    return True


def _is_authorized_engine(req: Request) -> bool:
    """Placeholder for calling the real Cedar engine. Not wired in this demo."""
    raise RuntimeError(
        "CEDAR_MODE=engine requested but no Cedar engine binary is wired in. "
        "Set CEDAR_MODE=mock or integrate the real engine here."
    )
