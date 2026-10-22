# Release notes

## 2026.1.0-141

- Run the nova-api (osapi) and nova-metadata APIs under uwsgi only (remove
  the Apache httpd frontend).
- Set terminationGracePeriodSeconds to 180s for nova-compute,
  nova-conductor, and nova-scheduler pods. Nova Gazpacho (2026.1)
  introduced graceful shutdown support with a default timeout of 180s.
  Previously, these pods used the K8s default of 30s, which could
  result in SIGKILL before Nova completes its graceful shutdown,
  potentially leaving VMs in ERROR state during live migrations or
  other long-running operations.
- The oslo_messaging secret no longer renders a ``TRANSPORT_URL`` key; like
  the other charts it now exposes only ``RABBITMQ_CONNECTION``.
- The database connection configuration has been reworked. The invalid
  ``[cell0_database]`` section is no longer written to ``nova.conf`` (it was
  never a real Nova config group). The API and cell1 database connections
  remain in ``nova.conf`` as the ``[api_database]`` and ``[database]``
  sections. The cell0 connection is treated as data (it lives in the API
  database via the cell mapping) and is delivered as the
  ``nova-db-cell0-user`` secret rather than a config section.
- db-init/db-drop initialize the API and cell1 databases from the
  ``[api_database]`` and ``[database]`` sections of ``nova.conf`` (``oslo``
  init type) and cell0 from the secret (``secret`` init type). The db-sync
  job receives the cell0 connection as the ``DB_CONNECTION_CELL0`` environment
  variable; cell1 mapping defaults its transport URL and database connection
  from config rather than dedicated environment variables.
- The database endpoints and their secrets have been renamed to reflect
  nova's cell layout. The API database endpoint ``oslo_db_api`` was renamed
  to ``oslo_db`` (``/nova``), and the former ``oslo_db`` (cell1's main
  database) was renamed to ``oslo_db_cell1`` (``/nova_cell1``).
  ``oslo_db_cell0`` (``/nova_cell0``) is unchanged. Their secrets follow the
  same renaming (for example ``nova-db-api-*`` becomes ``nova-db-*`` and the
  former ``nova-db-*`` becomes ``nova-db-cell1-*``).
