# File cấu hình của Nova

File cấu hình chính của Nova nằm tại đường dẫn:  
`/etc/nova/nova.conf`

File này được sử dụng trên **cả Controller node** và **Compute node**, nhưng nội dung sẽ khác nhau tùy theo vai trò của node.  

Sau khi chỉnh sửa file, bạn cần restart các service tương ứng:
- Trên Controller: `systemctl restart nova-api nova-scheduler nova-conductor nova-placement-api` (và các console proxy nếu có).
- Trên Compute: `systemctl restart nova-compute`.

**Lưu ý quan trọng**:
- Sử dụng **MySQL/MariaDB** với Galera Cluster cho production.
- Transport URL thường dùng RabbitMQ (hoặc Redis/Kafka ở một số môi trường cao cấp).
- Tất cả password nên được thay bằng giá trị thực tế và bảo mật (không dùng password mặc định).

## 1. File cấu hình trên node Controller

Trên Controller node, nova.conf cần cấu hình đầy đủ các service: API, Scheduler, Conductor, Placement, Database, Keystone, Neutron, Glance, VNC/SPICE, Cache,...

```ini
[DEFAULT]
# IP management của node Controller (dùng cho internal communication)
my_ip = 10.10.34.161

# Transport URL cho message queue (RabbitMQ khuyến nghị)
transport_url = rabbit://openstack:Welcome123@10.10.34.161:5672/

# Hỗ trợ Neutron (bắt buộc ở phiên bản hiện tại, nova-network đã deprecated)
use_neutron = True
firewall_driver = nova.virt.firewall.NoopFirewallDriver

# Các tùy chọn khác thường dùng
log_dir = /var/log/nova
state_path = /var/lib/nova
lock_path = /var/lib/nova/tmp
enable_vnc = True                  # hoặc False nếu chỉ dùng SPICE

[api]
# Xác thực qua Keystone
auth_strategy = keystone

[api_database]
# Database cho nova-api (api database tách biệt từ Newton)
connection = mysql+pymysql://nova:Welcome123@10.10.34.161/nova_api

[cache]
# Cache backend (memcached khuyến nghị cho performance)
backend = oslo_cache.memcache_pool
enabled = true
memcache_servers = 10.10.34.161:11211

[database]
# Database chính cho Nova service
connection = mysql+pymysql://nova:Welcome123@10.10.34.161/nova

[glance]
# Đường dẫn đến Glance API
api_servers = http://10.10.34.161:9292

[keystone_authtoken]
auth_url = http://10.10.34.161:5000/v3
memcached_servers = 10.10.34.161:11211
auth_type = password
project_domain_name = Default
user_domain_name = Default
project_name = service
username = nova
password = Welcome123
region_name = RegionOne
# service_token_roles_required = True   # Khuyến nghị cho security

[neutron]
url = http://10.10.34.161:9696
auth_url = http://10.10.34.161:5000/v3
auth_type = password
project_domain_name = Default
user_domain_name = Default
region_name = RegionOne
project_name = service
username = neutron
password = Welcome123
service_metadata_proxy = true
metadata_proxy_shared_secret = Welcome123
# ovs_bridge = br-int                  # Nếu dùng OVS

[placement]
os_region_name = RegionOne
project_domain_name = Default
project_name = service
auth_type = password
user_domain_name = Default
auth_url = http://10.10.34.161:5000/v3
username = placement
password = Welcome123

[vnc]
# Cấu hình VNC proxy (noVNC - phổ biến nhất)
enabled = true
novncproxy_host = 10.10.34.161
vncserver_listen = 0.0.0.0                    # Hoặc 10.10.34.161
vncserver_proxyclient_address = 10.10.34.161
novncproxy_base_url = http://10.10.34.161:6080/vnc_auto.html
# keymap đã deprecated từ Rocky, không cần thiết lập nữa

# Nếu muốn dùng SPICE thay vì VNC (khuyến nghị cho performance tốt hơn)
#[spice]
#enabled = true
#html5proxy_base_url = http://10.10.34.161:6082/spice_auto.html
#server_listen = 0.0.0.0
#server_proxyclient_address = 10.10.34.161
```

**Các phần bổ sung thường dùng trên Controller (production)**:
```ini
[oslo_messaging_rabbit]
heartbeat_timeout_threshold = 60
amqp_durable_queues = false

[conductor]
workers = 4     # Tùy theo CPU của controller

[scheduler]
driver = filter_scheduler
workers = 4
```

## 2. File cấu hình của Nova-compute (trên Compute Node)

