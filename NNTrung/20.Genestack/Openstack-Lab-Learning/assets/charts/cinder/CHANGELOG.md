# Release notes

## 2026.1.0-141

- Update Ceph images to Ubuntu Noble
- Add PVC support for the cinder-volume conversion directory. The
  ``/var/lib/cinder/conversion`` directory is used as a temporary workspace
  during image conversion operations (e.g., image-to-volume). When large
  images are processed frequently, the emptyDir backend can exhaust the
  node's root filesystem and cause disk pressure or pod eviction. Operators
  can now set ``conf.enable_conversion_pvc: true`` and
  ``manifests.pvc_conversion: true`` to mount this directory from a
  PersistentVolumeClaim and isolate conversion I/O onto a dedicated storage
  backend (e.g., Ceph RBD, NFS, local-path).
- Use a single dedicated client certificate (cinder-client) for all mutual TLS
  backend connections (MariaDB and RabbitMQ) instead of rendering separate
  certificates, and allow enabling mutual TLS to RabbitMQ independently via
  the tls.oslo_messaging value. The MariaDB client certificate secret was
  renamed from cinder-mariadb-client to cinder-client.
- Add an optional StatefulSet manifest for the cinder-volume service, gated
  by ``manifests.statefulset_volume`` (disabled by default). When enabled,
  the existing ``deployment_volume`` manifest is suppressed and each pod
  gets a stable, unique hostname (cinder-volume-0, cinder-volume-1, ...).
  If ``conf.cinder.DEFAULT.host`` is left empty, each pod uses its own pod
  name as the backend host, which is the supported way to run more than
  one cinder-volume replica (combine with ``[DEFAULT] cluster`` and a Tooz
  coordination backend for active/active). The static
  ``host: cinder-volume-worker`` default remains and is only safe with a
  single replica.
- Added ``bootstrap.script`` value to inject custom shell commands
  at the end of the cinder bootstrap process.
- Removed the unused non-admin database user secret ``cinder-db-user``. The
  service database connection string is generated from the ``oslo_db``
  endpoint definition and rendered directly into the service configuration
  file, so the dedicated user ``DB_CONNECTION`` secret was never mounted
  or referenced by any job or pod. The admin database secret used for
  ``ROOT_DB_CONNECTION`` is unaffected.
- Removed the unused ``endpoints.oslo_db.auth.admin.secret.tls`` and
  ``endpoints.oslo_messaging.auth.admin.secret.tls`` metadata.
- Use a dedicated client certificate when connecting to MariaDB over TLS
  instead of reusing the MariaDB server certificate on the client side. The
  MariaDB connection TLS is now gated on the `tls.oslo_db` value so it can be
  enabled independently of other TLS settings.
