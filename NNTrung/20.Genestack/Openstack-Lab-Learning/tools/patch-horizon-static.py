#!/usr/bin/env python3
"""Patch a copied Horizon chart; safe to run again."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: patch-horizon-static.py CHART_DIR")
path = Path(sys.argv[1]).expanduser() / "templates/bin/_horizon.sh.tpl"
text = path.read_text()
marker = "  /tmp/manage.py collectstatic --noinput"
addition = '  # Return to Horizon after compiling plugin translations.\n  cd "${SITE_PACKAGES_ROOT}/openstack_dashboard"\n'
if text.count(marker) != 1:
    raise SystemExit("Unexpected startup script: collectstatic marker missing or duplicated")
if addition + marker not in text:
    path.write_text(text.replace(marker, addition + marker, 1))
print("Startup script ready:", path)
