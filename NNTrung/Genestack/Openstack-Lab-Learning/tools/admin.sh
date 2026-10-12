#!/usr/bin/env bash
# Source this file. Reads credentials; does not deploy anything or edit /etc/hosts.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo 'Use: source ~/osh-lab/bin/admin.sh' >&2
  exit 1
fi
_osh_admin_load() {
  local venv="${OSH_CLIENT_VENV:-$HOME/openstack-client}"
  local ns="${OSH_NAMESPACE:-openstack}" secret="${OSH_ADMIN_SECRET:-nova-keystone-admin}"
  local domain="${OSH_DOMAIN:-lab.test}" port data encoded key value host
  local -A auth=()
  for key in kubectl python3 base64; do
    command -v "$key" >/dev/null || { echo "Missing tool: $key" >&2; return 1; }
  done
  [[ -f "$venv/bin/activate" ]] || { echo "Missing venv: $venv" >&2; return 1; }
  port=$(kubectl -n envoyproxy-gateway-system get svc openstack-gateway \
    -o jsonpath='{.spec.ports[?(@.port==443)].nodePort}') || return 1
  [[ "$port" =~ ^[0-9]+$ ]] || { echo 'Gateway HTTPS NodePort missing' >&2; return 1; }
  data=$(kubectl -n "$ns" get secret "$secret" -o json) || return 1
  encoded=$(printf '%s' "$data" | python3 -c '
import base64,json,sys
try:
    d=json.load(sys.stdin)["data"]
    keys=["OS_USERNAME","OS_PASSWORD","OS_PROJECT_NAME","OS_USER_DOMAIN_NAME","OS_PROJECT_DOMAIN_NAME"]
    for k in keys:
        assert d.get(k) and base64.b64decode(d[k],validate=True), "missing auth key"
    for k in keys:
        print(k+"\t"+d[k])
except Exception:
    sys.exit("Admin Secret missing/invalid auth fields; no credentials printed")
') || return 1
  while IFS=$'\t' read -r key value; do
    auth["$key"]=$(printf '%s' "$value" | base64 -d) || return 1
  done <<< "$encoded"
  for host in keystone nova neutron glance cinder octavia; do
    getent ahosts "$host.$domain" >/dev/null || {
      echo "DNS missing: $host.$domain; configure DNS or /etc/hosts to a reachable node IP first." >&2
      return 1
    }
  done
  source "$venv/bin/activate" || return 1
  command -v openstack >/dev/null || { echo 'OpenStack CLI missing in venv' >&2; return 1; }
  python -c 'import octaviaclient' >/dev/null 2>&1 || {
    echo 'Octavia CLI plugin missing. Run: python -m pip install python-octaviaclient' >&2
    return 1
  }
  # Remove alternate auth selectors from previous sessions.
  unset OS_CLOUD OS_TOKEN OS_ENDPOINT OS_AUTH_TOKEN OS_SERVICE_TOKEN OS_SERVICE_ENDPOINT
  unset OS_PROJECT_ID OS_USER_ID OS_USER_DOMAIN_ID OS_PROJECT_DOMAIN_ID
  for key in "${!auth[@]}"; do export "$key=${auth[$key]}"; done
  export OS_AUTH_TYPE=password OS_IDENTITY_API_VERSION=3 OS_INTERFACE=public
  export OS_REGION_NAME="${OSH_REGION:-RegionOne}"
  export OS_AUTH_URL="https://keystone.$domain:$port/v3"
  export OS_IDENTITY_ENDPOINT_OVERRIDE="$OS_AUTH_URL"
  export OS_COMPUTE_ENDPOINT_OVERRIDE="https://nova.$domain:$port/v2.1"
  export OS_NETWORK_ENDPOINT_OVERRIDE="https://neutron.$domain:$port"
  export OS_IMAGE_ENDPOINT_OVERRIDE="https://glance.$domain:$port"
  export OS_BLOCK_STORAGE_ENDPOINT_OVERRIDE="https://cinder.$domain:$port/v3"
  export OS_VOLUME_API_VERSION=3
  # Octavia uses its public Keystone catalog endpoint, registered by its Helm Jobs.
  export OS_INSECURE="${OSH_INSECURE:-true}"
  if [[ -n "${OSH_CACERT:-}" ]]; then
    export OS_CACERT="$OSH_CACERT" OS_INSECURE=false
  else
    unset OS_CACERT
  fi
  printf 'OpenStack admin loaded via HTTPS Gateway :%s; Octavia CLI ready.\n' "$port"
  printf 'Try: openstack token issue / openstack port list / openstack loadbalancer list\n'
}
if _osh_admin_load; then
  unset -f _osh_admin_load
else
  unset -f _osh_admin_load
  return 1
fi
