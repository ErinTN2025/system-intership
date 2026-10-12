import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import yaml

os.umask(0o077)
root = Path.home() / 'osh-lab/octavia'
root.mkdir(parents=True, exist_ok=True)
private = root / 'rabbitmq-private.yaml'
secret_name = 'gs-octavia-rabbitmq-credentials'

def kubectl(args, **kwargs):
    return subprocess.run(['kubectl', '-n', 'openstack'] + args,
                          capture_output=True, text=True, timeout=60, **kwargs)

existing = kubectl(['get', 'secret', secret_name, '--ignore-not-found', '-o', 'json'], check=True)
if private.exists():
    values = yaml.safe_load(private.read_text())
    auth = values['endpoints']['oslo_messaging']['auth']['octavia']
    assert auth['username'] == 'octavia' and auth['password'], 'Private values khong hop le'
    password = auth['password']
else:
    assert not existing.stdout.strip(), 'Secret da ton tai: khong tao password moi; can doi chieu truoc'
    password = secrets.token_hex(24)
    values = {'endpoints': {'oslo_messaging': {
        'auth': {'octavia': {'username': 'octavia', 'password': password}},
        'hosts': {'default': 'rabbitmq-genestack'},
        'host_fqdn_override': {'default': 'rabbitmq-genestack.openstack.svc.cluster.local'},
        'path': '/octavia'}}}
    private.write_text(yaml.safe_dump(values, sort_keys=False))
os.chmod(private, 0o600)
if existing.stdout.strip():
    data = json.loads(existing.stdout)['data']
    assert base64.b64decode(data['username']).decode() == 'octavia'
    assert base64.b64decode(data['password']).decode() == password, 'Password file va Secret lech; dung lai'

labels = {'lab-component': 'octavia-topology'}
def obj(kind, name, spec):
    return {'apiVersion': 'rabbitmq.com/v1beta1', 'kind': kind,
            'metadata': {'name': name, 'namespace': 'openstack', 'labels': labels}, 'spec': spec}
ref = {'name': 'rabbitmq-genestack', 'namespace': 'openstack'}
objects = [{'apiVersion': 'v1', 'kind': 'Secret',
    'metadata': {'name': secret_name, 'namespace': 'openstack'}, 'type': 'Opaque',
    'stringData': {'username': 'octavia', 'password': password}},
    obj('User', 'gs-octavia-user', {'rabbitmqClusterReference': ref,
        'tags': ['management', 'policymaker'], 'importCredentialsSecret': {'name': secret_name}}),
    obj('Vhost', 'gs-octavia-vhost', {'name': 'octavia', 'defaultQueueType': 'quorum',
        'rabbitmqClusterReference': ref}),
    obj('Permission', 'gs-octavia-permission', {'vhost': 'octavia',
        'userReference': {'name': 'gs-octavia-user'}, 'rabbitmqClusterReference': ref,
        'permissions': {'configure': '.*', 'read': '.*', 'write': '.*'}})]
result = kubectl(['apply', '-f', '-'], input=yaml.safe_dump_all(objects, sort_keys=False))
if result.returncode:
    raise SystemExit('Apply topology that bai; dung lai. Khong in payload chua password.')
print(result.stdout, end='')
print('Private values: ' + str(private) + ' (khong gui noi dung, khong commit Git)')
print('Da tao/cap nhat topology Octavia; chua tao DB, chua install Octavia.')
