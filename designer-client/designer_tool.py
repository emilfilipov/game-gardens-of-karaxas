#!/usr/bin/env python3
"""Standalone designer client for level/content authoring operations."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from urllib import error, request


def _load_local_version() -> str:
    root = Path(__file__).resolve().parents[1]
    version_file = root / "VERSION"
    if version_file.exists():
        value = version_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return "0.0.0"


class DesignerTool(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Children of Ikphelion - Designer Client")
        self.geometry("1360x900")
        self.minsize(1120, 760)

        self.base_url = tk.StringVar(value="https://karaxas-backend-rss3xj2ixq-ew.a.run.app")
        self.email = tk.StringVar(value="")
        self.password = tk.StringVar(value="")
        self.otp_code = tk.StringVar(value="")
        self.client_version = tk.StringVar(value=_load_local_version())
        self.client_content_version = tk.StringVar(value="runtime_gameplay_v1")
        self.status_text = tk.StringVar(value="Please login.")
        self.commit_message = tk.StringVar(value="Designer content update")
        self.repo_path = tk.StringVar(value="assets/runtime/runtime_gameplay_config.json")
        self.trigger_release = tk.BooleanVar(value=True)
        self.trigger_backend = tk.BooleanVar(value=False)
        self.level_rows: list[dict] = []
        self.access_token = ""
        self.refresh_token = ""
        self.session_email = ""

        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        auth_row = ttk.Frame(root)
        auth_row.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(auth_row, text="API Base URL").pack(side=tk.LEFT)
        ttk.Entry(auth_row, width=44, textvariable=self.base_url).pack(side=tk.LEFT, padx=(8, 10))
        ttk.Label(auth_row, text="Email").pack(side=tk.LEFT)
        ttk.Entry(auth_row, width=26, textvariable=self.email).pack(side=tk.LEFT, padx=(8, 8))
        ttk.Label(auth_row, text="Password").pack(side=tk.LEFT)
        ttk.Entry(auth_row, width=22, textvariable=self.password, show="*").pack(side=tk.LEFT, padx=(8, 8))
        ttk.Label(auth_row, text="OTP").pack(side=tk.LEFT)
        ttk.Entry(auth_row, width=8, textvariable=self.otp_code).pack(side=tk.LEFT, padx=(8, 8))
        ttk.Button(auth_row, text="Login", command=self._login).pack(side=tk.LEFT, padx=(2, 8))
        ttk.Button(auth_row, text="Logout", command=self._logout).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(auth_row, text="Build").pack(side=tk.LEFT)
        ttk.Entry(auth_row, width=10, textvariable=self.client_version).pack(side=tk.LEFT, padx=(8, 8))
        ttk.Button(auth_row, text="Release Summary", command=self._ping_release_summary).pack(side=tk.LEFT)

        tabs = ttk.Notebook(root)
        tabs.pack(fill=tk.BOTH, expand=True)

        level_tab = ttk.Frame(tabs, padding=10)
        runtime_tab = ttk.Frame(tabs, padding=10)
        tabs.add(level_tab, text="Levels")
        tabs.add(runtime_tab, text="Runtime Content")

        self._build_levels_tab(level_tab)
        self._build_runtime_tab(runtime_tab)

        status_row = ttk.Frame(root)
        status_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(status_row, textvariable=self.status_text).pack(side=tk.LEFT)

    def _build_levels_tab(self, parent: ttk.Frame) -> None:
        controls = ttk.Frame(parent)
        controls.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(controls, text="Load Levels", command=self._load_levels).pack(side=tk.LEFT)
        ttk.Button(controls, text="Load Selected Level JSON", command=self._load_selected_level).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(controls, text="Save Level JSON", command=self._save_level_json).pack(side=tk.LEFT, padx=(8, 0))

        body = ttk.Frame(parent)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        list_col = ttk.Frame(body)
        list_col.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
        ttk.Label(list_col, text="Level List").pack(anchor="w")
        self.level_list = tk.Listbox(list_col, width=40, exportselection=False)
        self.level_list.pack(fill=tk.Y, expand=True)

        editor_col = ttk.Frame(body)
        editor_col.grid(row=0, column=1, sticky="nsew")
        ttk.Label(editor_col, text="Level JSON Payload").pack(anchor="w")
        self.level_payload = tk.Text(editor_col, wrap="none", undo=True)
        self.level_payload.pack(fill=tk.BOTH, expand=True)

    def _build_runtime_tab(self, parent: ttk.Frame) -> None:
        controls = ttk.Frame(parent)
        controls.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(controls, text="Load Runtime Config", command=self._load_runtime_config).pack(side=tk.LEFT)
        ttk.Button(controls, text="Stage Runtime Config", command=self._stage_runtime_config).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(controls, text="Publish Staged Runtime", command=self._publish_runtime_config).pack(side=tk.LEFT, padx=(8, 0))

        repo_controls = ttk.Frame(parent)
        repo_controls.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(repo_controls, text="Repo Path").pack(side=tk.LEFT)
        ttk.Entry(repo_controls, width=44, textvariable=self.repo_path).pack(side=tk.LEFT, padx=(8, 10))
        ttk.Label(repo_controls, text="Commit").pack(side=tk.LEFT)
        ttk.Entry(repo_controls, width=42, textvariable=self.commit_message).pack(side=tk.LEFT, padx=(8, 10))
        ttk.Checkbutton(repo_controls, text="Trigger Release Build", variable=self.trigger_release).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Checkbutton(repo_controls, text="Trigger Backend Deploy", variable=self.trigger_backend).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(repo_controls, text="Publish To GitHub CI", command=self._publish_to_github_ci).pack(side=tk.LEFT)

        ttk.Label(
            parent,
            text="Runtime config changes can be staged/published directly and optionally committed via backend to GitHub CI.",
        ).pack(anchor="w", pady=(0, 6))

        self.runtime_payload = tk.Text(parent, wrap="none", undo=True)
        self.runtime_payload.pack(fill=tk.BOTH, expand=True)

    def _set_status(self, text: str) -> None:
        self.status_text.set(text)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "X-Client-Version": self.client_version.get().strip() or "0.0.0",
            "X-Client-Content-Version": self.client_content_version.get().strip() or "runtime_gameplay_v1",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _request(self, method: str, path: str, payload: dict | None = None, allow_refresh_retry: bool = True) -> dict | list:
        base = self.base_url.get().strip().rstrip("/")
        if not base:
            raise ValueError("API Base URL is required.")
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        req = request.Request(f"{base}{path}", method=method, data=body, headers=self._headers())
        try:
            with request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                if not raw:
                    return {}
                parsed = json.loads(raw)
                if isinstance(parsed, (dict, list)):
                    return parsed
                return {}
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            if exc.code == 401 and allow_refresh_retry and self.refresh_token:
                if self._refresh_session():
                    return self._request(method, path, payload, allow_refresh_retry=False)
            detail = raw
            try:
                detail = json.dumps(json.loads(raw), indent=2)
            except Exception:
                pass
            raise RuntimeError(f"{exc.code} {exc.reason}: {detail}") from exc

    def _require_login(self) -> bool:
        if self.access_token:
            return True
        messagebox.showerror("Login Required", "Login is required before using designer operations.")
        return False

    def _login(self) -> None:
        email = self.email.get().strip()
        password = self.password.get()
        if not email or not password:
            messagebox.showerror("Missing Credentials", "Email and password are required.")
            return
        payload = {
            "email": email,
            "password": password,
            "otp_code": self.otp_code.get().strip() or None,
            "client_version": self.client_version.get().strip() or "0.0.0",
            "client_content_version_key": self.client_content_version.get().strip() or "runtime_gameplay_v1",
        }
        try:
            response = self._request("POST", "/auth/login", payload, allow_refresh_retry=False)
            if not isinstance(response, dict):
                raise RuntimeError("Unexpected login response.")
            self.access_token = str(response.get("access_token", "")).strip()
            self.refresh_token = str(response.get("refresh_token", "")).strip()
            self.session_email = str(response.get("email", email)).strip()
            if not self.access_token:
                raise RuntimeError("Login response missing access token.")
            self._set_status(f"Logged in as {self.session_email}.")
        except Exception as exc:
            messagebox.showerror("Login Failed", str(exc))
            self._set_status("Login failed.")

    def _logout(self) -> None:
        self.access_token = ""
        self.refresh_token = ""
        self.session_email = ""
        self._set_status("Logged out.")

    def _refresh_session(self) -> bool:
        token = self.refresh_token.strip()
        if not token:
            return False
        payload = {
            "refresh_token": token,
            "client_version": self.client_version.get().strip() or "0.0.0",
            "client_content_version_key": self.client_content_version.get().strip() or "runtime_gameplay_v1",
        }
        try:
            response = self._request("POST", "/auth/refresh", payload, allow_refresh_retry=False)
            if not isinstance(response, dict):
                return False
            self.access_token = str(response.get("access_token", "")).strip()
            new_refresh = str(response.get("refresh_token", "")).strip()
            if new_refresh:
                self.refresh_token = new_refresh
            return bool(self.access_token)
        except Exception:
            return False

    def _ping_release_summary(self) -> None:
        try:
            payload = self._request("GET", "/release/summary")
            if not isinstance(payload, dict):
                raise RuntimeError("Unexpected release summary response.")
            latest = str(payload.get("latest_version", "unknown"))
            client = str(payload.get("client_version", self.client_version.get().strip() or "0.0.0"))
            note = str(payload.get("latest_user_facing_notes", "")).strip() or str(payload.get("latest_build_release_notes", "")).strip()
            summary = f"Release summary: client={client}, latest={latest}"
            if note:
                summary += f" | notes: {note[:120]}"
            self._set_status(summary)
        except Exception as exc:
            messagebox.showerror("Release Summary Failed", str(exc))
            self._set_status("Release summary check failed.")

    def _load_levels(self) -> None:
        if not self._require_login():
            return
        try:
            rows = self._request("GET", "/levels")
            if not isinstance(rows, list):
                raise RuntimeError("Unexpected /levels response shape.")
            self.level_rows = rows
            self.level_list.delete(0, tk.END)
            for row in rows:
                level_id = int(row.get("id", 0))
                name = str(row.get("descriptive_name", row.get("name", f"level-{level_id}")))
                self.level_list.insert(tk.END, f"{level_id}: {name}")
            self._set_status(f"Loaded {len(rows)} levels.")
        except Exception as exc:
            messagebox.showerror("Load Levels Failed", str(exc))
            self._set_status("Load levels failed.")

    def _selected_level_id(self) -> int:
        selected = self.level_list.curselection()
        if not selected:
            raise RuntimeError("Select a level first.")
        row = self.level_rows[selected[0]]
        return int(row.get("id", 0))

    def _load_selected_level(self) -> None:
        if not self._require_login():
            return
        try:
            level_id = self._selected_level_id()
            payload = self._request("GET", f"/levels/{level_id}")
            self.level_payload.delete("1.0", tk.END)
            self.level_payload.insert("1.0", json.dumps(payload, indent=2))
            self._set_status(f"Loaded level {level_id}.")
        except Exception as exc:
            messagebox.showerror("Load Level Failed", str(exc))
            self._set_status("Load selected level failed.")

    def _save_level_json(self) -> None:
        if not self._require_login():
            return
        try:
            payload = json.loads(self.level_payload.get("1.0", tk.END).strip())
            self._request("POST", "/levels", payload)
            self._set_status("Level payload saved.")
            self._load_levels()
        except Exception as exc:
            messagebox.showerror("Save Level Failed", str(exc))
            self._set_status("Save level failed.")

    def _load_runtime_config(self) -> None:
        if not self._require_login():
            return
        try:
            payload = self._request("GET", "/content/runtime-config")
            self.runtime_payload.delete("1.0", tk.END)
            self.runtime_payload.insert("1.0", json.dumps(payload, indent=2))
            self._set_status("Runtime config loaded.")
        except Exception as exc:
            messagebox.showerror("Load Runtime Failed", str(exc))
            self._set_status("Load runtime config failed.")

    def _stage_runtime_config(self) -> None:
        if not self._require_login():
            return
        try:
            payload = json.loads(self.runtime_payload.get("1.0", tk.END).strip())
            self._request("POST", "/content/runtime-config/stage", {"payload": payload})
            self._set_status("Runtime config staged.")
        except Exception as exc:
            messagebox.showerror("Stage Runtime Failed", str(exc))
            self._set_status("Stage runtime config failed.")

    def _publish_runtime_config(self) -> None:
        if not self._require_login():
            return
        try:
            self._request("POST", "/content/runtime-config/publish", {})
            self._set_status("Staged runtime config published.")
        except Exception as exc:
            messagebox.showerror("Publish Runtime Failed", str(exc))
            self._set_status("Publish runtime config failed.")

    def _publish_to_github_ci(self) -> None:
        if not self._require_login():
            return
        try:
            runtime_json = self.runtime_payload.get("1.0", tk.END).strip()
            if not runtime_json:
                raise RuntimeError("Runtime payload is empty.")
            json.loads(runtime_json)
            repo_path = self.repo_path.get().strip()
            if not repo_path:
                raise RuntimeError("Repository path is required.")
            commit_message = self.commit_message.get().strip()
            if len(commit_message) < 3:
                raise RuntimeError("Commit message must be at least 3 characters.")
            payload = {
                "commit_message": commit_message,
                "file_changes": [
                    {
                        "path": repo_path,
                        "content": runtime_json + "\n",
                        "encoding": "utf-8",
                    }
                ],
                "trigger_release_workflow": bool(self.trigger_release.get()),
                "trigger_backend_workflow": bool(self.trigger_backend.get()),
                "workflow_inputs": {"origin": "designer-client"},
            }
            response = self._request("POST", "/designer/publish", payload)
            if not isinstance(response, dict):
                raise RuntimeError("Unexpected publish response.")
            self._set_status(
                "Published commit %s on %s (release=%s backend=%s)." % (
                    str(response.get("commit_sha", "unknown"))[:12],
                    str(response.get("branch", "main")),
                    str(response.get("release_workflow_triggered", False)),
                    str(response.get("backend_workflow_triggered", False)),
                )
            )
        except Exception as exc:
            messagebox.showerror("GitHub Publish Failed", str(exc))
            self._set_status("GitHub publish failed.")


def main() -> int:
    app = DesignerTool()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
