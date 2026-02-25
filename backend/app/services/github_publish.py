from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from urllib import error, request

from app.core.config import settings


class GitHubPublishError(RuntimeError):
    pass


@dataclass
class GitHubFileChange:
    path: str
    content: str
    encoding: str = "utf-8"


@dataclass
class GitHubPublishResult:
    repo: str
    branch: str
    commit_sha: str
    release_workflow_triggered: bool
    backend_workflow_triggered: bool


def _required_setting(name: str, value: str) -> str:
    trimmed = (value or "").strip()
    if not trimmed:
        raise GitHubPublishError(f"Missing required setting: {name}")
    return trimmed


def _repo_slug() -> str:
    owner = _required_setting("github_repo_owner", settings.github_repo_owner)
    repo = _required_setting("github_repo_name", settings.github_repo_name)
    return f"{owner}/{repo}"


def _branch_name(override: str | None = None) -> str:
    return (override or settings.github_default_branch or "main").strip() or "main"


def _token() -> str:
    return _required_setting("github_token", settings.github_token)


def _validate_repo_path(path: str) -> str:
    normalized = (path or "").strip().replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    if not normalized or normalized.startswith("/") or normalized.startswith(".") or ".." in normalized.split("/"):
        raise GitHubPublishError(f"Invalid repository path: {path}")
    return normalized


def _decode_change_content(change: GitHubFileChange) -> bytes:
    if change.encoding == "base64":
        try:
            return base64.b64decode(change.content.encode("ascii"), validate=True)
        except Exception as exc:  # pragma: no cover - exact decoder exception type not important
            raise GitHubPublishError(f"Invalid base64 content for {change.path}") from exc
    return (change.content or "").encode("utf-8")


def _api_request(method: str, path: str, payload: dict | None = None, expected_statuses: set[int] | None = None) -> dict:
    token = _token()
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(
        f"https://api.github.com{path}",
        method=method,
        data=body,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "karaxas-backend",
        },
    )
    try:
        with request.urlopen(req, timeout=35) as resp:
            if expected_statuses and resp.status not in expected_statuses:
                raise GitHubPublishError(f"GitHub API status {resp.status} for {path}")
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        raise GitHubPublishError(f"GitHub API error {exc.code} for {path}: {raw}") from exc
    except error.URLError as exc:
        raise GitHubPublishError(f"GitHub API network error for {path}: {exc.reason}") from exc


def _create_blob(repo: str, content: bytes) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    response = _api_request(
        "POST",
        f"/repos/{repo}/git/blobs",
        payload={"content": encoded, "encoding": "base64"},
        expected_statuses={201},
    )
    sha = str(response.get("sha", "")).strip()
    if not sha:
        raise GitHubPublishError("GitHub blob creation did not return sha.")
    return sha


def _trigger_workflow(repo: str, workflow: str, ref: str, inputs: dict[str, str]) -> bool:
    if not workflow.strip():
        return False
    _api_request(
        "POST",
        f"/repos/{repo}/actions/workflows/{workflow}/dispatches",
        payload={"ref": ref, "inputs": inputs},
        expected_statuses={204},
    )
    return True


def publish_changes_and_dispatch(
    *,
    commit_message: str,
    file_changes: list[GitHubFileChange],
    trigger_release_workflow: bool,
    trigger_backend_workflow: bool,
    workflow_ref: str | None = None,
    workflow_inputs: dict[str, str] | None = None,
) -> GitHubPublishResult:
    if not settings.github_publish_enabled:
        raise GitHubPublishError("GitHub publish flow is disabled.")
    if not file_changes:
        raise GitHubPublishError("No file changes provided.")

    repo = _repo_slug()
    branch = _branch_name(workflow_ref)
    ref_path = f"/repos/{repo}/git/ref/heads/{branch}"
    ref_response = _api_request("GET", ref_path, expected_statuses={200})
    head_sha = str(ref_response.get("object", {}).get("sha", "")).strip()
    if not head_sha:
        raise GitHubPublishError("Unable to resolve branch head SHA.")

    head_commit = _api_request("GET", f"/repos/{repo}/git/commits/{head_sha}", expected_statuses={200})
    base_tree_sha = str(head_commit.get("tree", {}).get("sha", "")).strip()
    if not base_tree_sha:
        raise GitHubPublishError("Unable to resolve base tree SHA.")

    tree_entries: list[dict] = []
    for change in file_changes:
        normalized_path = _validate_repo_path(change.path)
        blob_sha = _create_blob(repo, _decode_change_content(change))
        tree_entries.append(
            {
                "path": normalized_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            }
        )

    tree_response = _api_request(
        "POST",
        f"/repos/{repo}/git/trees",
        payload={"base_tree": base_tree_sha, "tree": tree_entries},
        expected_statuses={201},
    )
    new_tree_sha = str(tree_response.get("sha", "")).strip()
    if not new_tree_sha:
        raise GitHubPublishError("Unable to create git tree.")

    commit_response = _api_request(
        "POST",
        f"/repos/{repo}/git/commits",
        payload={
            "message": commit_message.strip(),
            "tree": new_tree_sha,
            "parents": [head_sha],
        },
        expected_statuses={201},
    )
    commit_sha = str(commit_response.get("sha", "")).strip()
    if not commit_sha:
        raise GitHubPublishError("Unable to create commit.")

    _api_request(
        "PATCH",
        ref_path,
        payload={"sha": commit_sha, "force": False},
        expected_statuses={200},
    )

    workflow_payload = dict(workflow_inputs or {})
    workflow_payload.setdefault("source", "designer_publish")
    workflow_payload.setdefault("commit_sha", commit_sha)
    release_triggered = False
    backend_triggered = False
    if trigger_release_workflow:
        release_triggered = _trigger_workflow(repo, settings.github_release_workflow, branch, workflow_payload)
    if trigger_backend_workflow:
        backend_triggered = _trigger_workflow(repo, settings.github_backend_workflow, branch, workflow_payload)

    return GitHubPublishResult(
        repo=repo,
        branch=branch,
        commit_sha=commit_sha,
        release_workflow_triggered=release_triggered,
        backend_workflow_triggered=backend_triggered,
    )
