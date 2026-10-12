# Release notes

## 2026.1.0-141

- The horizon dashboard keeps running under Apache httpd (mod_wsgi), now
  serving plain HTTP on the dashboard ``web`` port; TLS is no longer
  terminated by Apache but by the nginx sidecar in front of it. Apache is
  retained (rather than switching to uwsgi) because it also serves the
  dashboard's static assets. Django trusts the sidecar's
  ``X-Forwarded-Proto`` header via ``SECURE_PROXY_SSL_HEADER``.
- Rename the MariaDB client certificate secret from horizon-mariadb-client to
  horizon-client. It is now the chart's single client certificate for mutual TLS
  backend connections.
- Add support for configuring the SECONDARY_ENDPOINT_TYPE option.
  This enables deployers to select the secondary endpoint type.
  By default, SECONDARY_ENDPOINT_TYPE is set to publicURL.
- Use a dedicated client certificate when connecting to MariaDB over TLS
  instead of reusing the MariaDB server certificate on the client side. The
  MariaDB connection TLS is now gated on the `tls.oslo_db` value so it can be
  enabled independently of other TLS settings.
- Removed the unused ``endpoints.oslo_db.auth.admin.secret.tls`` metadata.
- Add support for configuring DEFAULT_SERVICE_REGIONS.
  This enables deployers to configure the DEFAULT_SERVICE_REGIONS option.
  By default, DEFAULT_SERVICE_REGIONS is empty.
- The Horizon chart now allows SECURE_PROXY_ADDR_HEADER to be configured
  through values.yaml. This lets deployments choose the trusted proxy
  header used for the remote client address while keeping
  HTTP_X_FORWARDED_FOR as the default.

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

- Fix missing job annotation support from values.yaml on the db-sync job.

## 2025.1.0

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency version to ">= 0.1.0"
- 0.1.2 To avoid wrong version check for mysqlclient
- 0.1.3 Modify Password validator related settings in Horizon
- 0.1.4 Change Issuer to ClusterIssuer
- 0.1.5 Revert - Change Issuer to ClusterIssuer
- 0.1.6 Change Issuer to ClusterIssuer
- 0.1.7 Update glance default policy values
- 0.1.8 Implement "CSRF_COOKIE_HTTPONLY" option support in horizon
- 0.2.0 Remove support for releases before T
- 0.2.1 Make python script PEP8 compliant
- 0.2.2 Use policies in yaml format
- 0.2.3 Add openstack_enable_password_retrieve variable in value
- 0.2.4 Fix OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT value
- 0.2.5 Add Ussuri release support
- 0.2.6 Add Victoria and Wallaby releases support
- 0.2.7 Fix OPENSTACK_ENABLE_PASSWORD_RETRIEVE value
- 0.2.8 Add default polices
- 0.2.9 Removed default policy in chart in favor of default policy in code
- 0.2.10 Helm 3 - Fix Job Labels
- 0.2.11 Update htk requirements repo
- 0.2.12 Support both json and yaml RBAC Policy Format
- 0.2.13 Add container infra api version in values
- 0.2.14 Add OPENSTACK_ENDPOINT_TYPE value
- 0.2.15 Add local_settings.d
- 0.2.16 Fix container-infra value
- 0.2.17 Add custom logo
- 0.2.18 Enable taint toleration for Openstack services
- 0.2.19 Remove unsupported value overrides
- 0.2.20 Add SHOW_OPENRC_FILE value
- 0.2.21 Add helm hook annotations in db-sync and db-init jobs
- 0.2.22 Migrated PodDisruptionBudget resource to policy/v1 API version
- 0.2.23 Add Xena and Yoga value overrides
- 0.2.24 Remove blank lines in logo configmap
- 0.2.25 Added OCI registry authentication
- 0.2.26 Support SSL identity endpoint
- 0.3.0 Remove support for Train and Ussuri
- 0.3.1 Fix container infra api version in values
- 0.3.2 Update mysql client version to 1.4.0
- 0.3.3 Update mysql client version in django.wsgi also
- 0.3.4 Add readiness probe timeout
- 0.3.5 Replace node-role.kubernetes.io/master with control-plane
- 0.3.6 Fix container infra api version parsing
- 0.3.7 Update the script to add extra panels
- 0.3.8 Fix horizon tolerations
- 0.3.9 Add Zed overrides
- 0.3.10 Add 2023.1 overrides
- 0.3.11 Rollout when logo configmap is changed
- 0.3.12 Add Ubuntu Jammy overrides
- 0.3.13 Make selenium v4 syntax optional
- 0.3.14 Add 2023.2 Ubuntu Jammy overrides
- 0.3.15 Update osh-selenium image used by default
- 0.3.16 Add support for custom panels
- 0.3.17 Set ingress annotation proxy-body-size=300m by default
- 0.3.18 Enable custom annotations for Openstack pods
- 0.3.19 Add 2024.1 overrides
- 0.3.20 Enable custom annotations for Openstack secrets
- 0.3.21 Update images used by default
- 0.3.22 Align with 2024.1 requirements
- 0.3.23 Use global wsgi subinterpreter
- 0.3.24 Use base64 values for custom logo
- 0.3.25 Implement "CSRF_TRUSTED_ORIGINS" option support in horizon
- 0.3.26 Fix templating of CSRF_TRUSTED_ORIGINS
- 0.3.27 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.3.28 Add WEBSSO_KEYSTONE_URL value
- 0.3.29 Add 2024.2 Ubuntu Jammy overrides
- 0.3.30 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle
