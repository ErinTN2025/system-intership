import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
from urllib.parse import urlsplit, unquote
import yaml

os.umask(0o077)
root = Path.home() / 'osh-lab/octavia'
root.mkdir(parents=True, exist_ok=True)
path = root / 'credentials-private.yaml'

def read_secret(name):
    result = subprocess.run(['kubectl', '-n', 'openstack', 'get', 'secret', name, '-o', 'json'],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise SystemExit('Khong doc duoc Secret ' + name + '; dung lai')
    return {k: base64.b64decode(v).decode() for k, v in json.loads(result.stdout)['data'].items()}

def required(data, key):
    value = data.get(key, '')
    assert value, 'Secret thieu key ' + key
    return value

admin = read_secret('nova-keystone-admin')
service = read_secret('nova-keystone-user')
db_uri = urlsplit(required(read_secret('nova-db-admin'), 'DB_CONNECTION'))
assert db_uri.scheme.startswith('mysql') and db_uri.username and db_uri.password, 'DB URL khong hop le'
assert db_uri.hostname == 'mariadb.openstack.svc.cluster.local', 'DB host khac du kien; dung doi chieu'
if path.exists():
    values = yaml.safe_load(path.read_text())
    endpoints = values['endpoints']
    ks_password = endpoints['identity']['auth']['octavia']['password']
    db_password = endpoints['oslo_db']['auth']['octavia']['password']
    cache_key = endpoints['oslo_cache']['auth']['memcache_secret_key']
    assert ks_password and db_password and cache_key, 'File private thieu credentials'
else:
    result = subprocess.run(['helm', 'list', '-n', 'openstack', '--filter', '^octavia$', '-o', 'json'],
                            capture_output=True, text=True, timeout=30, check=True)
    assert not json.loads(result.stdout), 'Octavia da co release; khong sinh credentials moi'
    ks_password, db_password, cache_key = [secrets.token_hex(24) for _ in range(3)]

admin_auth = {
    'username': required(admin, 'OS_USERNAME'), 'password': required(admin, 'OS_PASSWORD'),
    'project_name': required(admin, 'OS_PROJECT_NAME'),
    'user_domain_name': required(admin, 'OS_USER_DOMAIN_NAME'),
    'project_domain_name': required(admin, 'OS_PROJECT_DOMAIN_NAME'),
    'region_name': admin.get('OS_REGION_NAME') or 'RegionOne'}
service_auth = {
    'username': 'octavia', 'password': ks_password, 'role': 'admin',
    'project_name': required(service, 'OS_PROJECT_NAME'),
    'user_domain_name': required(service, 'OS_USER_DOMAIN_NAME'),
    'project_domain_name': required(service, 'OS_PROJECT_DOMAIN_NAME'),
    'region_name': admin_auth['region_name']}
db_auth = {'admin': {'username': unquote(db_uri.username), 'password': unquote(db_uri.password)},
           'octavia': {'username': 'octavia', 'password': db_password}}
values = {'endpoints': {
    'identity': {'auth': {'admin': admin_auth, 'octavia': service_auth}},
    'oslo_db': {'auth': db_auth}, 'oslo_db_persistence': {'auth': db_auth},
    'oslo_cache': {'auth': {'memcache_secret_key': cache_key}}}}
path.write_text(yaml.safe_dump(values, sort_keys=False))
os.chmod(path, 0o600)
print('PASS: da luu ' + str(path) + '; mode 600; khong in password')
print('Service project=' + service_auth['project_name'] + ', user domain=' + service_auth['user_domain_name'])
print('Chua tao DB/Keystone user; chart Jobs se tao khi install.')
