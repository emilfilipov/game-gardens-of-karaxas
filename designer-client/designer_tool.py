#!/usr/bin/env python3
"""Standalone designer client for level/content authoring operations."""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk
from urllib import error, request


class DesignerTool(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Gardens of Karaxas - Designer Client")
        self.geometry("1320x860")
        self.minsize(1060, 760)

        self.base_url = tk.StringVar(value="https://karaxas-backend-rss3xj2ixq-ew.a.run.app")
        self.access_token = tk.StringVar(value="")
        self.status_text = tk.StringVar(value="Ready.")
        self.level_rows: list[dict] = []

        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        auth_row = ttk.Frame(root)
        auth_row.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(auth_row, text="API Base URL").pack(side=tk.LEFT)
        ttk.Entry(auth_row, width=54, textvariable=self.base_url).pack(side=tk.LEFT, padx=(8, 14))
        ttk.Label(auth_row, text="Admin Access Token").pack(side=tk.LEFT)
        ttk.Entry(auth_row, width=66, textvariable=self.access_token, show="*").pack(side=tk.LEFT, padx=(8, 8))
        ttk.Button(auth_row, text="Ping Runtime Config", command=self._ping_runtime).pack(side=tk.LEFT)

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
        self.level_list = tk.Listbox(list_col, width=38, exportselection=False)
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

        ttk.Label(
            parent,
            text="Use this panel for content/asset gameplay payload updates. Stage first, then publish.",
        ).pack(anchor="w", pady=(0, 6))

        self.runtime_payload = tk.Text(parent, wrap="none", undo=True)
        self.runtime_payload.pack(fill=tk.BOTH, expand=True)

    def _set_status(self, text: str) -> None:
        self.status_text.set(text)

    def _headers(self) -> dict[str, str]:
        token = self.access_token.get().strip()
        headers = {
            "Content-Type": "application/json",
            "X-Client-Version": "designer-1.0.0",
            "X-Client-Content-Version": "runtime_gameplay_v1",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
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
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            detail = raw
            try:
                detail = json.dumps(json.loads(raw), indent=2)
            except Exception:
                pass
            raise RuntimeError(f"{exc.code} {exc.reason}: {detail}") from exc

    def _require_token(self) -> bool:
        if self.access_token.get().strip():
            return True
        messagebox.showerror("Missing Token", "Please provide an admin bearer token.")
        return False

    def _ping_runtime(self) -> None:
        if not self._require_token():
            return
        try:
            payload = self._request("GET", "/content/runtime-config")
            key = str(payload.get("config_key", "runtime_gameplay_v1"))
            self._set_status(f"Runtime reachable. config_key={key}")
        except Exception as exc:
            messagebox.showerror("Runtime Check Failed", str(exc))
            self._set_status("Runtime check failed.")

    def _load_levels(self) -> None:
        if not self._require_token():
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
        if not self._require_token():
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
        if not self._require_token():
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
        if not self._require_token():
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
        if not self._require_token():
            return
        try:
            payload = json.loads(self.runtime_payload.get("1.0", tk.END).strip())
            self._request("POST", "/content/runtime-config/stage", payload)
            self._set_status("Runtime config staged.")
        except Exception as exc:
            messagebox.showerror("Stage Runtime Failed", str(exc))
            self._set_status("Stage runtime config failed.")

    def _publish_runtime_config(self) -> None:
        if not self._require_token():
            return
        try:
            self._request("POST", "/content/runtime-config/publish", {})
            self._set_status("Staged runtime config published.")
        except Exception as exc:
            messagebox.showerror("Publish Runtime Failed", str(exc))
            self._set_status("Publish runtime config failed.")


def main() -> int:
    app = DesignerTool()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
