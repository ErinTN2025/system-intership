"""Prepare and render Octavia OVN only; never install or print credentials."""
import base64
import configparser
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlsplit, unquote
import yaml

os.umask(0o077)
root = Path.home() / 'osh-lab/octavia'
chart = Path.home() / 'osh-lab/charts/octavia'
assert yaml.safe_load((chart / 'Chart.yaml').read_text())['version'] == '2026.1.8+d03dd061a'
private = yaml.safe_load((root / 'credentials-private.yaml').read_text())
rabbit = yaml.safe_load((root / 'rabbitmq-private.yaml').read_text())
def read(args):
    p = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if p.returncode:
        raise SystemExit('Failed: ' + ' '.join(args[:3]) + '; no credentials printed')
    return json.loads(p.stdout)
ssl = read(['helm', 'get', 'values', 'kube-ovn', '-n', 'kube-system', '--all', '-o', 'json'])
assert ssl.get('networking', {}).get('ENABLE_SSL') is False, 'OVN SSL differs; stop'
def ovn(name, port):
    s = read(['kubectl', '-n', 'kube-system', 'get', 'svc', name, '-o', 'json'])['spec']
    assert any(p['port'] == port for p in s['ports'])
    assert s['clusterIP'] not in ('None', '')
    return 'tcp:' + s['clusterIP'] + ':' + str(port)
proxy = read(['kubectl', '-n', 'envoyproxy-gateway-system', 'get', 'svc', 'openstack-gateway', '-o', 'json'])
https = next(p['nodePort'] for p in proxy['spec']['ports'] if p['port'] == 443)
node = read(['kubectl', 'get', 'node', 'controlplane-01', '-o', 'json'])
assert any(c['type'] == 'Ready' and c['status'] == 'True' for c in node['status']['conditions'])
images = {
    'dep_check': 'ghcr.io/rackerlabs/genestack-images/kubernetes-entrypoint:latest',
    'db_init': 'ghcr.io/rackerlabs/genestack-images/openstack-client:2026.1-latest',
    'ks_user': 'ghcr.io/rackerlabs/genestack-images/openstack-client:2026.1-latest',
    'ks_service': 'ghcr.io/rackerlabs/genestack-images/openstack-client:2026.1-latest',
    'ks_endpoints': 'ghcr.io/rackerlabs/genestack-images/openstack-client:2026.1-latest',
    'octavia_api': 'ghcr.io/rackerlabs/genestack-images/octavia:2026.1-latest',
    'octavia_driver_agent': 'ghcr.io/rackerlabs/genestack-images/octavia:2026.1-latest',
    'octavia_db_sync': 'ghcr.io/rackerlabs/genestack-images/octavia:2026.1-latest'}
service_auth = dict(private['endpoints']['identity']['auth']['octavia'])
service_auth.pop('role', None)
service_auth.update(auth_type='password', auth_version='v3', interface='internal',
                    auth_url='http://keystone-api.openstack.svc.cluster.local:5000/v3')
endpoints = {
    'identity': {'hosts': {'default': 'keystone-api', 'internal': 'keystone-api'},
        'port': {'api': {'default': 5000, 'internal': 5000}}},
    'network': {'hosts': {'default': 'neutron-server', 'internal': 'neutron-server'},
        'port': {'api': {'default': 9696, 'internal': 9696}}},
    'load_balancer': {'hosts': {'default': 'octavia-api', 'internal': 'octavia-api', 'public': 'octavia.lab.test'},
        'host_fqdn_override': {'public': 'octavia.lab.test'},
        'scheme': {'default': 'http', 'internal': 'http', 'public': 'https'},
        'port': {'api': {'default': 9876, 'internal': 9876, 'public': https}}}}
for name in ['oslo_db', 'oslo_db_persistence']:
    endpoints[name] = {'hosts': {'default': 'mariadb'},
        'host_fqdn_override': {'default': 'mariadb.openstack.svc.cluster.local'}}
