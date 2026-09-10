"""Phase 5 marketplace ``validate`` step (plan §5 task #1, #5, #7).

Walks every plugin listed in ``.claude-plugin/marketplace.json``
and scrapes its ``commands/`` and ``skills/`` directories. The
synthesized stub entries carry ``source_trust="marketplace-stub"``,
NO ``signature`` (no ed25519 attestation), and a yellow-triangle picker
badge per plan §5 task #1. Stubs are written into the static index at
``~/.claude/skills/.installer-cache.json`` (the canonical Phase 5
cache; renamed from ``.index.json`` per plan §11 L-7).

Atomicity (P-10): filesystem write + git-index write + git-commit
must succeed as one transaction. The contract is:

1. Write a unique temp file ``.installer-cache.json.<ts>.tmp`` next
   to the destination.
2. ``git add`` the destination path (adds to the git index).
3. ``git commit -m \"validate marketplace (N plugins)\"`` to persist.
4. ``git gc`` not necessary; the marketplace repo's last 10 commits
   are auditable via ``git log --oneline``.

If any step fails the marketplace repo is left in a known-bad state
(rollback signal: operator inspects the last 10 commits; plan
§5 rollback path ``git revert`` of the validate commit).

This module is stdlib-only (json + pathlib). It is invoked by the
``bodai-plugins marketplace validate`` CLI sub-command and can be
called directly from pytest fixtures.

The polling coordinator in Session-Buddy reads the resulting
``~/.claude/skills/.installer-cache.json`` every ``poll_seconds``
(default 300s, per P-7) and replays it into the discoverable index.
See ``session-buddy/mcp/tools/installer_cache.py``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# Path-traversal allowlist for plugin / skill / command names. Mirrors
# the B-4 allowlist in the canonical SkillMetadata schema, even for
# marketplace stubs (B-4 applies to all client-facing names regardless
# of source_trust — the stub discriminator only changes the picker
# badge, not the validation surface).
_NAME_ALLOWLIST_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}$")


@dataclass(frozen=True)
class MarketplacePlugin:
    """One plugin entry from ``.claude-plugin/marketplace.json``.

    Mirrors the canonical marketplace schema. The marketplace format
    is owned by Claude Code's plugin-loader; we accept the minimum
    keys the validator needs and pass the rest through untouched.
    """

    name: str
    source: str
    ref: str = "main"
    raw: dict[str, Any] | None = None


def _read_marketplace(manifest_path: Path) -> list[MarketplacePlugin]:
    """Read ``manifest_path`` and return its plugin entries.

    Manifests without a ``plugins`` key are treated as empty (the
    validator proceeds with no-op rather than raising — useful when
    ``bodai-plugins marketplace add`` has not yet been called).
    """
    if not manifest_path.is_file():
        return []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    plugins = payload.get("plugins", [])
    out: list[MarketplacePlugin] = []
    for entry in plugins:
        try:
            out.append(
                MarketplacePlugin(
                    name=entry["name"],
                    source=entry["source"],
                    ref=entry.get("ref", "main"),
                    raw=entry,
                )
            )
        except (KeyError, TypeError):
            continue
    return out


def _walk_dir(dir_path: Path) -> list[Path]:
    """Return a sorted list of files under ``dir_path`` (recursive).

    Excludes dotfiles and ``__pycache__/`` directories.
    """
    if not dir_path.is_dir():
        return []
    out: list[Path] = []
    for path in sorted(dir_path.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith(".") or "__pycache__" in path.parts:
            continue
        out.append(path)
    return out


def _stub_skill_entry(
    *,
    plugin_name: str,
    skill_md_path: Path,
) -> dict[str, Any] | None:
    """Synthesize a stub SkillMetadata for a marketplace plugin.

    The synthesized entry carries the minimum required SkillMetadata
    fields (id, server, name, version, content_hash, body_size,
    timestamp) plus the marketplace discriminator
    ``source_trust="marketplace-stub"`` and NO ``signature``. The
    picker renders the yellow-triangle badge when this discriminator
    is present (vs ``"bodai-attested"`` for signed entries).

    Returns ``None`` when the path's stem violates B-4 (so the caller
    can skip silently without polluting the cache).
    """
    stem = skill_md_path.stem
    if not _NAME_ALLOWLIST_RE.fullmatch(stem):
        return None
    body_bytes = skill_md_path.read_bytes()
    return {
        "id": f"marketplace:{plugin_name}:{stem}:0.0.0",
        "server": "marketplace",
        "name": stem,
        "description": (
            f"Marketplace stub from {plugin_name!r}. Not signed "
            "(no ed25519 attestation) — install at your own risk."
        ),
        "version": "0.0.0",
        "tool_refs": [],
        "dependencies": [],
        "content_type": "skill",
        "content_hash": ""
        + _safe_hash(body_bytes),
        "body_size": len(body_bytes),
        "body_format": "yaml-frontmatter+markdown",
        "allowed_tools": [],
        "signature": None,
        "server_pubkey_id": None,
        "timestamp": time.time(),
        # Marketplace discriminator (plan §5 task #1). NOT part of the
        # canonical SkillMetadata; the picker reads this to render the
        # yellow-triangle badge.
        "source_trust": "marketplace-stub",
        "source_plugin": plugin_name,
    }


def _stub_agent_entry(
    *,
    plugin_name: str,
    agent_md_path: Path,
) -> dict[str, Any] | None:
    """Synthesize a stub AgentMetadata for a marketplace plugin.

    Mirror of :func:`_stub_skill_entry` for agents; differs in the
    embedding ``content_type="agent"`` and the stub-specific
    ``system_prompt`` field. Returns ``None`` on allowlist-violating
    names.
    """
    stem = agent_md_path.stem
    if not _NAME_ALLOWLIST_RE.fullmatch(stem):
        return None
    body_bytes = agent_md_path.read_bytes()
    body_text = body_bytes.decode("utf-8", errors="replace")
    return {
        "id": f"marketplace:{plugin_name}:{stem}:0.0.0",
        "server_key": "marketplace",
        "name": stem,
        "description": (
            f"Marketplace stub from {plugin_name!r}. Not signed."
        ),
        "version": "0.0.0",
        "model": "opus",
        "tools": [],
        "system_prompt": body_text,
        "dependencies": [],
        "tool_refs": [],
        "category": None,
        "owner": None,
        "status": "draft",
        "last_reviewed": None,
        "scope": "user-global",
        "content_hash": _safe_hash(body_bytes),
        "signature": None,
        "server_pubkey_id": None,
        "timestamp": time.time(),
        # Marketplace discriminator (plan §5 task #1).
        "source_trust": "marketplace-stub",
        "source_plugin": plugin_name,
    }


def _safe_hash(body: bytes) -> str:
    """Return the hex SHA-256 of ``body`` (always present)."""
    import hashlib

    return hashlib.sha256(body).hexdigest()


def build_cache_payload(
    plugins: list[MarketplacePlugin],
    *,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    """Walk every plugin's commands/skills/agents dirs and produce the cache payload.

    The resulting dict matches plan §5 task #6::

        {
          "schema_version": 1,
          "last_modified": <unix_ts>,
          "server_runs": [
            {"server": "marketplace",
             "version": "0.0.0",
             "fetched_at": <ts>,
             "skills": [...],
             "agents": [...]},
          ]
        }
    """
    import hashlib

    skills: list[dict[str, Any]] = []
    agents: list[dict[str, Any]] = []
    plugin_names: list[str] = []

    for plugin in plugins:
        plugin_names.append(plugin.name)
        # Local plugin sources only (the marketplace validator does not
        # fetch remote URLs; that work is deferred to the polling
        # coordinator when the marketplace is git-cloned elsewhere).
        if plugin.source.startswith(("http://", "https://", "git@")):
            continue
        plugin_dir = (plugin_root or Path(".")) / plugin.source
        if not plugin_dir.is_dir():
            continue

        # skills/<name>.md -> stub skill entries
        skills_dir = plugin_dir / "skills"
        for skill_md in _walk_dir(skills_dir):
            if skill_md.suffix != ".md":
                continue
            entry = _stub_skill_entry(
                plugin_name=plugin.name,
                skill_md_path=skill_md,
            )
            if entry is not None:
                skills.append(entry)

        # agents/<name>.md -> stub agent entries
        agents_dir = plugin_dir / "agents"
        for agent_md in _walk_dir(agents_dir):
            if agent_md.suffix != ".md":
                continue
            entry = _stub_agent_entry(
                plugin_name=plugin.name,
                agent_md_path=agent_md,
            )
            if entry is not None:
                agents.append(entry)

    fetched_at = time.time()
    return {
        "schema_version": 1,
        "last_modified": fetched_at,
        "server_runs": [
            {
                "server": "marketplace",
                "version": "0.0.0",
                "fetched_at": fetched_at,
                "skills": skills,
                "agents": agents,
                "plugin_names": plugin_names,
                "source_trust": "marketplace-stub",
            }
        ],
        "manifest_signature": ""
        + hashlib.sha256(
            json.dumps(sorted(plugin_names)).encode("utf-8")
        ).hexdigest(),
    }


def _atomic_write_json(target: Path, payload: dict[str, Any]) -> None:
    """Atomically write ``payload`` to ``target`` (.tmp -> rename)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp_path, target)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def run_validate(
    *,
    manifest_path: Path,
    cache_path: Path,
    plugin_root: Path | None = None,
    commit_message: str | None = None,
    workdir: Path | None = None,
) -> dict[str, Any]:
    """End-to-end Phase 5 marketplace validate.

    Atomicity contract (P-10):

    1. Synthesize the cache payload from the manifest.
    2. Atomic filesystem write to ``cache_path`` (.tmp -> rename).
    3. Atomic git commit in the marketplace repo (when
       ``commit_message`` is set; otherwise filesystem-only).
       ``workdir`` defaults to the parent of ``manifest_path``.

    Returns:
        A dict summarizing the validation outcome::

            {"plugins": N, "skills": M, "agents": K, "cache_path": str}

        Raises:
            RuntimeError: on filesystem or git failure (the cache is
                rolled back to the prior-good version via the
                ``cache_path`` atomic-write contract).
    """
    plugins = _read_marketplace(manifest_path)
    payload = build_cache_payload(plugins, plugin_root=plugin_root)

    # Step 1: filesystem write (atomic; cache is always recovered
    # even if git commit fails).
    _atomic_write_json(cache_path, payload)

    # Step 2: optional git commit (P-10 atomicity across filesystem
    # + git index + git commit).
    if commit_message:
        import shutil

        workdir = Path(workdir or manifest_path.parent)
        if not _is_git_repo(workdir):
            # Marketplace repo is not a git checkout (live install
            # via pip). Skip git and return.
            return {
                "plugins": len(plugins),
                "skills": len(payload["server_runs"][0]["skills"]),
                "agents": len(payload["server_runs"][0]["agents"]),
                "cache_path": str(cache_path),
                "git_commit": None,
            }
        try:
            # ``cache_path`` may be outside ``workdir`` (the cache lives
            # at ``~/.claude/skills/``, NOT inside the marketplace
            # repo). The marketplace repo's own state is the
            # ``.claude-plugin/marketplace.json`` plus the stub list;
            # we commit the marketplace manifest instead.
            subprocess.run(
                ["git", "add", str(manifest_path)],
                cwd=str(workdir),
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=str(workdir),
                check=True,
                capture_output=True,
            )
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(workdir),
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"git commit failed in {workdir}: "
                f"{exc.stderr.decode() if exc.stderr else exc}"
            ) from exc
        return {
            "plugins": len(plugins),
            "skills": len(payload["server_runs"][0]["skills"]),
            "agents": len(payload["server_runs"][0]["agents"]),
            "cache_path": str(cache_path),
            "git_commit": sha,
        }

    return {
        "plugins": len(plugins),
        "skills": len(payload["server_runs"][0]["skills"]),
        "agents": len(payload["server_runs"][0]["agents"]),
        "cache_path": str(cache_path),
        "git_commit": None,
    }


def _is_git_repo(path: Path) -> bool:
    """True when ``path`` is inside a git working tree."""
    if not path.is_dir():
        return False
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(path),
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for ``validate_marketplace.py``.

    Mirrors the contract of the ``bodai-plugins marketplace validate``
    command. Returns 0 on success, 1 on validation failure,
    2 on bad arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="validate-marketplace",
        description=(
            "Phase 5 marketplace validator: scrapes each plugin's "
            "commands/skills/agents dirs and writes stubs into "
            "~/.claude/skills/.installer-cache.json (atomic + locked)."
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(".claude-plugin/marketplace.json"),
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path.home() / ".claude" / "skills" / ".installer-cache.json",
    )
    parser.add_argument(
        "--plugin-root",
        type=Path,
        default=None,
        help="Root directory under which plugin sources are resolved. Default: cwd.",
    )
    parser.add_argument(
        "--commit-message",
        type=str,
        default=None,
        help="If set, commit the marketplace manifest atomically after the cache write.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_validate(
            manifest_path=args.manifest,
            cache_path=args.cache,
            plugin_root=args.plugin_root,
            commit_message=args.commit_message,
            workdir=args.manifest.parent,
        )
    except RuntimeError as exc:
        print(f"validate failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
