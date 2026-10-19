# Release notes

## 2026.1.0-141

- Update Ceph images to Ubuntu Noble
- Update Ceph to Tentacle 20.2.4
- Store generated /etc/ceph content for the libvirt pod in an emptyDir volume
  instead of a hostPath. This avoids propagating Ceph config and keyring bind
  mounts into the host mount namespace during libvirt pod restarts.

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

- Add .Values.libvirt.extraContainers hook to make it possible to
  add additional containers to libvirt daemonset, e.g. for monitoring
  purposes. Also move exporter container to values_overrides.
- Update Ceph to Tentacle 20.2.1
- Update Ceph to Tentacle 20.2.0 and replaced image sources from docker.io/openstackhelm with quay.io/airshipit
- Keeping vnc ca/key/cert in /tmp so in case container (not pod) restarts
  it could copy them one again to the proper place. This allows to handle
  libvirt crashes properly without restarting libvirt pods.

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
- Added ability to configure libvirt hooks.

### Bug Fixes

- Added readiness and liveness probes for the libvirt-exporter sidecar container.

## 2025.1.0

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency version to ">= 0.1.0"
- 0.1.2 Setup libvirt SSL
- 0.1.3 Create override for external ceph cinder backend
- 0.1.4 Set unix socket auth method as none
- 0.1.5 Use full image ref for docker official images
- 0.1.6 Enhancement to enable probes override from values.yaml
- 0.1.7 Add libvirt overrides for Victoria and Wallaby
- 0.1.8 Update htk requirements
- 0.1.9 Exec libvirt instead of forking from bash
- 0.1.10 Enable taint toleration for Openstack services jobs
- 0.1.11 Remove unused overrides and update default image
- 0.1.12 Add libvirt exporter as a sidecar
- 0.1.13 Added OCI registry authentication
- 0.1.14 Remove use of exec in libvirt.sh
- 0.1.15 Add support for libvirt to connect to external ceph without any local ceph present
- 0.1.16 Update all Ceph images to Focal
- 0.1.17 Add ovn.yaml values_override, remove dependency from neutron-ovs-agent module
- 0.1.18 Replace node-role.kubernetes.io/master with control-plane
- 0.1.19 Set kubernetes cgroup value equal kubepods.slice to fit systemd cgroup driver
- 0.1.20 Update Ceph to 17.2.6
- 0.1.21 Disable libvirt cgroup functionality for cgroup-v2
- 0.1.22 Set targeted dependency of libvirt with ovn networking backend
- 0.1.23 Add support for enabling vencrypt
- 0.1.24 Include HOSTNAME_FQDN for certificates
- 0.1.25 Add 2023.2 Ubuntu Jammy overrides
- 0.1.26 Update Rook to 1.12.5 and Ceph to 18.2.0
- 0.1.27 Add watch verb to vencrypt cert-manager Role
- 0.1.28 Update Ceph images to Jammy and Reef 18.2.1
- 0.1.29 Update Ceph images to patched 18.2.2 and restore debian-reef repo
- 0.1.30 Add 2024.1 overrides
- 0.1.31 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.1.32 Enable a flag to parse Libvirt Nova metadata in libvirt exporter
- 0.1.33 Handle cgroupv2 correctly
- 0.1.34 Remove hugepages creation test
- 0.1.35 Allow to initialize virtualization modules
- 0.1.36 Allow to generate dynamic config options
- 0.1.37 Make readiness probes more tiny
- 0.1.38 Implement daemonset overrides for libvirt
- 0.1.39 Add 2023.1 overrides for Ubuntu Focal and Jammy
- 0.1.40 Add 2024.2 overrides
- 0.1.41 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.
