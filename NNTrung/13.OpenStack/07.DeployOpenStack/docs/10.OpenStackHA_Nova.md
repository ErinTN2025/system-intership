# GIAI ĐOẠN 6 — PLACEMENT + NOVA (Compute) HA, EPHEMERAL DISK TRÊN CEPH

> **Tiền đề:** Phase 5 xanh, Glance + Ceph RBD chạy. Test B failover controller01 đã pass —
> Galera/RabbitMQ/HAProxy/Keystone/Glance đều HA thật. Pool `vms` đã tạo ở Phase 4.5.
> **Phạm vi:**
> - Placement API trên 3 controller (port 8778)
> - Nova control plane (`nova-api`, `nova-scheduler`, `nova-conductor`, `nova-novncproxy`)
>   trên 3 controller
> - `nova-compute` + libvirt + KVM trên `compute01/02/03`
> - Ephemeral disk của VM lưu trong pool `vms` Ceph (CoW clone từ pool `images`)
> **Mục tiêu:** `openstack compute service list` thấy đủ 7 service up (3 controller × 3 dịch
> vụ + 3 compute × 1 dịch vụ + scheduler×3 + conductor×3), `nova-status upgrade check` 3
> dấu tick. **Chưa boot được VM full** vì Neutron chưa có (Phase 7) — chỉ verify đến mức
> compute node lên + cell discovery work.

---

## 0. KIẾN TRÚC NOVA + CEPH (đọc 5 phút)

**Nova = "bộ điều phối VM".** Khi user gõ `openstack server create`, dòng đời 1 request:

```
client → nova-api (8774) → nova-scheduler (chọn compute node) → nova-conductor (orchestrator)
       → nova-compute (chạy trên compute node đích) → libvirt → qemu-kvm → VM up
```

**5 thành phần Nova phải nắm:**

| Tên | Vai trò | Chạy ở đâu | Port |
|---|---|---|---|
| nova-api | REST API entrypoint | 3 controller | 8774 |
| nova-scheduler | Chọn compute node nào nhận VM mới | 3 controller | (RabbitMQ) |
| nova-conductor | Trung gian DB cho compute (compute KHÔNG nói DB trực tiếp) | 3 controller | (RabbitMQ) |
| nova-novncproxy | Proxy console VNC từ trình duyệt → compute | 3 controller | 6080 |
| nova-compute | Daemon trên hypervisor, gọi libvirt | 3 compute node | (RabbitMQ) |

**Placement** là service **tách riêng** (từ Stein trở đi). Giữ "kho tài nguyên": mỗi compute
node là 1 "resource provider" với VCPU/MEMORY/DISK. Scheduler hỏi Placement "ai còn 2 vCPU +
4GB RAM" → trả về danh sách candidate.

→ Phải dựng Placement TRƯỚC Nova. Placement gần như clone Keystone về kiến trúc HA (Apache
mod_wsgi + DB + endpoint).

### Ceph integration

**Nova ephemeral disk = đĩa boot của VM**, sống và chết cùng VM. Mặc định lưu file qcow2 ở
local disk của compute node. Khi backend là **Ceph RBD pool `vms`**:

1. VM tạo từ image `cirros-0.6.2` (đang ở pool `images` Ceph).
2. Nova-compute KHÔNG copy bytes image. Nó **CoW snapshot** trong pool images → tạo image mới
   trong pool `vms` reference snapshot đó.
3. VM boot, ghi → chỉ ghi vào image vms (snapshot images bất biến).
4. Tạo VM 20GB từ image 20MB chỉ tốn vài giây + vài MB metadata. Đây là "siêu năng lực" lớn
   nhất của Ceph+OpenStack.

Để CoW chạy được, image Glance phải **format raw** (không phải qcow2). Cirros mặc định qcow2 —
sẽ phải re-upload ở Phase 6, sẽ làm trong mục 10.

### libvirt secret

Libvirt cần biết cephx key để mount RBD. **Không thể chỉ đường file keyring cho libvirt** —
libvirt giữ key dạng "secret" trong store nội bộ (XML + virsh secret-define/set-value). Mỗi
compute node có 1 secret UUID (giống nhau giữa 3 node để dễ quản lý), giá trị = base64 key của
`client.cinder`.

### Vì sao dùng `client.cinder` chung (chưa đến Phase 8 Cinder)?

Convention Ceph: 1 user `client.cinder` chia sẻ caps `volumes + vms + read-only images` cho cả
Nova ephemeral lẫn Cinder volume. Lý do: 1 VM có thể vừa có ephemeral disk (pool `vms`) vừa
attach Cinder volume (pool `volumes`) — libvirt cần 1 secret để truy cập cả 2. Tạo `client.nova`
riêng sẽ phải thêm secret thứ 2, phức tạp không cần thiết.

→ Phase 6 tạo `client.cinder` đầy đủ caps. Phase 8 (Cinder) tái sử dụng.

---

## 1. TẠO CEPH USER `client.cinder` (trên deployer)

```bash
# trên deployer
sudo ceph auth get-or-create client.cinder \
  mon 'profile rbd' \
  osd 'profile rbd pool=volumes, profile rbd pool=vms, profile rbd-read-only pool=images' \
  -o /tmp/ceph.client.cinder.keyring

sudo cat /tmp/ceph.client.cinder.keyring
sudo ceph auth get client.cinder
```

Mong đợi caps:
```
caps mon = "profile rbd"
caps osd = "profile rbd pool=volumes, profile rbd pool=vms, profile rbd-read-only pool=images"
```

> `rbd-read-only pool=images` cực kỳ quan trọng cho CoW. Nếu để `rbd` thường, Nova có thể vô
> tình ghi đè image Glance — thảm hoạ.

---

## 2. PHÂN PHỐI `ceph.conf` + `cinder.keyring` SANG CONTROLLERS + COMPUTES

```bash
# trên deployer
for h in controller01 controller02 controller03 compute01 compute02 compute03; do
  ssh $h 'sudo mkdir -p /etc/ceph'
  sudo scp /etc/ceph/ceph.conf root@$h:/etc/ceph/ceph.conf
  sudo scp /tmp/ceph.client.cinder.keyring root@$h:/etc/ceph/ceph.client.cinder.keyring
done

# xoá file tạm
sudo rm /tmp/ceph.client.cinder.keyring
```

Verify:
```bash
ssh compute01 'sudo ls -l /etc/ceph/'
```

---

## 3. PLACEMENT TRÊN 3 CONTROLLER

### 3.1. DB

```bash
ssh controller01 "sudo mariadb <<'EOF'
CREATE DATABASE placement;
CREATE USER 'placement'@'%' IDENTIFIED BY 'PLACEMENT_DBPASS';
GRANT ALL PRIVILEGES ON placement.* TO 'placement'@'%';
FLUSH PRIVILEGES;
EOF"
```

### 3.2. Keystone user + service + endpoint

```bash
# trên deployer
source ~/admin-openrc

openstack user create --domain default --password PLACEMENT_PASS placement
openstack role add --project service --user placement admin

openstack service create --name placement --description "Placement API" placement

openstack endpoint create --region RegionOne placement public   http://192.168.70.120:8778
openstack endpoint create --region RegionOne placement internal http://192.168.70.120:8778
openstack endpoint create --region RegionOne placement admin    http://192.168.70.120:8778
```

### 3.3. Cài + cấu hình trên 3 controller

```bash
for h in controller01 controller02 controller03; do
  ssh $h 'sudo apt update && sudo apt -y install placement-api python3-osc-placement'
done
```

Ghi đè `/etc/placement/placement.conf` trên **TỪNG controller** (xài tee + heredoc, **không
nano**):

```bash
# Mẫu cho controller01 — đổi IP cho 02/03
ssh controller01 "sudo tee /etc/placement/placement.conf > /dev/null <<'EOF'
[DEFAULT]
[api]
auth_strategy = keystone

[placement_database]
connection = mysql+pymysql://placement:PLACEMENT_DBPASS@192.168.70.120/placement
max_retries = -1

[keystone_authtoken]
auth_url = http://192.168.70.120:5000/v3
memcached_servers = 192.168.70.122:11211,192.168.70.127:11211,192.168.70.119:11211
auth_type = password
project_domain_name = Default
user_domain_name = Default
project_name = service
username = placement
password = PLACEMENT_PASS
EOF"
ssh controller01 "sudo chown root:placement /etc/placement/placement.conf && sudo chmod 0640 /etc/placement/placement.conf"
```

Lặp y hệt cho controller02, controller03 (cùng nội dung, không có IP node trong file này — DB
qua VIP, không cần `bind_host`).

### 3.4. Override Apache để bind đúng IP node

Lý do giống Keystone (Phase 4): Apache mặc định `Listen 8778` wildcard → chiếm cổng VIP.

```bash
# trên controller01 — IP_NODE=192.168.70.122
ssh controller01 "sudo tee /etc/apache2/sites-available/placement-api.conf > /dev/null <<'EOF'
Listen 192.168.70.122:8778

<VirtualHost 192.168.70.122:8778>
    WSGIDaemonProcess placement-api processes=3 threads=1 user=placement group=placement display-name=%{GROUP}
    WSGIProcessGroup placement-api
    WSGIScriptAlias / /usr/bin/placement-api
    WSGIApplicationGroup %{GLOBAL}
    WSGIPassAuthorization On
    ErrorLog /var/log/apache2/placement-api.log
    CustomLog /var/log/apache2/placement-api_access.log combined

    <Directory /usr/bin>
        Require all granted
    </Directory>
</VirtualHost>
EOF"
```

Lặp cho controller02 (`.127`), controller03 (`.119`).

### 3.5. Sync DB + restart Apache

