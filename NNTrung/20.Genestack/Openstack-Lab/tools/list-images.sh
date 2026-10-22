#!/usr/bin/env bash
# Read-only cluster inventory. Does not collect Secrets or download images.
set -euo pipefail
umask 077
for cmd in kubectl jq; do
  command -v "$cmd" >/dev/null || { printf 'Missing tool: %s\n' "$cmd" >&2; exit 1; }
done
out=${1:-"$HOME/Openstack-Lab-Learning/artifacts/image-inventory"}
mkdir -p "$out"
kubectl get pods -A -o json | jq -r '
  .items[] | .spec |
  (.containers[]?, .initContainers[]?, .ephemeralContainers[]?) |
  .image // empty' | LC_ALL=C sort -u > "$out/images-pods.txt"
kubectl get deployments,statefulsets,daemonsets,jobs,cronjobs -A -o json | jq -r '
  .items[] | .. | objects |
  select(has("containers") or has("initContainers")) |
  (.containers[]?, .initContainers[]?) | .image // empty' |
  LC_ALL=C sort -u > "$out/images-workloads.txt"
LC_ALL=C sort -u "$out/images-pods.txt" "$out/images-workloads.txt" > "$out/images-observed.txt"
printf 'Observed images: %s\n' "$out/images-observed.txt"
printf 'Not a complete cold-install inventory: also inspect hooks, operator specs and Talos/core images.\n'