- Removed the trivial per-daemon start scripts. The daemon commands
  are now specified inline as the container ``command`` in the
  Deployment, DaemonSet and StatefulSet manifests, dropping the
  ConfigMap data entry and ``/tmp/*.sh`` volume mount for each.
- Point the cinder-api liveness probe at the uwsgi stats port instead of
  /healthcheck. /healthcheck is answered by the uwsgi request workers, and
  cinder-api runs a single worker, so a slow request failed the liveness
  probe and the pod was killed while it was still serving. The stats socket
  is served by the uwsgi master and answers regardless of worker load.
  Readiness keeps /healthcheck, which is the right signal for taking a busy
  replica out of rotation. Same convention as heat, placement, glance,
  barbican and nova.
- Run the cinder API under uwsgi only (remove the Apache httpd frontend).

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

- Add missing default glance identity endpoint for cinder.
- Add support for etcSources to db-sync job.
- Allow users to add additional sources to the Projected Volume that is mounted
  at /etc/cinder/cinder.conf.d/ so they may more easily override configs or provide
  additional configs for the various services in the chart.
- Update Ceph to Tentacle 20.2.0 and replaced image sources from docker.io/openstackhelm with quay.io/airshipit
- Add missing priority class and runtime class definition for cinder_db_purge
- Split out the OpenStack service account definitions from cinder.conf and into
  config snippets which are loaded at /etc/cinder/cinder.d/, which is automatically
  loaded by OSLO when loading the main cinder.conf. This makes it easier for users
  to use the regular config generation while supplying credentials out of band.
- Replaced uWSGI ``wsgi-file`` with ``module`` directive
  (``cinder.wsgi.api:application``) for OpenStack 2026.1 compatibility.
  The wsgi script entry points have been removed upstream in favor of
  direct module references.

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

## 2025.2.0

- Enable passing custom_job_annotations via values for specific Cinder jobs.
  This allows controlling Argo CD / Helm job behavior (e.g., sync-waves,
  hook policies) without modifying the chart templates directly.
- Add cronjob to purge old deleted database entries
- Fix cinder volume container permission to fix FailedToDropPrivileges issue.
- Unhardcode readiness/liveness probe parameters for cinder-api

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName

### Upgrade Notes

- Change the default volume v3 path to not include the tenant_id. The is the
  current recommended approach and has not been necessary since the Yoga release.

### Bug Fixes

- Some backends of cinder will write some temp data into the state_path
  so it should be something available to be written to for the pod.

## 2025.1.0

- Fix ingress resource generation

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency version to ">= 0.1.0"
- 0.1.2 Support service tokens to prevent long-running job failures
- 0.1.3 Support of external ceph backend
- 0.1.4 Enable iscsi to work correctly in cinder volume
- 0.1.5 Resolves mount issue with termination-log
- 0.1.6 Enable volume backup for iSCSI based volumes
- 0.1.7 Change Issuer to ClusterIssuer
- 0.1.8 Revert - Change Issuer to ClusterIssuer
- 0.1.9 Use HostToContainer mount propagation
- 0.1.10 Change Issuer to ClusterIssuer
- 0.1.11 Update RBAC apiVersion from /v1beta1 to /v1
- 0.1.12 Update volume type creation bootstrap logic
- 0.1.13 Add NFS cinder backup override
- 0.1.14 Add Multipathd support for ISCSI backed volumes
- 0.1.15 Fix the problem in hostNetwork mode
- 0.2.0 Remove support for releases before T
- 0.2.1 Fix the ceph pool creations for openstack services
- 0.2.2 Adding rabbitmq TLS logic
- 0.2.3 Mount rabbitmq TLS secret
- 0.2.4 Add Ussuri release support
- 0.2.5 Add volume QoS support
- 0.2.6 Added helm.sh/hook with value of post-install and post-upgrade
- 0.2.7 Add Victoria and Wallaby releases support
- 0.2.8 Add logic to bootstrap to handle upgrade timing issue
- 0.2.9 Mount rabbitmq TLS secret for audit usage cronjob
- 0.2.10 Helm 3 - Fix Job Labels
- 0.2.11 Update htk requirements repo
- 0.2.12 Remove cinder v1/v2 defaults
- 0.2.13 Upgrade default images to ussuri
- 0.2.14 Fix notifications
- 0.2.15 Remove glance registry
- 0.2.16 Enable taint toleration for Openstack services
- 0.2.17 Remove unsupported values overrides
- 0.2.18 Add helm hook in bootstrap job
- 0.2.19 Add volume types visibility (public/private)
- 0.2.20 Allow cinder v1/v2 endpoint creation if needed
- 0.2.21 Migrated CronJob resource to batch/v1 API version & PodDisruptionBudget to policy/v1
- 0.2.22 Add Xena and Yoga values overrides
- 0.2.23 Added OCI registry authentication
- 0.2.24 Fix conditional check for cinder.utils.has_ceph_backend template
- 0.2.25 Remove volumes unrelated with ceph backend from conditional volume list in cinder-volume deployment
- 0.2.26 Distinguish between port number of internal endpoint and binding port number
- 0.2.27 Support TLS endpoints
- 0.2.28 Use HTTP probe instead of TCP probe
- 0.2.29 Add SYS_ADMIN capability in cinder-volume
- 0.2.30 Specify a existing configmap name for external ceph configuration
- 0.2.31 Remove fixed node name from default values and add service cleaner cronjob
- 0.2.32 Revert "Remove fixed node name from default values and add service cleaner cronjob"
- 0.3.0 Remove support for Train and Ussuri
- 0.3.1 Change ceph-config-helper image tag
- 0.3.2 Remove default policy rules
- 0.3.3 Fix for creation endpoins and services when v1/v2 are disabled
- 0.3.4 Fix Helm hooks for storage bootstrap jobs
- 0.3.5 Add Nova endpoint details to support online volume resize
- 0.3.6 Fix ceph keyring placement for uppercased backends
- 0.3.7 Allow Ceph pools to use 1x replication
- 0.3.8 Update all Ceph images to Focal
- 0.3.9 Replace node-role.kubernetes.io/master with control-plane
- 0.3.10 Define service_type in keystone_authtoken to support application credentials with access rules
- 0.3.11 Add Zed overrides
- 0.3.12 Add 2023.1 overrides
- 0.3.13 Use service tokens
- 0.3.14 Add Ubuntu Jammy overrides
- 0.3.15 Add 2023.2 Ubuntu Jammy overrides
- 0.3.16 Update Ceph images to Jammy and Reef 18.2.1
- 0.3.17 Use uWSGI for API service
- 0.3.18 Enable custom annotations for Openstack pods
- 0.3.19 Add 2024.1 overrides
- 0.3.20 Add readiness probe initial delay
- 0.3.21 Enable custom annotations for Openstack secrets
- 0.3.22 Update images used by default
- 0.3.23 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.3.24 Fix volume type create to allow encrypt volume type
- 0.3.25 Add 2024.2 Ubuntu Jammy overrides
- 0.3.26 Mount /run/cryptsetup in cinder-volume container
- 0.3.27 Add support for using a tmpfs for cinder image conversion
- 0.3.28 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle
