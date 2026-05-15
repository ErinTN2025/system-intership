# Cấu trúc thư mục OPS Kolla Ansible

## 1. Vị trí thực tế trên host

```
/etc/kolla/          ← config của tất cả service
/var/log/kolla/      ← log của tất cả service
```

Kolla-Ansible mount 2 thư mục này vào trong container, nên bạn xem được từ cả 2 phía.

---

## 2. Cấu trúc thư mục

### 2.1 Config — `/etc/kolla/`

```
/etc/kolla/
  ├── globals.yml          ← config tổng cụm (bạn đã biết)
  ├── passwords.yml        ← toàn bộ password
  ├── admin-openrc.sh      ← credentials CLI
  │
  ├── keystone/
  │     └── keystone.conf
  ├── nova/
  │     ├── nova.conf
  │     └── nova-compute.conf
  ├── neutron/
  │     ├── neutron.conf
  │     └── ml2_conf.ini
  ├── glance/
  │     └── glance-api.conf
  ├── cinder/
  │     └── cinder.conf
  ├── mariadb/
  │     └── config.json
  └── horizon/
        └── local_settings
```

### 2.2 Log — `/var/log/kolla/`

```
/var/log/kolla/
  ├── keystone/
  │     └── keystone.log
  ├── nova/
  │     ├── nova-api.log
  │     ├── nova-scheduler.log
  │     ├── nova-conductor.log
  │     └── nova-compute.log      ← trên compute node
  ├── neutron/
  │     ├── neutron-server.log
  │     ├── neutron-l3-agent.log
  │     ├── neutron-dhcp-agent.log
  │     └── neutron-metadata-agent.log
  ├── glance/
  │     └── glance-api.log
  ├── cinder/
  │     ├── cinder-api.log
  │     ├── cinder-scheduler.log
  │     └── cinder-volume.log
  └── horizon/
        └── horizon.log
```

---

## 3. Cách xem log

### Cách 1: Xem trực tiếp file trên host 

```bash
# Keystone
sudo tail -f /var/log/kolla/keystone/keystone.log

# Nova API
sudo tail -f /var/log/kolla/nova/nova-api.log

# Nova Compute (chạy trên compute node)
ssh kolla@compute01 'sudo tail -f /var/log/kolla/nova/nova-compute.log'

# Neutron server
sudo tail -f /var/log/kolla/neutron/neutron-server.log

# Neutron L3 agent (floating IP, router)
sudo tail -f /var/log/kolla/neutron/neutron-l3-agent.log

# DHCP agent (VM không lấy được IP)
sudo tail -f /var/log/kolla/neutron/neutron-dhcp-agent.log

# Glance
sudo tail -f /var/log/kolla/glance/glance-api.log
```

### Cách 2: Xem qua Docker logs

```bash
# Realtime
sudo docker logs -f keystone
sudo docker logs -f nova_api
sudo docker logs -f nova_compute
sudo docker logs -f neutron_server
sudo docker logs -f neutron_l3_agent
sudo docker logs -f glance_api
sudo docker logs -f mariadb

# Xem 100 dòng cuối
sudo docker logs --tail 100 nova_scheduler
```

### Cách 3: Grep tìm lỗi nhanh

```bash
# Tìm ERROR trong tất cả log
sudo grep -r "ERROR" /var/log/kolla/ --include="*.log" -l

# Tìm lỗi cụ thể
sudo grep "ERROR" /var/log/kolla/nova/nova-api.log | tail -20

# Tìm theo thời gian (ví dụ hôm nay)
sudo grep "2026-05-15" /var/log/kolla/neutron/neutron-server.log | grep ERROR
```

---

## 4. Cách xem config

### 4.1 Xem file config trên host

```bash
# Nova
sudo cat /etc/kolla/nova/nova.conf

# Neutron
sudo cat /etc/kolla/neutron/neutron.conf

# Keystone
sudo cat /etc/kolla/keystone/keystone.conf

# Glance
sudo cat /etc/kolla/glance/glance-api.conf
```

### 4.2 Xem config đang chạy bên trong container

```bash
# Đôi khi config trong container khác với file trên host
# (Kolla inject thêm biến lúc chạy)
sudo docker exec nova_api cat /etc/nova/nova.conf
sudo docker exec neutron_server cat /etc/neutron/neutron.conf
sudo docker exec keystone cat /etc/keystone/keystone.conf
sudo docker exec glance_api cat /etc/glance/glance-api.conf
```

---

## 5. Workflow debug thực tế

Khi có lỗi, đi theo thứ tự này:

```
Bước 1: Xác định service nào lỗi
  openstack compute service list
  openstack network agent list

Bước 2: Xem log service đó
  sudo tail -f /var/log/kolla/<service>/<service>.log

Bước 3: Nếu log không đủ, vào container xem
  sudo docker exec -it <container> bash
  cat /etc/<service>/<service>.conf

Bước 4: Nếu cần sửa config
  sudo nano /etc/kolla/<service>/<service>.conf
  sudo docker restart <container>
```

---

## 6. Bảng tham chiếu nhanh

| Service | Log | Config | Container |
|---------|-----|--------|-----------|
| Keystone | `/var/log/kolla/keystone/keystone.log` | `/etc/kolla/keystone/keystone.conf` | `keystone` |
| Nova API | `/var/log/kolla/nova/nova-api.log` | `/etc/kolla/nova/nova.conf` | `nova_api` |
| Nova Compute | `/var/log/kolla/nova/nova-compute.log` | `/etc/kolla/nova/nova.conf` | `nova_compute` |
| Nova Scheduler | `/var/log/kolla/nova/nova-scheduler.log` | `/etc/kolla/nova/nova.conf` | `nova_scheduler` |
| Neutron Server | `/var/log/kolla/neutron/neutron-server.log` | `/etc/kolla/neutron/neutron.conf` | `neutron_server` |
| Neutron L3 | `/var/log/kolla/neutron/neutron-l3-agent.log` | `/etc/kolla/neutron/neutron.conf` | `neutron_l3_agent` |
| Neutron DHCP | `/var/log/kolla/neutron/neutron-dhcp-agent.log` | `/etc/kolla/neutron/neutron.conf` | `neutron_dhcp_agent` |
| Glance | `/var/log/kolla/glance/glance-api.log` | `/etc/kolla/glance/glance-api.conf` | `glance_api` |
| Cinder API | `/var/log/kolla/cinder/cinder-api.log` | `/etc/kolla/cinder/cinder.conf` | `cinder_api` |
| MariaDB | `/var/log/kolla/mariadb/mariadb.log` | `/etc/kolla/mariadb/` | `mariadb` |
| RabbitMQ | `/var/log/kolla/rabbitmq/` | `/etc/kolla/rabbitmq/` | `rabbitmq` |
| Horizon | `/var/log/kolla/horizon/horizon.log` | `/etc/kolla/horizon/` | `horizon` |

> **Lưu ý:** Log trên compute node (`nova-compute`, `neutron-openvswitch-agent`) nằm trên **chính compute node đó**, không phải control01. Phải SSH vào compute01/02 để xem.