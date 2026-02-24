# Designer Client

`designer-client` is a separate external tool for content authoring and publish operations.

Scope of this bootstrap:
- edit and save level payloads through `/levels`,
- edit and stage runtime content payloads through `/content/runtime-config/stage`,
- publish staged runtime payloads through `/content/runtime-config/publish`.

Run:

```bash
python3 designer-client/designer_tool.py
```

The tool uses an admin bearer access token from the live backend.