values = {
    'images': {'tags': images}, 'endpoints': endpoints,
    'labels': {k: {'node_selector_key': 'kubernetes.io/hostname', 'node_selector_value': 'controlplane-01'}
               for k in ['api', 'job']},
    'bootstrap': {'enabled': False},
    'manifests': {'deployment_api': True, 'deployment_driver_agent': False,
        'daemonset_worker': False, 'daemonset_health_manager': False, 'deployment_housekeeping': False,
        'job_bootstrap': False, 'job_image_repo_sync': False, 'job_rabbit_init': False,
        'job_db_init': True, 'job_db_sync': True, 'job_ks_user': True,
        'job_ks_service': True, 'job_ks_endpoints': True, 'pod_rally_test': False},
    'dependencies': {'static': {'api': {'jobs': ['octavia-db-sync', 'octavia-ks-user', 'octavia-ks-endpoints']}}},
    'pod': {'resources': {'enabled': True, 'api': {
        'requests': {'cpu': '250m', 'memory': '512Mi'}, 'limits': {'memory': '1536Mi'}}}},
    'conf': {'octavia_api_uwsgi': {'uwsgi': {'processes': 1, 'threads': 2}}, 'octavia': {
        'api_settings': {'default_provider_driver': 'ovn', 'enabled_provider_drivers': 'ovn:OVN provider'},
        'driver_agent': {'enabled_provider_agents': 'ovn'},
        'neutron': {'endpoint_type': 'internalURL', 'valid_interfaces': 'internal',
                    'endpoint_override': 'http://neutron-server.openstack.svc.cluster.local:9696'},
        'ovn': {'ovn_nb_connection': ovn('ovn-nb', 6641), 'ovn_sb_connection': ovn('ovn-sb', 6642)},
        'task_flow': {'jobboard_enabled': False}, 'service_auth': service_auth,
        'oslo_messaging_rabbit': {'rabbit_quorum_queue': True, 'rabbit_transient_quorum_queue': False}}}}
# Service auth contains a password: keep it in private credentials, not public lab values.
private.setdefault('conf', {}).setdefault('octavia', {})['service_auth'] = values['conf']['octavia'].pop('service_auth')
(root / 'credentials-private.yaml').write_text(yaml.safe_dump(private, sort_keys=False))
(root / 'lab-values.yaml').write_text(yaml.safe_dump(values, sort_keys=False))
post = root / 'post-render.py'
post.write_text('''#!/usr/bin/env python3
import copy
import sys
import yaml
docs = [d for d in yaml.safe_load_all(sys.stdin) if isinstance(d, dict)]
api = next(d for d in docs if d.get('kind') == 'Deployment' and d['metadata']['name'] == 'octavia-api')
spec = api['spec']['template']['spec']
container = next(c for c in spec['containers'] if c['name'] == 'octavia-api')
container.setdefault('securityContext', {})['runAsUser'] = 0
assert not any(v['name'] == 'pod-run-octavia' for v in spec['volumes'])
spec['volumes'].append({'name': 'pod-run-octavia', 'emptyDir': {}})
container['volumeMounts'].append({'name': 'pod-run-octavia', 'mountPath': '/var/run/octavia'})
mounts = [copy.deepcopy(m) for m in container['volumeMounts'] if m['name'] in
          ['pod-etc-octavia', 'octavia-etc', 'octavia-etc-snippets', 'oslo-lock-path', 'pod-run-octavia']]
# Include config file + snippets, but not API-specific uWSGI or policy mounts.
mounts = [m for m in mounts if m.get('subPath') not in ['octavia-api-uwsgi.ini', 'policy.yaml']]
spec['containers'].append({'name': 'octavia-agent', 'image': container['image'],
    'imagePullPolicy': 'IfNotPresent', 'securityContext': {'runAsUser': 0},
    'command': ['octavia-driver-agent', '--config-file', '/etc/octavia/octavia.conf',
                '--config-dir', '/etc/octavia/octavia.conf.d'],
    'resources': {'requests': {'cpu': '100m', 'memory': '128Mi'}, 'limits': {'memory': '512Mi'}},
    'volumeMounts': mounts})
for d in docs:
    if d.get('kind') == 'Deployment':
        pod = d['spec']['template']['spec']
    elif d.get('kind') == 'Job':
        pod = d['spec']['template']['spec']
    else:
        continue
    tolerations = pod.setdefault('tolerations', [])
    if not any(t.get('key') == 'node-role.kubernetes.io/control-plane' for t in tolerations):
        tolerations.append({'key': 'node-role.kubernetes.io/control-plane', 'operator': 'Exists', 'effect': 'NoSchedule'})
yaml.safe_dump_all(docs, sys.stdout, sort_keys=False)
''')
os.chmod(post, 0o700)
args = ['helm', 'template', 'octavia', str(chart), '-n', 'openstack',
        '-f', str(root / 'lab-values.yaml'), '-f', str(root / 'credentials-private.yaml'),
        '-f', str(root / 'rabbitmq-private.yaml'), '--post-renderer', str(post)]
