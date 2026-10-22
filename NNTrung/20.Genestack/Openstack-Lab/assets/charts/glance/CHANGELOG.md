# Release notes

## 2026.1.0-141

- Replace the chart-native nginx TLS sidecar with the shared
  ``pod.extraContainers``/``pod.extraVolumes`` sidecar approach.
- Removed the trivial per-daemon start scripts. The daemon commands
  are now specified inline as the container ``command`` in the
  Deployment, DaemonSet and StatefulSet manifests, dropping the
  ConfigMap data entry and ``/tmp/*.sh`` volume mount for each.
- Removed the unused non-admin database user secret ``glance-db-user``. The
  service database connection string is generated from the ``oslo_db``
  endpoint definition and rendered directly into the service configuration
  file, so the dedicated user ``DB_CONNECTION`` secret was never mounted
  or referenced by any job or pod. The admin database secret used for
  ``ROOT_DB_CONNECTION`` is unaffected.
- Update Ceph images to Ubuntu Noble
- Added a persistent volume claim (``glance-tmp``) for the Glance staging
  directory (``/var/lib/glance/tmp``). This directory holds data for
  ``os_glance_tasks_store`` and ``os_glance_staging_store`` which are used
  during image import. Previously this was backed by an emptyDir which
  meant staged data was lost on pod restart and was not shared across pods,
  breaking image imports when running more than one API replica. When
  ``storage: pvc`` is set and ``manifests.pvc_staging`` is enabled (the
  default), a dedicated PVC is created and an init container
  (``glance-tmp-perms``) ensures correct ownership. The PVC size, storage
  class, and access modes are configurable via the new ``volume_staging``
  values key.
- Use a dedicated client certificate when connecting to MariaDB over TLS
  instead of reusing the MariaDB server certificate on the client side. The
  MariaDB connection TLS is now gated on the `tls.oslo_db` value so it can be
  enabled independently of other TLS settings.
- Use a single dedicated client certificate (glance-client) for all mutual TLS
  backend connections (MariaDB and RabbitMQ) instead of rendering separate
  certificates, and allow enabling mutual TLS to RabbitMQ independently via
  the tls.oslo_messaging value. The MariaDB client certificate secret was
  renamed from glance-mariadb-client to glance-client.
- limit envsubst by specifying the list of env variables to prevent it
  from substituting everything starting from $.
- Removed the unused ``endpoints.oslo_db.auth.admin.secret.tls`` and
  ``endpoints.oslo_messaging.auth.admin.secret.tls`` metadata.
- Point the glance-api liveness probe at the uwsgi stats port instead of
  /healthcheck. /healthcheck is answered by the request workers, so a
  worker pool saturated by long image uploads failed the liveness probe
  and the pod was killed with its uploads in flight. Readiness keeps
  using /healthcheck, which is the right signal for taking a busy
  replica out of rotation. Same convention as heat and placement.

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

- Add support for etcSources to db-sync job.
- Restructured paste configuration for OpenStack 2026.1 compatibility.
  The healthcheck middleware is now deployed as an app instead of a filter
  (``app:healthcheck`` with ``paste.app_factory``) to comply with the
  oslo.middleware HealthcheckMiddleware change that no longer supports
  filter mode. Paste pipelines have been converted to composite applications
  using ``glance.api:root_app_factory`` and ``glance.api:pipeline_factory``.
  Removed deprecated Glance v1 API references, audit filter, and deprecated
  osprofiler options. Replaced uWSGI ``wsgi-file`` with ``module``
  directive (``glance.wsgi.api:application``).
- Add support for etcSources to glance-metadefs-load job.
- Update Ceph to Tentacle 20.2.0 and replaced image sources from docker.io/openstackhelm with quay.io/airshipit
- add raise_for_status method call to the livenessProbe command to properly
  raise an error when return code is 4xx (client error) or 5xx (server error)
- Allow users to add additional sources to the Projected Volume that is mounted
  at /etc/glance/glance.conf.d/ so they may more easily override configs or provide
  additional configs for the various services in the chart.

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

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName

### Bug Fixes

- Fix missing job annotation support from values.yaml on the clean, metadefs-load,
  and storage-init jobs.

## 2025.1.0

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency to >= 0.1.0
- 0.1.2 Change issuer to clusterissuer
- 0.1.3 Revert - Change issuer to clusterissuer
- 0.1.4 Update RBAC apiVersion from /v1beta1 to /v1
- 0.1.5 Change Issuer to ClusterIssuer
- 0.1.6 Update glance default policy values
- 0.1.7 Update storage init script with cacert
- 0.1.8 Update glance default policy values
- 0.2.0 Remove support for releases before T
- 0.2.1 Fix the ceph pool creations for openstack services
- 0.2.2 Adding rabbitmq TLS logic
- 0.2.3 Use policies in yaml format
- 0.2.4 Mount rabbitmq TLS secret
- 0.2.5 Add Ussuri release support
- 0.2.6 Add Victoria and Wallaby releases support
- 0.2.7 Added helm.sh/hook for the jobs
- 0.2.8 Helm 3 - Fix Job Labels
- 0.2.9 Helm 3 - Fix More Job Labels
- 0.2.10 Update htk requirements repo
- 0.3.0 Remove glance registry
- 0.3.1 Enable taint toleration for Openstack services
- 0.3.2 Decrease terminationGracePeriodSeconds on glance-api
- 0.3.3 Update naming for subchart compatibility
- 0.3.4 Change image default version to wallaby
- 0.3.5 Migrated PodDisruptionBudget resource to policy/v1 API version
- 0.3.6 Add Xena and Yoga values overrides
- 0.3.7 Fix glance-etc template changing due to comment and whitespace between install and first upgrade
- 0.3.8 Added OCI registry authentication
- 0.3.9 Support TLS endpoints
- 0.3.10 Distinguish between port number of internal endpoint and binding port number
- 0.3.11 Use HTTP probe instead of TCP probe
- 0.3.12 Add support for using Cinder as backend
- 0.4.0 Remove support for Train and Ussuri
- 0.4.1 Remove default policy rules
- 0.4.2 Allow Ceph pools to use 1x replication
- 0.4.3 Update all Ceph images to Focal
- 0.4.4 Replace node-role.kubernetes.io/master with control-plane
- 0.4.5 Fix wrong configFile path in glance bootstrap container.
- 0.4.6 Define service_type in keystone_authtoken to support application credentials with access rules
- 0.4.7 Add Zed overrides
- 0.4.8 Add 2023.1 overrides
- 0.4.9 Use service tokens
- 0.4.10 Add exec probe timeouts
- 0.4.11 Bring liveness/readiness params out to values.yaml
- 0.4.12 Add flag `keep_pvc` to allows set helm resource-policy for glance-images PVC to keep.
- 0.4.13 Add Ubuntu Jammy overrides
- 0.4.14 Bump Cirros version to 0.6.2
- 0.4.15 Add 2023.2 Ubuntu Jammy overrides
- 0.4.16 Use --region option to prevent OS_SWIFT_ENDPOINT_PREFIX is broken in storage-init.sh
- 0.4.17 Update Ceph images to Jammy and Reef 18.2.1
- 0.4.18 Enable custom annotations for Openstack pods
- 0.4.19 Add 2024.1 overrides
- 0.4.20 Add readiness probe initial delay
- 0.4.21 Use uWSGI
- 0.4.22 Enable custom annotations for Openstack secrets
- 0.4.23 Update images used by default
- 0.4.24 Do not attach backend pvc to storage init pod
- 0.4.25 Allow customisation of pvc storage accessMode so we can run multiple api pods
- 0.4.26 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.5.0 Remove deprecated config options `stores` and `default_store`
- 0.5.1 Add 2024.2 Ubuntu Jammy overrides
- 0.5.2 Fix HTTP healthcheck URLs for Kubernetes probes
- 0.5.3 Add override for downloading Ubuntu image
- 0.5.4 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle
