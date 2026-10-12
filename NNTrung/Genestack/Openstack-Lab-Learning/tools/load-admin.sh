load_osh_admin() {
  local auth_key auth_value
  for auth_key in OS_USERNAME OS_PASSWORD OS_PROJECT_NAME OS_USER_DOMAIN_NAME OS_PROJECT_DOMAIN_NAME; do
    auth_value=$(kubectl -n openstack get secret nova-keystone-admin \
      -o "jsonpath={.data.${auth_key}}" | base64 -d) || return 1
    if [ -z "$auth_value" ]; then
      printf 'Thieu key %s trong Secret\n' "$auth_key"
      return 1
    fi
    export "$auth_key=$auth_value"
  done
  export OS_AUTH_TYPE=password
  export OS_IDENTITY_API_VERSION=3
  export OS_AUTH_URL="${OSH_AUTH_URL:-http://127.0.0.1:5000/v3}"
  export OS_IDENTITY_ENDPOINT_OVERRIDE="$OS_AUTH_URL"
}