p = subprocess.run(args, capture_output=True, text=True, timeout=120)
(root / 'render-error.txt').write_text(p.stderr)
if p.returncode:
    raise SystemExit('Render failed; inspect render-error.txt locally; do not send secrets or raw debug output')
(root / 'rendered.yaml').write_text(p.stdout)
docs = [d for d in yaml.safe_load_all(p.stdout) if isinstance(d, dict)]
api = next(d for d in docs if d.get('kind') == 'Deployment' and d['metadata']['name'] == 'octavia-api')
containers = api['spec']['template']['spec']['containers']
assert {c['name'] for c in containers} == {'octavia-api', 'octavia-agent'}
assert all(any(m['mountPath'] == '/var/run/octavia' and m['name'] == 'pod-run-octavia'
               for m in c['volumeMounts']) for c in containers)
assert not any(d.get('kind') == 'DaemonSet' for d in docs)
assert not any(d.get('kind') == 'Deployment' and d['metadata']['name'] != 'octavia-api' for d in docs)
jobs = {d['metadata']['name'] for d in docs if d.get('kind') == 'Job'}
assert {'octavia-db-init', 'octavia-db-sync', 'octavia-ks-user', 'octavia-ks-service', 'octavia-ks-endpoints'} <= jobs
assert 'octavia-rabbit-init' not in jobs
etc = next(d for d in docs if d.get('kind') == 'Secret' and d['metadata']['name'] == 'octavia-etc')
config = configparser.ConfigParser(interpolation=None, strict=False)
config.read_string(base64.b64decode(etc['data']['octavia.conf']).decode())
assert config.get('neutron', 'valid_interfaces') == 'internal'
assert config.get('neutron', 'endpoint_override') == 'http://neutron-server.openstack.svc.cluster.local:9696'
assert config.get('api_settings', 'default_provider_driver') == 'ovn'
assert not config.getboolean('task_flow', 'jobboard_enabled')
assert config.get('ovn', 'ovn_nb_connection') == values['conf']['octavia']['ovn']['ovn_nb_connection']
assert config.get('ovn', 'ovn_sb_connection') == values['conf']['octavia']['ovn']['ovn_sb_connection']
for section, key, expected in [('database', 'connection', 'mariadb.openstack.svc.cluster.local'),
                             ('DEFAULT', 'transport_url', 'rabbitmq-genestack.openstack.svc.cluster.local')]:
    uri = urlsplit(config.get(section, key))
    assert uri.hostname == expected
    assert unquote(uri.username or '') == 'octavia'
    assert unquote(uri.password or '') == (private['endpoints']['oslo_db']['auth']['octavia']['password']
        if section == 'database' else rabbit['endpoints']['oslo_messaging']['auth']['octavia']['password'])
assert urlsplit(config.get('service_auth', 'auth_url')).hostname == 'keystone-api.openstack.svc.cluster.local'
assert config.get('service_auth', 'username') == 'octavia'
print('PASS: OVN-only, API + agent shared socket; DB/MQ/auth hosts and passwords match')
print('Jobs: ' + ', '.join(sorted(jobs)))
print('Files: ' + str(root) + '/{lab-values.yaml,post-render.py,rendered.yaml}')
print('Public API planned: https://octavia.lab.test:' + str(https))
print('NOT installed; render includes private Secrets: do not commit/send it')