- Removed the trivial per-daemon start scripts. The daemon commands
  are now specified inline as the container ``command`` in the
  Deployment, DaemonSet and StatefulSet manifests, dropping the
  ConfigMap data entry and ``/tmp/*.sh`` volume mount for each.
- Update Ceph images to Ubuntu Noble
- Remove support for linuxbridge.
- Removed the unused non-admin database user secret ``nova-db-api-user``. The
  service database connection string is generated from the ``oslo_db``
  endpoint definition and rendered directly into the service configuration
  file, so the dedicated user ``DB_CONNECTION`` secret was never mounted
  or referenced by any job or pod. The admin database secret used for
  ``ROOT_DB_CONNECTION`` is unaffected.
- Use a dedicated client certificate when connecting to MariaDB over TLS
  instead of reusing the MariaDB server certificate on the client side. The
  MariaDB connection TLS is now gated on the `tls.oslo_db` value so it can be
  enabled independently of other TLS settings.
- Use a single dedicated client certificate (nova-client) for all mutual TLS
  backend connections (MariaDB and RabbitMQ) instead of rendering separate
  certificates, and allow enabling mutual TLS to RabbitMQ independently via
  the tls.oslo_messaging value. The MariaDB client certificate secret was
  renamed from nova-mariadb-client to nova-client.
- Removed the unused ``endpoints.oslo_db.auth.admin.secret.tls`` and
  ``endpoints.oslo_messaging.auth.admin.secret.tls`` metadata.
- Point the nova-api-osapi and nova-api-metadata liveness probes at the
  uwsgi stats port instead of the API port. The API port is answered by the
  uwsgi request workers, so one slow request failed the liveness probe and
  the pod was killed while still serving it. The stats socket is served by
  the uwsgi master and answers regardless of worker load. Readiness keeps
  the API port, which is the right signal for taking a busy replica out of
  rotation. Same convention as heat, placement, glance and barbican.

### New Features

- The ``helm-toolkit.manifests.certificates`` template now accepts an
  optional ``secretName`` parameter. When provided, it sets the name of the
  rendered cert-manager ``Certificate`` (both ``metadata.name`` and
  ``spec.secretName``) instead of deriving it from the endpoint's
  ``host_fqdn_override.default.tls.secretName``.

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
- Support for linuxbridge has been removed from nova chart.

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

## 2026.1.0

- Update Ceph to Tentacle 20.2.0 and replaced image sources from docker.io/openstackhelm with quay.io/airshipit
- Support for tungstenfabric has been removed.
- Update values_overrides for ovn. If OVN is used, network.backend needs to be ovn.
  There is no need to keep openvswitch as it adds OVS plugin related pod dependencies.
- Fix issue with etcSources where resources fails to apply if the list is empty.
- Remove `memcache_servers` and `memcache_secret_key` from `[ironic]` section.
  It was found that nothing consumes those configurations.
- Update the wait computes default bootstrap script. Now it is going to print timestamps
  while waiting for the computes to be ready. This is going to be handy during debugging.
  Also the typo has been fixed that prevented the script to fail after timeout.
- Update dependencies for the bootstrap job. It must start after cell setup job is finished
  because it looks up for hypervisors which are discovered by the cell setup job.
- Add ability to disable nova-ssh Secret with `.manifests.secret_ssh`.
- Allows users to set custom 'host' values for nova conductor and scheduler
  services. This may be useful for kubernetes users, where new deploys of
  scheduler and conductor use the pod names, leaaving stale compute service entries
  which are eventually cleaned by the nova-service-cleaner job.
  Ref: https://docs.openstack.org/nova/latest/configuration/config.html#DEFAULT.host
- health-probe.py now supports reading database connections from /etc/nova/nova.conf.d.
- Replaced uWSGI ``wsgi-file`` with ``module`` directive for OpenStack
  2026.1 compatibility. Nova API now uses
  ``nova.wsgi.osapi_compute:application`` and Nova metadata API uses
  ``nova.wsgi.metadata:application``. The wsgi script entry points have
  been removed upstream in favor of direct module references.
- The ironic Keystone user for Nova will not be created anymore unless `manifests.statefulset_compute_ironic` is set to True.
- Add missing nova-etc-snippets for cell-setup cronjob.

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
- The `.manifests.configmap_etc` value no longer control the nova-ssh Secret,
  use `.manifests.secret_ssh` instead.

## 2025.2.0

- Fix Cinder auth config in values.yaml
- Fix mount path /etc/nova/nova.conf.d for novncproxy deployment
- Includes custom job annotations for nova-bootstrap chart. Other jobs
  include the custom job annotations, but they were missing for the
  nova-bootstrap job.
- Ensure that the nova chart always loads config overrides from /etc/nova/nova.conf.d
- Refactored the flavor creation logic in the nova bootstrap script to simplify
  and generalize flavor definitions using dynamic key/value iteration. This makes
  the chart more maintainable and flexible for various flavor configurations.
- Adds support to UUID deployment-provisioning configuration
- Allow users to add additional sources to the Projected Volume that is mounted
  at /etc/nova/nova.conf.d/ so they may more easily override configs or provide
  additional configs for the various services in the chart.

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName
- Split out the OpenStack service account definitions from nova.conf and into
  config snippets which are loaded at /etc/nova/nova.d/, which is automatically
  loaded by OSLO when loading the main nova.conf. This makes it easier for users
  to use the regular config generation while supplying credentials out of band.

### Upgrade Notes

- Change the default volume v3 path to not include the tenant_id. The is the
  current recommended approach and has not been necessary since the Yoga release.
- Change the default volume v2.1 path to not include the tenant_id. The is the
  current recommended approach and has not been necessary since the Mitaka release.

## 2025.1.0

- Add custom annotations to the nova-cell-setup job
- Add serialproxy support

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency version to ">= 0.1.0"
- 0.1.2 Add ssh to Nova compute
- 0.1.3 Establish Nova and Placement dependencies
- 0.1.4 Remove deprecated os_region_name for placement
- 0.1.5 Enable hostIPC
- 0.1.6 Swap SSH key names to reflect the correct key
- 0.1.7 Use HostToContainer mountPropagation
- 0.1.8 Change Issuer to ClusterIssuer
- 0.1.9 Revert "Change Issuer to ClusterIssuer"
- 0.1.10 Use HostToContainer mount propagation
- 0.1.11 Secure libvirt connection from using 127.0.0.1 to use unix socket
- 0.1.12 Update RBAC apiVersion from /v1beta1 to /v1
- 0.1.13 Change Issuer to ClusterIssuer
- 0.1.14 BUG for deploying multiple compute nodes
- 0.1.15 Mount /dev/pts in Nova compute container
- 0.1.16 Use first IP address for migration
- 0.1.17 Add multipathd support for ISCSI backed volume VMs
- 0.1.18 Fix the nova-compute-ironic label issue
- 0.1.19 Host resource scale adjustment about ironic
- 0.2.0 Remove support for releases before T
- 0.2.1 Remove unnecessary +x permission on gotpl files
- 0.2.2 Adding rabbitmq TLS logic
- 0.2.3 Replace deprecated configuration ``[vnc]/vncserver_proxyclient_address``
- 0.2.4 Mount rabbitmq TLS secret
- 0.2.5 Set reasonable default probe timeouts
- 0.2.6 Added cronJob with script for archive deleted rows which cleanup databases
- 0.2.7 Add Ussuri release support
- 0.2.8 Fix the cron archive_deleted_rows bash script for before and max-rows values
- 0.2.9 Add image clean up to rally test
- 0.2.10 Add tls cert mounting to nova-novnc
- 0.2.11 Add Victoria and Wallaby releases support
- 0.2.12 Bootstrap flavor creation efficiencies
- 0.2.13 Add missing 'runlock' hostMount when enable_scsi
- 0.2.14 Use helm.sh/hook annotations for jobs
- 0.2.15 Fix archive-deleted-rows for enabling date command as value for before option
- 0.2.16 Remove the policy document in values file
- 0.2.17 Fix disablement of helm.sh/hook for Helm v2
- 0.2.18 Give service time to restore
- 0.2.19 Define service cleaner sleep time
- 0.2.20 Update script to true of grep does get anything.
- 0.2.21 Helm 3 - Fix Job Labels
- 0.2.22 Update htk requirements repo
- 0.2.23 Add option to enable extra wait for cell-setup-init
- 0.2.24 Fix nova-bootstrap job labels
- 0.2.25 Add check for compute nodes
- 0.2.26 Fix _ssh-init.sh.tpl to copy the ssh keys to the user on the security context
- 0.2.27 Add tls1.2 minimum version to tls overrides
- 0.2.28 Move ssl_minimum_version to console section
- 0.2.29 Remove ssh-config
- 0.2.30 Improve health probe logging
- 0.2.31 Update oslo messaging get_transport
- 0.2.32 Host of ironic compute service equals pod name
- 0.2.33 Cleanup old releases
- 0.2.34 Remove consoleauth in nova
- 0.2.35 Enable taint toleration for Openstack services
- 0.2.36 Support TLS endpoints
- 0.2.37 Remove nova-placement
- 0.2.38 Update nova image defaults
- 0.2.39 Migrated CronJob resource to batch/v1 API version & PodDisruptionBudget to policy/v1
- 0.2.40 Updated naming for subchart compatibility
- 0.2.41 Add Xena and Yoga values overrides
- 0.2.42 Add missing configuration ``[vnc]/novncproxy_host``
- 0.2.43 Added OCI registry authentication
- 0.2.44 Distinguish between port number of internal endpoint and binding port number
- 0.2.45 Support TLS endpoints for metadata-api
- 0.2.46 Use HTTP probe instead of TCP probe
- 0.2.47 Remove list agents rally test
- 0.3.0 Remove support for Train and Ussuri
- 0.3.1 Added backoffLimit for bootstrap job
- 0.3.2 Remove un-used configs for Nova
- 0.3.3 Update all Ceph images to Focal
- 0.3.4 Add OVN values_override, disable dependency to ovn-agent and vif configs for ovn
- 0.3.5 Replace node-role.kubernetes.io/master with control-plane
- 0.3.6 Fix VNC access issues
- 0.3.7 Fix live migration without DNS resolution
- 0.3.8 Fix missing privilege separation directory for nova compute ssh
- 0.3.9 Fix typo in spice proxy deployment
- 0.3.10 Define service_type in keystone_authtoken to support application credentials with access rules
- 0.3.11 Update get_notification_transport
- 0.3.12 Update oslo_messaging_RPCClient
- 0.3.13 Add Zed overrides
- 0.3.14 Add 2023.1 overrides
- 0.3.15 Ensure that the health check script handles cases where the PID file exists but is empty or does not contain the expected data structure.
- 0.3.16 Use service tokens
- 0.3.17 Set targeted dependency of nova-compute with ovn networking backend
- 0.3.18 Fix nova ssh keys permission
- 0.3.19 Add support for enabling vencrypt
- 0.3.20 Add cinder auth config
- 0.3.21 Update health probe script considering ovsdb_connection config
- 0.3.22 Replace deprecated configuration vncserver_proxyclient_address to server_proxyclient_address
- 0.3.23 Add Ubuntu Jammy overrides
- 0.3.24 Create a certificate for novnc vencrypt separately
- 0.3.25 Add IP addresses search control flag
- 0.3.26 Improve cinder authentication support
- 0.3.27 Add 2023.2 Ubuntu Jammy overrides
- 0.3.28 Add ability to define extra command(s) for the nova cell setup job
- 0.3.29 Add ability to define extra command(s) for the nova service cleaner job
- 0.3.30 Add the conditional statement for log_config_append
- 0.3.31 Add getting LISTEN IP for CIDR
- 0.3.32 Set the startupProbe for nova-compute
- 0.3.33 Add job to create 'vms' pool
- 0.3.34 Add public endpoints for the spiceproxy
- 0.3.35 Use directory mount for vencrypt certificates
- 0.3.36 Update Ceph images to Jammy and Reef 18.2.1
- 0.3.37 Use metadata_listen_port instead of metadata_port
- 0.3.38 Using uWSGI
- 0.3.39 Enable custom annotations for Openstack pods
- 0.3.40 Add 2024.1 overrides
- 0.3.41 Enable custom annotations for Openstack secrets
- 0.3.42 Update images used by default
- 0.3.43 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.3.44 Add DPDK overrides
- 0.3.45 Add configuration for nova-scheduler
- 0.3.46 Add 2024.2 Ubuntu Jammy overrides
- 0.3.47 Use nova-compute.conf in nova-compute-ironic
- 0.3.48 Fix typo in archive_deleted_rows script
- 0.3.49 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle
