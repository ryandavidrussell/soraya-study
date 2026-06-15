# Soraya v1.2.4 — Hugging Face Gradio schema hotfix

## Symptom

Startup reaches Gradio, but the Space logs repeated errors like:

```text
TypeError: argument of type 'bool' is not iterable
```

The crash happens in `gradio_client.utils._json_schema_to_python_type()` while Gradio is rendering the Space homepage/API info.

## Cause

Older Gradio / gradio_client code assumes JSON Schema nodes are dictionaries. Some generated schemas contain boolean values, especially `additionalProperties: true`. The schema renderer then tries to evaluate:

```python
"const" in schema
```

where `schema` is actually `True`, causing the TypeError.

## Fix

`app.py` now applies a tiny runtime compatibility patch immediately after importing Gradio and before building the Blocks UI:

- Boolean JSON schema `True` is rendered as `Any`.
- Boolean JSON schema `False` is rendered as `None`.
- The patch is applied to both `gradio_client.utils` and `gradio.routes.client_utils`.

This avoids the `/` and `/info` schema crash without changing Soraya's runtime logic.

## Requirements

Keep the pinned stack:

```txt
gradio==4.44.0
gradio_client==1.3.0
fastapi==0.112.4
starlette==0.38.6
pydantic==2.10.6
huggingface_hub==0.25.2
jinja2==3.1.4
uvicorn==0.30.6
anyio==4.4.0
anthropic>=0.25.0
```

## Validation

Local checks:

```bash
python -m py_compile app.py ledger.py soraya_gates.py soraya_covenant.py
python test_gates.py
```

Result:

```text
41 passed, 0 failed
```

## Deploy note

Upload the new `app.py`, keep `requirements.txt` exactly named, then run a Hugging Face **Factory rebuild**.