```bash
ssh controller01 'sudo -u placement placement-manage db sync'

for h in controller01 controller02 controller03; do
  ssh $h 'sudo systemctl restart apache2 && sudo ss -lntp | grep 8778'
done
# mong đợi mỗi node thấy Apache nghe IP_NODE:8778
```

### 3.6. HAProxy listen placement

```bash
for h in controller01 controller02 controller03; do
  ssh $h "sudo tee -a /etc/haproxy/haproxy.cfg > /dev/null <<'EOF'

# === Placement API ===
listen placement_api
    bind 192.168.70.120:8778
    mode tcp
    balance roundrobin
    option tcp-check
    tcp-check connect
    server controller01 192.168.70.122:8778 check inter 2s rise 2 fall 3
    server controller02 192.168.70.127:8778 check inter 2s rise 2 fall 3
    server controller03 192.168.70.119:8778 check inter 2s rise 2 fall 3
EOF"
  ssh $h 'sudo haproxy -c -f /etc/haproxy/haproxy.cfg && sudo systemctl reload haproxy'
done
```

### 3.7. Verify Placement

```bash
# trên deployer
openstack endpoint list --service placement   # 3 endpoint xanh
openstack --os-placement-api-version 1.2 resource class list | head -5
# mong đợi liệt kê các resource class: VCPU, MEMORY_MB, DISK_GB, ...
```

![altimage](../images/Screenshot_33.png)

---

## 4. NOVA CONTROLLER — DB + KEYSTONE

### 4.1. Ba database

Nova có 3 DB (đặc thù từ cell_v2 architecture):
- `nova_api` — global state (flavor, quota, host aggregate)
- `nova_cell0` — VM "lạc trôi" (chưa schedule được)
- `nova` — state thật của cell1 (instance, block_device_mapping)

```bash
ssh controller01 "sudo mariadb <<'EOF'
CREATE DATABASE nova_api;
CREATE DATABASE nova;
CREATE DATABASE nova_cell0;
CREATE USER 'nova'@'%' IDENTIFIED BY 'NOVA_DBPASS';
GRANT ALL PRIVILEGES ON nova_api.* TO 'nova'@'%';
GRANT ALL PRIVILEGES ON nova.* TO 'nova'@'%';
GRANT ALL PRIVILEGES ON nova_cell0.* TO 'nova'@'%';
FLUSH PRIVILEGES;
EOF"
```

### 4.2. Keystone user + service + endpoint

```bash
# trên deployer
source ~/admin-openrc

openstack user create --domain default --password NOVA_PASS nova
openstack role add --project service --user nova admin

openstack service create --name nova --description "OpenStack Compute" compute

openstack endpoint create --region RegionOne compute public   http://192.168.70.120:8774/v2.1
openstack endpoint create --region RegionOne compute internal http://192.168.70.120:8774/v2.1
openstack endpoint create --region RegionOne compute admin    http://192.168.70.120:8774/v2.1
```

---

## 5. NOVA CONTROLLER — CÀI + CẤU HÌNH (3 controller)

```bash
for h in controller01 controller02 controller03; do
  ssh $h '
    sudo apt update
    sudo apt -y install nova-api nova-conductor nova-scheduler nova-novncproxy
  '
done
```

### 5.1. `/etc/nova/nova.conf` — mẫu cho controller01 (đổi IP cho 02/03)

```bash
ssh controller01 "sudo tee /etc/nova/nova.conf > /dev/null <<'EOF'
[DEFAULT]
my_ip = 192.168.70.119
state_path = /var/lib/nova
transport_url = rabbit://openstack:RABBIT_PASS@controller01:5672,openstack:RABBIT_PASS@controller02:5672,openstack:RABBIT_PASS@controller03:5672

[api]
auth_strategy = keystone

[api_database]
connection = mysql+pymysql://nova:NOVA_DBPASS@192.168.70.120/nova_api
max_retries = -1

[database]
connection = mysql+pymysql://nova:NOVA_DBPASS@192.168.70.120/nova
max_retries = -1

[keystone_authtoken]
www_authenticate_uri = http://192.168.70.120:5000/
auth_url = http://192.168.70.120:5000/
memcached_servers = 192.168.70.122:11211,192.168.70.127:11211,192.168.70.119:11211
auth_type = password
project_domain_name = Default
user_domain_name = Default
project_name = service
username = nova
password = NOVA_PASS

[service_user]
send_service_user_token = true
auth_url = http://192.168.70.120:5000/
auth_strategy = keystone
auth_type = password
project_domain_name = Default
user_domain_name = Default
project_name = service
username = nova
password = NOVA_PASS

[placement]
region_name = RegionOne
project_domain_name = Default
project_name = service
auth_type = password
user_domain_name = Default
auth_url = http://192.168.70.120:5000/v3
username = placement
password = PLACEMENT_PASS

[glance]
api_servers = http://192.168.70.120:9292

[oslo_concurrency]
lock_path = /var/lib/nova/tmp

[vnc]
enabled = true
server_listen = 192.168.70.119
server_proxyclient_address = 192.168.70.119
novncproxy_host = 192.168.70.119
novncproxy_port = 6080
novncproxy_base_url = http://192.168.70.120:6080/vnc_auto.html

[neutron]
# Sẽ điền ở Phase 7 — tạm chừa
auth_url = http://192.168.70.120:5000
auth_type = password
project_domain_name = Default
user_domain_name = Default
region_name = RegionOne
project_name = service
username = neutron
password = NEUTRON_PASS
service_metadata_proxy = true
metadata_proxy_shared_secret = METADATA_SECRET

[wsgi]
api_paste_config = /etc/nova/api-paste.ini
EOF"

ssh controller01 "sudo chown root:nova /etc/nova/nova.conf && sudo chmod 0640 /etc/nova/nova.conf"
```

> **Lặp y hệt cho controller02 (`my_ip=.127`, `server_listen=.127`, `server_proxyclient_address=.127`,
> `novncproxy_host=.127`) và controller03 (`.119`).** 4 chỗ phải đổi IP cho mỗi node, không
> được copy nguyên xi.

> `NEUTRON_PASS` và `METADATA_SECRET` chưa dùng đến (Phase 7) nhưng cứ đặt sẵn placeholder để
> nova-api không kêu. Có thể đặt giá trị giả `PLACEHOLDER` lúc này, Phase 7 sẽ thay.

### 5.2. Override nova-api Apache (giống Placement)

Trên Ubuntu UCA, `nova-api` mặc định cũng chạy qua Apache mod_wsgi. Phải override Listen:

```bash
# controller01
ssh controller01 "sudo tee /etc/apache2/sites-available/nova-api.conf > /dev/null <<'EOF'
Listen 192.168.70.127:8774

<VirtualHost 192.168.70.127:8774>
    WSGIDaemonProcess nova-api processes=3 threads=1 user=nova group=nova display-name=%{GROUP}
    WSGIProcessGroup nova-api
    WSGIScriptAlias / /usr/bin/nova-api-wsgi
    WSGIApplicationGroup %{GLOBAL}
    WSGIPassAuthorization On
    ErrorLog /var/log/apache2/nova-api.log
    CustomLog /var/log/apache2/nova-api_access.log combined

    <Directory /usr/bin>
        Require all granted
    </Directory>
</VirtualHost>
EOF"
ssh controller01 'sudo a2ensite nova-api && sudo systemctl reload apache2'
```

Lặp cho controller02 (`.127`), controller03 (`.119`).

#### Cấu hình nova-api standalone bind IP node

Ubuntu UCA 2025.1 ship `nova-api` thành **systemd service standalone** (không qua Apache).
Mặc định bind `0.0.0.0:8774` wildcard → xung đột với HAProxy VIP. Phải override bind:

Thêm vào `[DEFAULT]` của `/etc/nova/nova.conf` trên TỪNG controller (đổi IP):
```ini
osapi_compute_listen = 192.168.70.122   # IP node
osapi_compute_listen_port = 8774
metadata_listen = 192.168.70.122
metadata_listen_port = 8775
```

```bash
for h in controller01 controller02 controller03; do
  ssh $h 'sudo systemctl restart nova-api && sudo systemctl reload haproxy'
done

# Verify
for h in controller01 controller02 controller03; do
  echo "=== $h ==="
  ssh $h 'sudo ss -lntp | grep -E "8774|8778|5000"'
done
```

![altimage](../images/Screenshot_34.png)

Verify Apache KHÔNG có vhost nova-api (nếu lỡ tạo theo guide cũ, disable):
```bash
sudo a2dissite nova-api 2>/dev/null
sudo systemctl reload apache2
```


> Nếu Ubuntu UCA của bạn cấu hình nova-api thành systemd service riêng (không qua Apache),
> bỏ bước này và sửa `[DEFAULT]` thêm `osapi_compute_listen = 192.168.70.122` + `osapi_compute_listen_port = 8774`.
> Verify bằng `systemctl status nova-api`: thấy `loaded` = systemd service, không thấy =
> Apache mod_wsgi. Phổ biến nhất 2025.1 là Apache.

### 5.3. Sync DB + tạo cell

```bash
# CHỈ trên controller01 — Galera đồng bộ về 02/03
ssh controller01 '
  sudo -u nova nova-manage api_db sync
  sudo -u nova nova-manage cell_v2 map_cell0 --database_connection mysql+pymysql://nova:NOVA_DBPASS@192.168.70.120/nova_cell0
  sudo -u nova nova-manage cell_v2 create_cell --name=cell1 --verbose
  sudo -u nova nova-manage db sync
  sudo -u nova nova-manage cell_v2 list_cells
'
```

> Nhớ thay `NOVA_DBPASS` thật trong câu lệnh `map_cell0` (không lấy từ config).

Mong đợi `cell_v2 list_cells` ra 2 cell: `cell0` (gốc DB nova_cell0) và `cell1` (gốc DB nova,
transport_url rabbitmq).

### 5.4. Start service trên 3 controller

```bash
for h in controller01 controller02 controller03; do
  ssh $h '
    sudo systemctl restart apache2 nova-scheduler nova-conductor nova-novncproxy
    sudo systemctl enable apache2 nova-scheduler nova-conductor nova-novncproxy
  '
done

# verify port
for h in controller01 controller02 controller03; do
  echo "=== $h ==="
  ssh $h 'sudo ss -lntp | grep -E "8774|6080"'
done
```

![altimage](../images/Screenshot_35.png)

Mong đợi mỗi node có 8774 (apache nova-api) + 6080 (nova-novncproxy) nghe IP_NODE.

### 5.5. HAProxy nova-api + novncproxy

```bash
for h in controller01 controller02 controller03; do
  ssh $h "sudo tee -a /etc/haproxy/haproxy.cfg > /dev/null <<'EOF'

# === Nova API ===
listen nova_api
    bind 192.168.70.120:8774
    mode tcp
    balance roundrobin
    option tcp-check
    tcp-check connect
    server controller01 192.168.70.122:8774 check inter 2s rise 2 fall 3
    server controller02 192.168.70.127:8774 check inter 2s rise 2 fall 3
    server controller03 192.168.70.119:8774 check inter 2s rise 2 fall 3

# === Nova novncproxy ===
listen nova_novncproxy
    bind 192.168.70.120:6080
    mode tcp
    balance source
    option tcp-check
    tcp-check connect
    server controller01 192.168.70.122:6080 check inter 2s rise 2 fall 3
    server controller02 192.168.70.127:6080 check inter 2s rise 2 fall 3
    server controller03 192.168.70.119:6080 check inter 2s rise 2 fall 3
EOF"
  ssh $h 'sudo haproxy -c -f /etc/haproxy/haproxy.cfg && sudo systemctl reload haproxy'
done
```

> `balance source` cho novncproxy: VNC websocket cần "sticky" — client kết nối lần đầu sang
> node nào thì duy trì sang node đó, không bị token VNC mismatch.

---

## 6. NOVA-COMPUTE TRÊN 3 COMPUTE NODE

### 6.1. Kiểm tra hardware-assisted virt (KVM hay QEMU)

```bash
for h in compute01 compute02 compute03; do
  echo "=== $h ==="
  ssh $h 'egrep -c "(vmx|svm)" /proc/cpuinfo'
done
```

- Output > 0 = nested virt OK → dùng `virt_type = kvm` (nhanh, native).
- Output = 0 = không có → dùng `virt_type = qemu` (emulation, chậm hơn ~10x).

Cloud cho VM thường không có nested virt mặc định — chuẩn bị tinh thần dùng qemu. Lab này:
**dùng qemu cho an toàn**. Nếu test sau thấy hỗ trợ thì đổi.

### 6.2. Cài gói

```bash
for h in compute01 compute02 compute03; do
  ssh $h '
    sudo apt update
    sudo apt -y install nova-compute python3-rbd python3-rados
  '
done
```

> `nova-compute` Ubuntu package tự kéo `qemu-kvm` + `libvirt-daemon-system`. `python3-rbd` +
> `python3-rados` cần thiết để libvirt + nova nói chuyện với Ceph.


### Nếu ở đây bạn lỡ apt instll trên controller thì sẽ khá là nguy hiểm
#### Bước 1: Diagnose tác hại đã xảy ra
```bash
# Xem nova-compute đã đăng ký controllers vào cluster chưa
openstack compute service list --service nova-compute
ssh controller01 'sudo -u nova nova-manage cell_v2 list_hosts --cell_name=cell1'
```
Nếu output 1 (compute service list) có dòng nova-compute ở controller01/02/03 → cần xoá khỏi cluster DB. Nếu chỉ có 3 compute01/02/03 thì controllers chưa đăng ký, nhẹ nhõm hơn.
#### Bước 2: Gỡ `nova-compute` khỏi 3 controller
```bash
for h in controller01 controller02 controller03; do
  echo "=== $h ==="
  # Stop + disable daemon trước
  ssh $h 'sudo systemctl stop nova-compute 2>/dev/null; sudo systemctl disable nova-compute 2>/dev/null'
  
  # Purge package (purge = xoá luôn config thừa nếu có)
  ssh $h 'sudo apt -y purge nova-compute nova-compute-kvm nova-compute-libvirt 2>&1 | tail -3'
done

# Dọn dependency thừa (libvirt-daemon, qemu-kvm... mà controller không cần)
# CHÚ Ý: kiểm tra trước khi yes
for h in controller01 controller02 controller03; do
  echo "=== $h ==="
  ssh $h 'sudo apt -y autoremove --purge 2>&1 | tail -3'
done

# Verify đã sạch
for h in controller01 controller02 controller03; do
  echo "=== $h ==="
  ssh $h 'dpkg -l | grep -E "nova-compute|qemu-kvm|libvirt-daemon-system" || echo "(sạch)"'
  ssh $h 'dpkg -l | grep -E "python3-rbd|python3-rados"'   # 2 dòng này vẫn phải còn
done
```
#### Bước 3 — Nếu controller đã bị register thành compute host, xoá khỏi DB
```bash
# Xem từng ID compute service trên controller
openstack compute service list --service nova-compute -c ID -c Host -c Status

# Xoá từng cái (thay <ID> bằng giá trị thật từ output trên)
openstack compute service delete <ID-of-controller01>
openstack compute service delete <ID-of-controller02>
openstack compute service delete <ID-of-controller03>

# Xoá host khỏi cell mapping
ssh controller01 'sudo -u nova nova-manage cell_v2 delete_host --cell_name=cell1 --host=controller01'
ssh controller01 'sudo -u nova nova-manage cell_v2 delete_host --cell_name=cell1 --host=controller02'
ssh controller01 'sudo -u nova nova-manage cell_v2 delete_host --cell_name=cell1 --host=controller03'

# Verify chỉ còn 3 compute thật
openstack compute service list --service nova-compute
ssh controller01 'sudo -u nova nova-manage cell_v2 list_hosts --cell_name=cell1'
```

Cuối cùng openstack compute service list phải đúng:
- 3 dòng nova-scheduler (controller01/02/03)
- 3 dòng nova-conductor (controller01/02/03)
- 3 dòng nova-compute (compute01/02/03 — KHÔNG có controller)

### 6.3. Set quyền keyring trên compute

```bash
for h in compute01 compute02 compute03; do
  ssh $h '
    sudo chgrp nova /etc/ceph/ceph.client.cinder.keyring
    sudo chmod 0640 /etc/ceph/ceph.client.cinder.keyring
  '
done
```

### 6.4. Libvirt secret (giống nhau giữa 3 compute)

```bash
# trên deployer — sinh UUID 1 lần
UUID=$(uuidgen)
echo "LIBVIRT_SECRET_UUID=$UUID"
# GHI LẠI UUID NÀY — sẽ dùng trong nova.conf
```

![altimage](../images/Screenshot_36.png)

Trên compute01 (và lặp y hệt cho compute02, compute03):

```bash
# 1. Set UUID — PHẢI GIỐNG NHAU 3 NODE, dùng UUID đã sinh ở deployer
UUID=<dán-UUID-bạn-đã-uuidgen-ở-deployer>
echo "UUID=$UUID"

# 2. Tạo secret XML
sudo tee /tmp/secret.xml > /dev/null <<EOF
<secret ephemeral='no' private='no'>
  <uuid>${UUID}</uuid>
  <usage type='ceph'>
    <name>client.cinder secret</name>
  </usage>
</secret>
EOF

# 3. Define secret vào libvirt
sudo virsh secret-define --file /tmp/secret.xml

# 4. Lấy key từ keyring (KHÔNG escape $)
KEY=$(sudo awk '/key/ {print $3}' /etc/ceph/ceph.client.cinder.keyring)
echo "KEY=$KEY"

# 5. Set value vào secret
sudo virsh secret-set-value --secret ${UUID} --base64 ${KEY}

# 6. Verify
sudo virsh secret-list

# 7. Cleanup
sudo rm /tmp/secret.xml
```

```bash
root@compute01:~# sudo virsh secret-set-value --secret ${UUID} --base64 ${KEY}
error: Passing secret value as command-line argument is insecure!
Secret value set
```
- Warning thôi, không phải error. Dòng cuối Secret value set xác nhận giá trị đã được lưu thành công. Libvirt mới gắn warning này vì command-line args có thể lộ qua ps aux lúc chạy hoặc lưu vào bash history — vấn đề security nhưng không ảnh hưởng kết quả lab.
- Verify nhanh secret thực sự có giá trị đúng:
```bash
sudo virsh secret-get-value $UUID
# in ra chuỗi base64 — phải khớp với $KEY bạn vừa echo
```
Nếu in ra base64 → xong, qua mục 6.5.
- Nếu muốn an toàn hơn dùng file thay command-line
```bash
# xoá secret cũ
sudo virsh secret-undefine $UUID

# định nghĩa lại
sudo virsh secret-define --file /tmp/secret.xml

# set qua file thay vì argv
echo -n "$KEY" | sudo tee /tmp/secret-value > /dev/null
sudo virsh secret-set-value --secret $UUID --file /tmp/secret-value
sudo shred -u /tmp/secret-value      # xoá an toàn

# verify
sudo virsh secret-get-value $UUID
```

> Verify ra 1 dòng `UUID  ceph client.cinder secret`. Nếu không thấy = secret-define fail
> (thường do XML lỗi syntax). Debug: `cat /tmp/secret.xml` rồi đọc.

### 6.5. `/etc/nova/nova.conf` trên compute01 (đổi IP cho 02/03)