Trên **Compute node**, file `/etc/nova/nova.conf` **không cần** cấu hình đầy đủ như Controller.  
Bạn chỉ cần giữ lại các phần chung (DEFAULT, keystone_authtoken, neutron, placement, glance, vnc/spice) và thêm phần **[libvirt]** + một số tùy chọn đặc thù cho compute.

**Các cấu hình khác biệt chính so với Controller**:

```ini
[DEFAULT]
my_ip = 10.10.34.162               # Thay bằng IP management của Compute node này
transport_url = rabbit://openstack:Welcome123@10.10.34.161:5672/

use_neutron = True
firewall_driver = nova.virt.firewall.NoopFirewallDriver

# Tùy chọn performance & resource reservation (rất quan trọng)
reserved_host_memory_mb = 4096     # Dự trữ RAM cho host (tùy theo dung lượng RAM thực tế)
reserved_host_cpus = 2             # Dự trữ CPU cho host
cpu_allocation_ratio = 16.0        # Overcommit CPU (mặc định 16.0 ở bản mới)
ram_allocation_ratio = 1.5         # Overcommit RAM

log_dir = /var/log/nova
state_path = /var/lib/nova
lock_path = /var/lib/nova/tmp

[api]
auth_strategy = keystone

# Không cần [api_database] trên compute node (chỉ cần trên controller)

[cache]
backend = oslo_cache.memcache_pool
enabled = true
memcache_servers = 10.10.34.161:11211   # IP của controller

[glance]
api_servers = http://10.10.34.161:9292

[keystone_authtoken]
auth_url = http://10.10.34.161:5000/v3
memcached_servers = 10.10.34.161:11211
auth_type = password
project_domain_name = Default
user_domain_name = Default
project_name = service
username = nova
password = Welcome123
region_name = RegionOne

[neutron]
url = http://10.10.34.161:9696
auth_url = http://10.10.34.161:5000/v3
auth_type = password
project_domain_name = Default
user_domain_name = Default
region_name = RegionOne
project_name = service
username = neutron
password = Welcome123
service_metadata_proxy = true
metadata_proxy_shared_secret = Welcome123

[placement]
os_region_name = RegionOne
project_domain_name = Default
project_name = service
auth_type = password
user_domain_name = Default
auth_url = http://10.10.34.161:5000/v3
username = placement
password = Welcome123

[vnc]
enabled = true
vncserver_listen = 0.0.0.0
vncserver_proxyclient_address = 10.10.34.162   # IP của compute node
novncproxy_base_url = http://10.10.34.161:6080/vnc_auto.html

# Hoặc cấu hình SPICE (nếu dùng)
#[spice]
#enabled = true
#html5proxy_base_url = http://10.10.34.161:6082/spice_auto.html
#server_listen = 0.0.0.0
#server_proxyclient_address = 10.10.34.162

[libvirt]
# Loại ảo hóa sử dụng (phổ biến nhất là kvm)
virt_type = kvm

# Các tùy chọn quan trọng khác (khuyến nghị)
images_type = qcow2                    # Hoặc raw / rbd nếu dùng Ceph
# images_rbd_pool = vms                # Nếu dùng Ceph RBD
# images_rbd_ceph_conf = /etc/ceph/ceph.conf
# rbd_user = nova

# Hỗ trợ CPU pinning, NUMA, hugepages (nếu cần)
# cpu_mode = host-passthrough
# cpu_model = None

# Hỗ trợ PCI passthrough (GPU, SR-IOV, v.v.)
#[pci]
#passthrough_whitelist = {"vendor_id": "10de", "product_id": "1e07"}   # Ví dụ NVIDIA GPU

# Live migration (cải tiến mạnh ở Gazpacho 2026.1 - hỗ trợ parallel)
live_migration_scheme = ssh
# live_migration_permit_post_copy = true   # Tùy chọn nâng cao
```

**Các phần bổ sung thường dùng trên Compute node**:
```ini
[compute]
# Số lượng worker
workers = 8   # Tùy theo số core của compute node

[oslo_concurrency]
lock_path = /var/lib/nova/tmp
```

**Lưu ý khi triển khai**:
- Trên compute node **không** cấu hình `[api_database]` connection (để tránh compute node kết nối trực tiếp DB).
- Nếu dùng **Ceph** cho ephemeral storage → thay `images_type = rbd` và cấu hình thêm.
- Nếu dùng **GPU passthrough** hoặc **vGPU** → cấu hình phần `[pci]` và traits trong Placement.
- Sau khi thay đổi nova.conf trên compute node, chạy lệnh `nova-manage discover_hosts` trên controller để scheduler nhận compute node mới.


