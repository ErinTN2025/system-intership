ARG BASE_IMAGE=quay.io/airshipit/horizon@sha256:61919ada1502dc698047489c496bb1873e02c239fdb9d6e278e35d6243bb812a
FROM ${BASE_IMAGE}
USER 0:0

# Chuẩn bị pip trong đúng virtualenv của Horizon.
RUN /var/lib/openstack/bin/python3 -c \
      "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', '/tmp/get-pip.py')" \
 && /var/lib/openstack/bin/python3 /tmp/get-pip.py \
 && rm /tmp/get-pip.py

# Lưu versions, tránh giữ các đường dẫn nguồn đã bị dọn trong image nền.
RUN /var/lib/openstack/bin/python3 -m pip list --format=freeze > /tmp/horizon-constraints.txt \
 && /var/lib/openstack/bin/python3 -m pip install --no-cache-dir \
      -c /tmp/horizon-constraints.txt octavia-dashboard==16.0.0 \
 && /var/lib/openstack/bin/python3 -m pip check \
 && /var/lib/openstack/bin/python3 -c "from importlib.metadata import version; from importlib.util import find_spec; print('Horizon:', version('horizon')); print('Octavia Dashboard:', version('octavia-dashboard')); assert find_spec('octavia_dashboard')" \
 && rm /tmp/horizon-constraints.txt

# Script của chart chown theo tên tài khoản horizon.
RUN getent passwd horizon >/dev/null || useradd --system --user-group \
      --home-dir /var/lib/horizon --no-create-home --shell /usr/sbin/nologin horizon
