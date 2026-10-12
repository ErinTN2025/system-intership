#!/usr/bin/env bash
# Local files only. No kubectl/Helm apply, no network, no data restore.
set -euo pipefail
umask 077
study=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
for cmd in cp tar; do command -v "$cmd" >/dev/null || { echo "Missing $cmd" >&2; exit 1; }; done
out=${1:-"$study/workspace/files-$(date +%Y%m%d-%H%M%S)-$$"}
if [ -e "$out" ]; then
  printf 'Target already exists, refusing to overwrite: %s\n' "$out" >&2
  exit 1
fi
mkdir -p "$out/bin" "$out/charts" "$out/overrides" "$out/operators" "$out/gateway-api" "$out/talos"
cp "$study/tools/admin.sh" "$study/tools/load-admin.sh" "$out/bin/"
cp -a "$study/assets/charts/." "$out/charts/"
cp -a "$study/assets/gateway-api/charts" "$out/gateway-api/"
cp -a "$study/config/overrides/." "$out/overrides/"
cp -a "$study/config/operators/." "$out/operators/"
cp -a "$study/config/gateway/." "$out/gateway-api/"
cp -a "$study/config/talos/." "$out/talos/"
# Only unpack archives when their chart directory is absent.
# Existing Talos-patched local charts always take precedence.
for archive in "$study"/assets/chart-archives/*.tgz; do
  test -f "$archive" || continue
  first=$(tar -tzf "$archive" | sed -n '1p')
  name=${first%%/*}
  if [[ -z "$name" || "$name" == "." || "$name" == ".." || "$name" == -* || "$name" == *\\* ]]; then
    echo 'Unexpected chart archive root; stop before extraction' >&2; exit 1
  fi
  if tar -tzf "$archive" | grep -Eq '(^/|(^|/)\.\.(/|$))'; then
    echo 'Unsafe archive member; stop' >&2; exit 1
  fi
  if [ ! -d "$out/charts/$name" ]; then tar -xzf "$archive" -C "$out/charts"; fi
done
printf 'Files prepared at: %s\n' "$out"
printf 'No cluster changes. Review config/node/IP/disk and read START-HERE.md.\n'
