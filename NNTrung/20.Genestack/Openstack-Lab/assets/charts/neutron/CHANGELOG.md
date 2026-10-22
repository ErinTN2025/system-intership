# Release notes

## 2026.1.0-142

- Replace the chart-native nginx TLS sidecar with the shared
  ``pod.extraContainers``/``pod.extraVolumes`` sidecar approach.
- Added nf_tables fallback for modprobe in the OVS agent init container.
  On kernels that have moved to nftables-only (e.g., 6.18.15+deb13-amd64
  on Debian Trixie), the ip6_tables module does not exist. The init
  container now falls back to modprobe nf_tables if ip6_tables fails,
  maintaining backward compatibility with older kernels while supporting
  newer nftables-only kernels.
- Enabled the uWSGI ``need-app`` option for ``neutron-server``. Without it
  uWSGI keeps running when it cannot import the WSGI application, logging
  ``no app loaded. going in full dynamic mode`` and answering every request
  with a plain-text HTTP 500 while still looking healthy to the container
  runtime, so the pod is never restarted. With ``lazy-apps`` enabled this
  can also affect only a subset of the workers, in which case the pod stays
  Ready and fails a fraction of the requests. The instance now exits
  instead, and Kubernetes restarts it with the usual backoff. Operators who
  prefer the previous behaviour can set ``need-app`` to ``false`` in their
  values overrides.
- limit envsubst by specifying the list of env variables to prevent it
  from substituting everything starting from $.
- Add the ``ovn-neutron-init`` container to the neutron ironic agent
  deployment and pass ``ovn.ini`` to the agent, so ``ovn_nb_connection`` is
  set rather than falling back to ``tcp:127.0.0.1:6641``.
- The ``neutron-rpc-server`` deployment now renders resource requests and
  limits. It referenced ``pod.resources.rpc_server``, which was never defined
  in ``values.yaml``, so the pod was created with no resources at all even
  when ``pod.resources.enabled`` was ``true``.
  
  It also resolves its entrypoint dependencies from
  ``dependencies.static.rpc_server`` instead of ``dependencies.static.server``.
  The ``rpc_server`` entry existed but nothing consumed it, so the pod waited
  on the ``neutron-ks-user`` and ``neutron-ks-endpoints`` jobs that it does
  not need.
- The ``neutron-ovn-agent`` and ``neutron-ovn-metadata-agent`` daemonsets now
  use their own ``images.tags.neutron_ovn_agent`` and
  ``images.tags.neutron_ovn_metadata`` tags instead of
  ``images.tags.neutron_metadata``, and ``neutron-ovn-metadata-agent`` reads
  its init container security context from
  ``pod.security_context.neutron_ovn_metadata_agent``. Previously overriding
  only the OVN ``runAsUser`` left the init container chowning the metadata
  proxy socket directory to the wrong UID.
  
  The first init container of each daemonset is renamed to
  ``neutron-ovn-agent-init`` and ``neutron-ovn-metadata-agent-init``, matching
  the names the AppArmor annotations already expected, and
  ``ovn-neutron-init`` is added to those lists. Operators setting
  ``pod.mandatory_access_control`` profiles for these pods must update the
  container keys.
- The following configs are computed from `.endpoints.compute_metadata.scheme.internal` unless populated:
  
  - `.conf.metadata_agent.DEFAULT.nova_metadata_protocol`
  - `.conf.ovn_agent.DEFAULT.nova_metadata_protocol`
  - `.conf.ovn_metadata_agent.DEFAULT.nova_metadata_protocol`
- Removed the unused non-admin database user secret ``neutron-db-user``. The
  service database connection string is generated from the ``oslo_db``
  endpoint definition and rendered directly into the service configuration
  file, so the dedicated user ``DB_CONNECTION`` secret was never mounted
  or referenced by any job or pod. The admin database secret used for
  ``ROOT_DB_CONNECTION`` is unaffected.
- The neutron-server readiness probe now targets the oslo.middleware
  ``/healthcheck`` endpoint (backed by ``disable_by_file``) instead of the
  API root ``/``. This routes the probe through a uWSGI worker and enables
  graceful draining: create ``/var/lib/neutron/healthcheck_disable`` to
  remove a pod from Service rotation without restarting it. The liveness
  probe is intentionally left on the uWSGI stats endpoint (port 1717), which
  is served by the master process, so a dependency outage cannot trigger a
  restart storm across neutron-server pods.