```bash
ssh compute01 "sudo tee /etc/nova/nova.conf > /dev/null <<'EOF'
[DEFAULT]
my_ip = 192.168.70.112
state_path = /var/lib/nova
transport_url = rabbit://openstack:RABBIT_PASS@controller01:5672,openstack:RABBIT_PASS@controller02:5672,openstack:RABBIT_PASS@controller03:5672

[api]
auth_strategy = keystone

[keystone_authtoken]
www_authenticate_uri = http://192.168.70.120:5000/
auth_url = http://192.168.70.120:5000/
memcached_servers = 192.168.70.122:11211,192.168.70.127:11211,192.168.70.119:11211
auth_type = password
project_domain_name = Default
user_domain_name = Default
project_name = service
username = nova
password = NOVA_PASS

[service_user]
send_service_user_token = true
auth_url = http://192.168.70.120:5000/
auth_strategy = keystone
auth_type = password
project_domain_name = Default
user_domain_name = Default
project_name = service
username = nova
password = NOVA_PASS

[placement]
region_name = RegionOne
project_domain_name = Default
project_name = service
auth_type = password
user_domain_name = Default
auth_url = http://192.168.70.120:5000/v3
username = placement
password = PLACEMENT_PASS

[glance]
api_servers = http://192.168.70.120:9292

[oslo_concurrency]
lock_path = /var/lib/nova/tmp

[vnc]
enabled = true
server_listen = 0.0.0.0
server_proxyclient_address = 192.168.70.112
novncproxy_base_url = http://192.168.70.120:6080/vnc_auto.html

[libvirt]
virt_type = qemu
images_type = rbd
images_rbd_pool = vms
images_rbd_ceph_conf = /etc/ceph/ceph.conf
images_rbd_glance_store_name = ceph
images_rbd_glance_copy_poll_interval = 15
images_rbd_glance_copy_timeout = 600
rbd_user = cinder
rbd_secret_uuid = LIBVIRT_SECRET_UUID
disk_cachemodes = network=writeback
inject_password = false
inject_key = false
inject_partition = -2
live_migration_uri = qemu+ssh://nova@%s/system
hw_disk_discard = unmap

[neutron]
auth_url = http://192.168.70.120:5000
auth_type = password
project_domain_name = Default
user_domain_name = Default
region_name = RegionOne
project_name = service
username = neutron
password = NEUTRON_PASS

[wsgi]
api_paste_config = /etc/nova/api-paste.ini
EOF"

ssh compute01 "sudo chown root:nova /etc/nova/nova.conf && sudo chmod 0640 /etc/nova/nova.conf"
ssh compute01 "sudo sed -i 's/LIBVIRT_SECRET_UUID/$UUID/' /etc/nova/nova.conf"
```

Lặp y hệt cho compute02 (`my_ip=.124`, `server_proxyclient_address=.124`) và compute03
(`my_ip=.112`, `server_proxyclient_address=.112`).

```bash
for h in compute01 compute02 compute03; do
  ssh $h 'sudo apt -y install ceph-common'
done

# Set quyền keyring cho user nova đọc được
for h in compute01 compute02 compute03; do
  ssh $h '
    sudo chgrp nova /etc/ceph/ceph.client.cinder.keyring
    sudo chmod 0640 /etc/ceph/ceph.client.cinder.keyring
  '
done

# Test ceph CLI từ compute01 với keyring của nó (verify trước restart)
ssh compute01 'sudo -u nova ceph -n client.cinder --keyring=/etc/ceph/ceph.client.cinder.keyring -s'
# Mong đợi: HEALTH_OK, không lỗi "command not found" hay "auth"

# Restart nova-compute
for h in compute01 compute02 compute03; do
  ssh $h 'sudo systemctl restart nova-compute'
done

# Verify
sleep 8
openstack compute service list --service nova-compute
```

```bash
for h in compute01 compute02 compute03; do
  echo "=== $h ==="
  # đổi virt_type
  ssh $h 'sudo sed -i "s/^virt_type *= *qemu/virt_type = kvm/" /etc/nova/nova.conf'
  ssh $h 'sudo grep "^virt_type" /etc/nova/nova.conf'
  
  # đảm bảo user nova có quyền vào /dev/kvm + libvirt
  ssh $h 'sudo usermod -aG kvm,libvirt nova'
  
  # restart cả libvirt và nova-compute (libvirt phải lên trước)
  ssh $h 'sudo systemctl restart libvirtd && sleep 2 && sudo systemctl restart nova-compute'
done

# Verify nova-compute không crash sau đổi
for h in compute01 compute02 compute03; do
  echo "=== $h ==="
  ssh $h 'sudo systemctl is-active libvirtd nova-compute; sudo journalctl -u nova-compute -n 5 --no-pager | tail -5'
done
```


### 6.6. Restart nova-compute + libvirt

