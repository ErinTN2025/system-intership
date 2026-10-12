ARG BASE_IMAGE=quay.io/airshipit/horizon:2026.1-ubuntu_noble
FROM ${BASE_IMAGE}
ARG RUNTIME_USER=root
USER root
# Preserve installed dependency versions instead of upgrading Horizon/Django.
RUN /var/lib/openstack/bin/python3 -m pip freeze > /tmp/horizon-constraints.txt \
 && /var/lib/openstack/bin/python3 -m pip install --no-cache-dir \
      -c /tmp/horizon-constraints.txt octavia-dashboard==17.0.0 \
 && /var/lib/openstack/bin/python3 -m pip check \
 && /var/lib/openstack/bin/python3 -c "from importlib.util import find_spec; assert find_spec('octavia_dashboard')" \
 && rm /tmp/horizon-constraints.txt
USER ${RUNTIME_USER}