- Remove support for linuxbridge.
- The DHCP and L3 agent init containers now receive a container security
  context. Both daemonsets already referenced
  ``pod.security_context.neutron_{dhcp,l3}_agent.container.neutron_{dhcp,l3}_agent_init``,
  but the keys were absent from ``values.yaml``, so the init containers ran
  with no container-level context at all. They are now defined with
  ``readOnlyRootFilesystem: true``; unlike the metadata and OVN agent init
  containers these scripts do not chown anything, so they do not need
  ``runAsUser: 0``.
  
  The DHCP agent's ``ovn-neutron-init`` init container now also renders the
  resources and security context snippets, and is included in the AppArmor
  annotation list. Previously it was skipped entirely, so it had no resource
  requests or limits when ``pod.resources.enabled`` was set.
- Add a readiness probe to the neutron ironic agent. The agent casts its
  state and cannot detect that no neutron server RPC worker is consuming
  the report topic, so the new ``--check-neutron-server`` health probe mode
  calls ``has_alive_neutron_server`` on that topic instead.
- The neutron ironic agent now runs as a StatefulSet instead of a
  Deployment. The ironic-neutron-agent names its notification listener pool
  queue after its own hostname, which under a Deployment is the pod name and
  so changed on every rollout. Quorum queues cannot be declared
  ``auto_delete``, so each rollout left the previous pool queue behind. A
  stable hostname also keeps the agent's hash ring membership stable across
  restarts.
- A headless service named ``neutron-ironic-agent`` is rendered alongside
  the StatefulSet, under the same ``manifests.statefulset_ironic_agent``
  value, as its governing service. It publishes the per-ordinal DNS names so
  the FQDN the agent registers as its ``host`` resolves.
- ``pod.lifecycle.upgrades.statefulsets.pod_replacement_strategy`` is now
  defined, defaulting to ``RollingUpdate``, so the update strategy of the
  ironic agent StatefulSet can be overridden.
- Use a dedicated client certificate when connecting to MariaDB over TLS
  instead of reusing the MariaDB server certificate on the client side. The
  MariaDB connection TLS is now gated on the `tls.oslo_db` value so it can be
  enabled independently of other TLS settings.
- Use a single dedicated client certificate (neutron-client) for all mutual TLS
  backend connections (MariaDB and RabbitMQ) instead of rendering separate
  certificates, and allow enabling mutual TLS to RabbitMQ independently via
  the tls.oslo_messaging value. The MariaDB client certificate secret was
  renamed from neutron-mariadb-client to neutron-client.
- The ``neutron-ovn-vpn-agent`` daemonset now renders the custom pod
  annotations and AppArmor annotations that every other neutron daemonset
  already supported. Previously ``annotations.pod.default`` and
  ``annotations.pod.ovn_vpn_agent`` were silently dropped for this pod, and
  ``pod.mandatory_access_control`` profiles could not be applied to it at all.
- Removed the unused ``endpoints.oslo_db.auth.admin.secret.tls`` and
  ``endpoints.oslo_messaging.auth.admin.secret.tls`` metadata.