```bash
for h in compute01 compute02 compute03; do
  ssh $h '
    sudo systemctl restart libvirtd nova-compute
    sudo systemctl enable libvirtd nova-compute
  '
done
```

Kiểm tra log compute01 ngay:
```bash
ssh compute01 'sudo journalctl -u nova-compute -n 30 --no-pager | tail -15'
```
Cần thấy `Compute node record created`. KHÔNG có `ERROR`.

---

## 7. CELL DISCOVERY (controller01)

Compute node mới đăng ký vào DB nhưng chưa được map vào cell1. Phải discover thủ công (hoặc
auto qua periodic, nhưng manual để chắc chắn):

```bash
ssh controller01 'sudo -u nova nova-manage cell_v2 discover_hosts --verbose'
```

Mong đợi:
```
Found 3 unmapped computes in cell: <cell1-uuid>
Checking host mapping for compute host 'compute01': <uuid>
Creating host mapping for compute host 'compute01': <uuid>
... (lặp cho compute02, compute03)
```

> Mỗi lần thêm compute mới sau này, chạy lại lệnh này. Hoặc cấu hình
> `discover_hosts_in_cells_interval = 300` trong `nova.conf` controller scheduler để tự động.

---

## 8. VERIFY GIAI ĐOẠN 6

### 8.1. Compute service list

```bash
# trên deployer
openstack compute service list
```

Mong đợi:
- 3 dòng `nova-scheduler` (3 controller) — State `up`, Status `enabled`.
- 3 dòng `nova-conductor` (3 controller) — `up`/`enabled`.
- 3 dòng `nova-compute` (3 compute) — `up`/`enabled`.
- **TỔNG 9 dòng**.

Nếu thiếu compute → cell discovery chưa chạy đủ, lặp mục 7.
Nếu thiếu scheduler/conductor → service controller không start được, xem
`journalctl -u nova-{scheduler,conductor}`.

### 8.2. Hypervisor list

```bash
openstack hypervisor list
```
3 dòng, mỗi node 1 hypervisor `QEMU` state `up`.

```bash
openstack hypervisor stats show
# total vCPU, RAM, disk = tổng 3 compute
```

![altimage](../images/Screenshot_37.png)

### 8.3. Nova status check

```bash
ssh controller01 'sudo -u nova nova-status upgrade check'
```

Mong đợi 7-8 mục, tất cả `Success`. Nếu có `Warning` đọc kỹ — thường là cảnh báo về placement
version hoặc cell mapping; nếu `Failure` thì phải fix.

![altimage](../images/Screenshot_38.png)

### 8.4. Convert cirros image sang RAW (yêu cầu CoW Ceph)

Cirros upload ở Phase 5 là qcow2 → Glance không tạo snapshot CoW → Nova phải copy full bytes
sang pool `vms`. Để dùng CoW, image phải là **raw**.

```bash
# trên deployer
cd ~
qemu-img convert -f qcow2 -O raw cirros-0.6.2-x86_64-disk.img cirros-0.6.2-x86_64-disk.raw

# xoá image cũ
openstack image delete cirros-0.6.2

# upload bản raw
openstack image create "cirros-0.6.2" \
  --file cirros-0.6.2-x86_64-disk.raw \
  --disk-format raw \
  --container-format bare \
  --public

# verify
openstack image show cirros-0.6.2 | grep -E 'disk_format|direct_url|stores'
sudo rbd -p images ls
sudo rbd -p images info <new-image-id>
sudo rbd -p images snap ls <new-image-id>
# mong đợi: có snap 'snap' (CoW parent)
```

### 8.5. Test boot VM (sẽ fail ở phase này vì chưa có network — đây là expected)

```bash
openstack flavor create --vcpus 1 --ram 64 --disk 1 m1.nano
openstack server create --flavor m1.nano --image cirros-0.6.2 test-vm-no-net
sleep 5
openstack server show test-vm-no-net -c status -c fault
```

Mong đợi: `status: ERROR`, `fault: ... Network ... not found` hoặc tương tự. Đây là dấu hiệu
**Nova làm đúng việc của nó**: scheduler chọn được compute node, libvirt chuẩn bị spawn, fail
ở bước network — đợi Phase 7 sửa.

```bash
openstack server delete test-vm-no-net
```

Nếu fail ở chỗ khác (`No valid host found`, `Image not raw`, `Connection to libvirt failed`)
là vấn đề Phase 6 thật — phải fix trước.

---

## 9. NGUỒN THAM KHẢO

- Placement install — Ubuntu 2025.1:
  https://docs.openstack.org/placement/2025.1/install/install-ubuntu.html
- Nova install — Ubuntu 2025.1:
  https://docs.openstack.org/nova/2025.1/install/
- Cells v2 layout:
  https://docs.openstack.org/nova/latest/admin/cells.html
- Nova + Ceph RBD (libvirt secret):
  https://docs.ceph.com/en/squid/rbd/rbd-openstack/#configuring-nova-to-attach-ceph-rbd-block-device

---