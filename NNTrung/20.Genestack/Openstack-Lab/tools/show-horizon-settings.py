"""Read rendered YAML and display only selected noncredential settings."""
import base64
import re
import sys
from pathlib import Path
import yaml

if len(sys.argv) != 2:
    raise SystemExit("Usage: python3 show-horizon-settings.py rendered.yaml")
allowed = re.compile(r"^\s*(ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS|SECURE_PROXY_SSL_HEADER|CSRF_COOKIE_SECURE|SESSION_COOKIE_SECURE|OPENSTACK_ENDPOINT_TYPE)\s*=")
found = False
for obj in yaml.safe_load_all(Path(sys.argv[1]).read_text()):
    if not isinstance(obj, dict) or obj.get("kind") not in ("Secret", "ConfigMap"):
        continue
    texts = []
    for value in (obj.get("data") or {}).values():
        if not isinstance(value, str):
            continue
        try:
            texts.append(base64.b64decode(value, validate=True).decode() if obj["kind"] == "Secret" else value)
        except (ValueError, UnicodeError):
            continue
    texts.extend(v for v in (obj.get("stringData") or {}).values() if isinstance(v, str))
    for content in texts:
        for line in content.splitlines():
            if allowed.match(line):
                print(line.strip())
                found = True
if not found:
    raise SystemExit("No selected Horizon settings found; check chart render structure.")
