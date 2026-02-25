# Designer Client

`designer-client` is a separate external tool for content authoring and publish operations.

Scope of this bootstrap:
- login using backend auth (`/auth/login`) with the same client version/content headers as the game client,
- edit and save level payloads through `/levels`,
- edit and stage runtime content payloads through `/content/runtime-config/stage`,
- publish staged runtime payloads through `/content/runtime-config/publish`,
- submit repo commit + workflow dispatch through backend-managed `/designer/publish`.

Run:

```bash
python3 designer-client/designer_tool.py
```

Designer operations require backend login and an admin account.