- Removed the trivial per-daemon start scripts. The daemon commands
  are now specified inline as the container ``command`` in the
  Deployment, DaemonSet and StatefulSet manifests, dropping the
  ConfigMap data entry and ``/tmp/*.sh`` volume mount for each.
- New chart value, `chown_ovsdb_sock`, has been added to allow operators to
  disable the chown of the OVS DB socket when using KubeOVN or other OVN
  deployed outside of OSH that might run as a different user.
- Added Deployments for the neutron-periodic-workers and
  neutron-ovn-maintenance-worker processes. When the Neutron API is served
  by a web server, as this chart does with uWSGI, upstream Neutron requires
  these as separate processes: neither the API process nor
  neutron-rpc-server runs the ML2 plugin periodic tasks or the ML2/OVN
  database maintenance task. Without them, those tasks were not running at
  all.
  
  The periodic worker is deployed when manifests.deployment_periodic_worker
  is enabled and conf.neutron.DEFAULT.core_plugin is ml2. The OVN
  maintenance worker is deployed when
  manifests.deployment_ovn_maintenance_worker is enabled and ovn is present
  in network.backend. Both default to true, so upgrading an existing ml2 or
  OVN deployment starts these pods.
  
  Each worker has its own images.tags, labels, dependencies, pod.replicas,
  pod.resources, pod.mounts, pod.etcSources, pod.security_context and
  pod.lifecycle.termination_grace_period entries under the periodic_worker /
  neutron_periodic_worker and ovn_maintenance_worker /
  neutron_ovn_maintenance_worker keys. The OVN maintenance worker is a
  single-process worker upstream and should not be scaled beyond one
  replica.

### New Features

- The ``helm-toolkit.manifests.certificates`` template now accepts an
  optional ``secretName`` parameter. When provided, it sets the name of the
  rendered cert-manager ``Certificate`` (both ``metadata.name`` and
  ``spec.secretName``) instead of deriving it from the endpoint's
  ``host_fqdn_override.default.tls.secretName``.
- Add support for neutron-ovn-agent.

### Upgrade Notes

- The charts no longer render ``Ingress`` resources, nor the auxiliary
  ``Service`` objects and TLS secrets that used to back them. Charts now
  deploy only the applications and their ClusterIP ``Service`` objects.
  Expose services outside the cluster by supplying the necessary objects
  through the ``.Values.extraObjects`` field, for example a Gateway API
  ``HTTPRoute`` (plus a ``BackendTLSPolicy`` for backend re-encryption) or,
  if preferred, an ``Ingress`` together with its ``Service``. Ready-to-use
  Gateway API examples are provided under
  ``values_overrides/<chart>/gateway.yaml``.
- The mTLS client certificate that each chart presents on outbound
  connections to MariaDB and RabbitMQ is now named after the chart-local
  value ``secrets.tls.client.<chart>`` rather than the shared
  ``endpoints.oslo_db.host_fqdn_override.default.tls.secretName``. This
  prevents a name collision for deployments whose values tooling renders
  endpoints from a single shared endpoint catalog, where the ``oslo_db``
  endpoint (and therefore its ``secretName``) is identical across every
  chart. The pod ``client-certs`` volume already references the same
  chart-local value, so the certificate and its mount remain in lockstep.
  No action is required for existing deployments: the default
  ``secrets.tls.client.<chart>`` value matches the previously rendered
  certificate name.
- Support for linuxbridge has been removed from neutron chart.
- The neutron ``manifests.deployment_ironic_agent`` value has been renamed
  to ``manifests.statefulset_ironic_agent``. Deployments that enabled the
  ironic agent must rename it in their overrides; the agent is not rendered
  at all if only the old name is set. The pod is recreated with an ordinal
  name (neutron-ironic-agent-0), so the previous Deployment and its
  ReplicaSets are removed on upgrade.

### API Changes

- Removed all ingress-related values from the charts: the
  ``manifests.ingress*``, ``manifests.service_ingress*`` and
  ``manifests.secret_ingress_tls`` toggles, the ``endpoints.ingress``
  controller endpoint and the ``network.<service>.ingress`` blocks. The
  now-unused ``helm-toolkit.manifests.ingress``,
  ``helm-toolkit.manifests.service_ingress`` and
  ``helm-toolkit.manifests.secret_ingress_tls`` helpers were removed as well.

### Bug Fixes

- Populate ``[cache] memcache_servers`` from the ``oslo_cache`` internal
  memcache endpoint for heat, neutron, trove, and zaqar when a cache section
  exists and ``memcache_servers`` has not already been set by user overrides.
  
  This brings these charts in line with other OpenStack-Helm services that
  already populate ``memcache_servers`` from the ``oslo_cache`` endpoint while
  keeping explicit overrides authoritative.
- Corrected ``rabbit_quorum_queues`` to ``rabbit_quorum_queue`` in every
  chart's ``values.yaml``. The oslo.messaging RabbitMQ driver only
  recognizes the singular option name (see
  `impl_rabbit.py <https://github.com/openstack/oslo.messaging/blob/b5593e2a733bf1ca86be8182f12a17d2d973fb5a/oslo_messaging/_drivers/impl_rabbit.py#L165>`_),
  so the plural form set by every chart since
  Change-Id ``I331e5e86744cbf935a1414399f0dc8e0ce76e4c0`` was silently
  ignored and quorum queues were never actually enabled via that setting.
- The ``neutron-periodic-worker`` and ``neutron-ovn-maintenance-worker``
  deployments now get the database connection when the neutron chart is
  deployed with the ``mariadb-crd`` overrides. That override stops
  generating the connection string into ``neutron.conf`` and instead
  projects the ``neutron-db-conn`` secret into the config directory of
  every workload that reads the database, but it listed only the server,
  the RPC server and the two db-sync jobs. The workers were added after
  the override and were never added to the list, so they started with no
  ``[database] connection`` at all and crash looped on
  ``CantStartEngineError: No sql_connection parameter is established``.
  
  Because neither worker declares a readiness probe, a crash looping pod
  reports its container ready during the brief window between a restart
  and the next crash, so ``helm osh wait-for-pods`` sampled it as healthy
  often enough that the mariadb-crd and mariadb-operator gates failed only
  intermittently.
- The readiness and liveness probes of the ``neutron-ovn-agent`` daemonset
  now check the agent instead of always succeeding. ``health-probe.py``
  selects its check from the configuration file name, and ``ovn_agent.ini``
  matched neither of the names it knew, so the OVN agent took the RPC branch.
  That branch does not apply to this agent, which serves no RPC and reports
  its liveness through the OVN southbound database, and it returned success
  without checking anything because the daemonset passes no
  ``--agent-queue-name``. A hung agent kept its pod Ready and was never
  restarted. ``ovn_agent.ini`` now takes the same unix domain socket check as
  ``ovn_metadata_agent.ini``.
  
  The check queries the metadata proxy socket, so it assumes the ``metadata``
  extension is enabled, as it is by default. Deployments that run the OVN
  agent with other extensions only should disable the probes under
  ``pod.probes.ovn_agent``.

## 2026.1.0

- Fix issue with etcSources where resources fails to apply if the list is empty.
- Use `ip add replace` instead of `ip addr add` in the init script to
  make it idempotent and avoid errors when the script tries to assign
  the same IP address to the interface on subsequent runs.
- Allow users to add additional sources to the Projected Volume that is mounted
  at /etc/neutron/neutron.conf.d/ so they may more easily override configs or provide
  additional configs for the various services in the chart. Ensure that the neutron
  chart always loads config overrides from /etc/neutron/neutron.conf.d
- Add support for etcSources to db-sync job.
- add raise_for_status method call to the livenessProbe command to properly
  raise an error when return code is 4xx (client error) or 5xx (server error)
- Update values_overrides for ovn. If OVN is used, network.backend needs to be ovn.
  There is no need to keep openvswitch as it adds OVS plugin related pod dependencies.
  daemonset_netns_cleanup_cron is also not required anymore with ovn.
- Add missing `--config-dir` option to `neutron-ovn-db-sync-util`.
- Added uwsgi start-time configuration to neutron-api-uwsgi section. The
  start-time parameter is set to "%t" (unix time at instance startup) and is
  used by ML2/OVN for creating OVN hash ring registers per worker. This
  configuration is mandatory for proper ML2/OVN operation. See the Neutron
  documentation for more details:
  https://docs.openstack.org/neutron/latest/admin/config-wsgi.html
- Replaced uWSGI ``wsgi-file`` with ``module`` directive
  (``neutron.wsgi.api:application``) for OpenStack 2026.1 compatibility.
  The wsgi script entry points have been removed upstream in favor of
  direct module references.
- Support for tungstenfabric has been removed.
- When enabling the OVN backend, don't fail to start with the default
  connection setup to OVN NB and SB. A feature change was made allowing users
  to override these connections but it did not preserve the default.

### New Features

- Update default ingress classes and annotations for charts to make them implementation
  agnostic. They used to be nginx specific because we always used ingress-nginx as the most
  common choice. Ingress-nginx is deprecated and will become unmaintained in Feb/2026.
  
  Now for all test jobs we use HAProxy Ingress as the default implementation. However any
  other implementation can be used as far as it suppports annotations similar to
  'nginx.ingress.kubernetes.io/rewrite-target' or 'haproxy.org/path-rewrite' which are
  used in many OpenStack-Helm charts.
- Added an extraObjects list to every chart to allow for adding extra
  Kubernetes objects along side the chart without modifying the chart.
  It has the added benefit of using Helm's built in templating so
  you are able to utilize other values supplied to the chart.
- Added emptyDir mounted at /var/lock and set OSLO_LOCK_PATH env var to
  this path for oslo.concurrency support in all OpenStack services.

### Upgrade Notes

- Support for Helm 2 has been removed by removal of the helm3_hook value across all charts.
  It is no longer possible to set helm3_hook to False to support Helm 2.

### Bug Fixes

- Fixed OVN metadata agent DaemonSet resource configuration inconsistency.
  All containers now consistently reference pod.resources.agent.ovn_metadata.

## 2025.2.0

- Fix neutron ironic agent fail to start with missing host information.
- Use psutil.net_connections to iterate over tcp connections
  during health check. The psutil.connections is still available
  but deprecated.
- Do not skip children processes when counting established connections
  because after eventlet removal plain threads are used.
- Added the ability to configure custom OVN Northbound (ovn_nb_connection) and
  Southbound (ovn_sb_connection) connection strings
  (e.g., for deployments using Kube-OVN or external OVN databases).
  By default, the chart continues to use the in-cluster service environment
  This change provides flexibility to support both default in-cluster OVN and
  custom/external OVN backends seamlessly.
- Create multiple Keystone service accounts to access to
  other Openstack APIs
- Neutron OVN now runs under **uWSGI**, and the legacy **eventlet** support
  has been removed. The ``neutron-server`` binary is no longer provided.
  Updated configuration references to reflect the switch to uWSGI
  for Neutron OVN.
- Add required OVN VPN configuration files to Neutron server so VPN
  features behave as expected. The Neutron server receives RPC calls from the
  Neutron OVN VPN agent and executes VPN operations. Therefore, the VPN
  configuration must be present on the Neutron server.
- Fix ovn sync db cron job to use helm-toolkit snippets when
  specifying runtime and priority classes.
- Add interface name parameter for DPDK configs
- Fix OVN support in neutron DHCP.
- Fix port duplication in neutron server deployment
- Add new cron job for neutron ovn db sync that runs evey 5 mins by default.
  This could be use as log alert if any part out of sync.
  Or it can be use as automatic repair method to prevent
  OVN DB got modified and failed it's purpose.
  This cron job is default disabled.
  Set `.Values.manifests.cron_job_ovn_db_sync_repair` to
  `true` to enable the cronjob.
  The sync mode for the cronjob is default only for check sync status.
  Set `.Values.jobs.ovn_db_sync_repair.sync_mode` to `repair` for enable
  automatic repair and sync OVN DB from Neutron DB.

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName
- Split out the OpenStack service account definitions from neutron.conf and into
  config snippets which are loaded at /etc/neutron/neutron.d/, which is automatically
  loaded by OSLO when loading the main neutron.conf. This makes it easier for users
  to use the regular config generation while supplying credentials out of band.

### Bug Fixes

- Since 0e7fe77f49 neutron-ironic-agent has had an invalid volumes spec. Fix the
  spec so the agent can run.

## 2025.1.0

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency version to ">= 0.1.0"
- 0.1.2 fixes tls issue
- 0.1.3 Update neutron to use Nginx apparmor profile
- 0.1.4 Pass ovs agent config to dhcp agent
- 0.1.5 Add missing flags to nginx container in neutron chart
- 0.1.6 Use HostToContainer mountPropagation
- 0.1.7 Change Issuer to ClusterIssuer
- 0.1.8 Revert Change Issuer to ClusterIssuer
- 0.1.9 Update ovs agent to support host/label overrides
- 0.1.10 Change Issuer to ClusterIssuer
- 0.1.11 Added the helm.sh/hook, helm.sh/hook-weight annotations
- 0.1.12 Removed "name" parameter from Rally tests
- 0.2.0 Remove support for releases before T
- 0.2.1 Adding rabbitmq TLS logic
- 0.2.2 Use policies in yaml format
- 0.2.3 Mount rabbitmq TLS secret
- 0.2.4 Add Ussuri release support
- 0.2.5 Use rootwrap daemon
- 0.2.6 Fix neutron agent-init script
- 0.2.7 Made dnsmasq.conf overridable in configmap-bin
- 0.2.8 Add Victoria and Wallaby releases support
- 0.2.9 Add option to disable helm.sh/hook annotations
- 0.2.10 Update htk requirements repo
- 0.2.11 Improve health probe logging
- 0.2.12 Fix infinite recursion deadlock on netns cleanup cron
- 0.2.13 Enable taint toleration for Openstack services
- 0.2.14 Migrate IP from bridge for auto_bridge_add
- 0.2.15 Remove unsupported values overrides
- 0.2.16 Remove usage of six
- 0.2.17 Migrated PodDisruptionBudget resource to policy/v1 API version
- 0.2.18 Updated naming for subchart compatibility
- 0.2.19 Added qdhcp NS host validation for deleting wrong namespaces.
- 0.2.20 Add Xena and Yoga values overrides
- 0.2.21 Fix for qdhcp NS host validation for deleting wrong namespaces.
- 0.2.22 Fix /run/xtables.lock may be a directory
- 0.2.23 Add neutron_netns_cleanup_cron release image override, so that the respective release image is used
- 0.2.24 Added OCI registry authentication
- 0.2.25 Support TLS endpoints
- 0.2.26 Use HTTP probe instead of TCP probe
- 0.2.27 Distinguish between port number of internal endpoint and binding port number
- 0.3.0 Remove support for Train and Ussuri
- 0.3.1 Remove default policy rules
- 0.3.2 Use correct labels for ovs which uses one daemonset for ovs-db and ovs-vswitchd
- 0.3.3 Add OVN Support
- 0.3.4 Replace node-role.kubernetes.io/master with control-plane
- 0.3.5 Fix health probe for OVN metadata agent
- 0.3.6 Fix the issue that ovn metadata not work in muti-node enviroment
- 0.3.7 Sync neutron db to ovn nb db when neutron-server start
- 0.3.8 Define service_type in keystone_authtoken to support application credentials with access rules
- 0.3.9 Extend neutron liveness probe with readiness probe
- 0.3.10 Configure keystone authentication credentials for placement
- 0.3.11 Add Zed overrides
- 0.3.12 Update oslo_messaging_RPCClient and get_rpc_transport
- 0.3.13 Remove duplicated argument when running a liveness check
- 0.3.14 Add 2023.1 overrides
- 0.3.15 Add asap2 support
- 0.3.16 Use service tokens
- 0.3.17 Add exec probe timeouts
- 0.3.18 Improve OVN support
- 0.3.19 Fix getting IP for interface when there are multiple IPs assigned
- 0.3.20 Add Ubuntu Jammy overrides
- 0.3.21 Run native netns cleanup
- 0.3.22 Add BGP Dragent support for running dragent agents as daemonsets
- 0.3.23 Fix start function template
- 0.3.24 Add 2023.2 Ubuntu Jammy overrides
- 0.3.25 Fix ovs member support for readiness
- 0.3.26 Fix ovs options to allow multiple options
- 0.3.27 Move old overrides from the tools directory
- 0.3.28 Fix ovn for slow enviroment
- 0.3.29 Disable DVR for OVN floating ip
- 0.3.30 Fix designate auth url
- 0.3.31 FIX ovn-metadata-agent mountPropagation overrides by parent directory
- 0.3.32 Update dpdk override
- 0.3.33 Make sure trust on command is applied to avoid race-condition with ovs-dpdk
- 0.3.34 Update metadata endpoint
- 0.3.35 Do not attach non-existing interfaces to br-ex bridge for OVS agent
- 0.3.36 Enable custom annotations for Openstack pods
- 0.3.37 Proper chown /run/openvswitch/db.sock under OVN
- 0.3.38 Add 2024.1 overrides
- 0.3.39 Ensure that the script handles cases where the PID file exists but is empty or does not contain the expected data structure.
- 0.3.40 Fix ovs bridge creation in mappings for DPDK
- 0.3.41 Enable custom annotations for Openstack secrets
- 0.3.42 Update images used by default
- 0.3.43 Switch neutron to uWSGI
- 0.3.44 Add OVN VPNaas support
- 0.3.45 Fix ironic/baremetal authentication
- 0.3.46 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.3.47 Add service role to the Neutron user
- 0.3.48 Add 2024.2 Ubuntu Jammy overrides
- 0.3.49 Add node_selector_* for OVN VPN agent
- 0.3.50 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle
