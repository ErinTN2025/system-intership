# Migrate VM trong OpenStack
## Tổng quan
Migration là quá trình di chuyển máy ảo từ host vật lí này sang một host vật lí khác. Migration được sinh ra để làm nhiệm vụ bảo trì nâng cấp hệ thống.

Trong OpenStack, Migration là hành động di chuyển một máy ảo (Instance) đang tồn tại từ Compute Node này sang Compute Node khác hoặc giữa các project trên cùng 1 node compute.

Nó phục vụ nhiều mục đích:
- **Cân bằng tải**: Di chuyển VMs tới các host khác khi phát hiện host đang chạy có dấu hiệu quá tải.
- **Bảo trì, nâng cấp hệ thống**: Di chuyển các VMs ra khỏi host trước khi tắt nó đi.
- **Khôi phục lại máy ảo khi host gặp lỗi**: Restart máy ảo trên một host khác.

**OpenStack hỗ trợ 2 kiểu migration**:
- Cold migration: Non-live migration
- **Live migration**: 
  - True live migration (shared storage or volume-based)
  - Block live migration

## So sánh 2 kiểu Migrate
### Cold Migration (Offline Migration / nova migrate)
- Máy ảo phải ở trạng thái Shutoff.
- Nova tắt máy ảo (nếu đang chạy), giải phóng tài nguyên trên host cũ.
- Scheduler chọn host mới → Nova chuyển instance sang host mới.
- Nếu dùng local disk (ephemeral storage): toàn bộ disk sẽ được copy qua mạng sang host mới.
- Nếu dùng shared storage (Ceph, NFS…): chỉ cần migrate định nghĩa máy ảo, không cần copy disk.
- Sau khi migrate xong, máy ảo được start lại trên host mới.
- Downtime = thời gian shutoff + copy disk (nếu có).
- Resize thực chất là cold migration kết hợp thay đổi flavor (và có thể thay đổi host).

### Live Migration
- Máy ảo vẫn đang chạy (Running), người dùng hầu như không bị gián đoạn.
- Có 2 loại chính:
  - Shared storage live migration (mặc định): Yêu cầu ephemeral disks phải nằm trên storage chung (Ceph, NFS…). Chỉ migrate RAM + CPU state → rất nhanh.
  - Block live migration: Không cần shared storage. Toàn bộ disk + RAM sẽ được copy qua mạng → chậm hơn, tốn băng thông.

- Quy trình chính:
  - **Tiền kiểm tra (Pre-migration checks)**: Nova kiểm tra xem Host đích có đủ RAM, CPU và cùng lớp mạng với Host nguồn không.
  - **Chuẩn bị tại Host đích**: Tạo ra các kết nối mạng (Neutron) và chuẩn bị các file cấu hình máy ảo tương ứng tại Host mới.
  - **Di chuyển bộ nhớ (Memory transfer)**: Đây là bước quan trọng nhất. RAM được copy từng phần. Vì máy ảo vẫn đang chạy, các trang RAM (memory pages) có thể bị thay đổi liên tục. Nova sẽ copy lặp đi lặp lại cho đến khi lượng RAM còn lại đủ nhỏ.
  - **Dừng và Chuyển giao (Suspend & Switchover)**: Trong một khoảnh khắc cực ngắn (vài ms), máy ảo ở Host cũ bị dừng hẳn, các trang RAM cuối cùng được đẩy sang Host mới.
  - **Kích hoạt**: Máy ảo được "đánh thức" tại Host mới.
  - **Dọn dẹp (Post-migration)**: Xóa cấu hình cũ tại Host nguồn.

- Downtime: Thường chỉ vài mili-giây đến dưới 1 giây (nếu memory dirty ít).
### Các điều kiện tiên quyết (Prerequisites)
- **CPU Compatibility**: Host nguồn và Host đích nên có cùng dòng CPU (ví dụ cùng là Intel Skylake). Nếu khác đời, bạn phải cấu hình `cpu_mode=custom` trong `nova.conf` để giả lập một tập lệnh chung.
- **Mạng (Networking)**: Cả hai Host phải cùng nằm trong một mạng quản trị và có kết nối thông suốt với nhau.
- **Libvirt/QEMU**: Phải cùng phiên bản hoặc phiên bản ở Host đích phải mới hơn Host nguồn.
- Thời gian: Đồng bộ thời gian (NTP) cực kỳ quan trọng giữa các node.

### Phân biệt Migration và Evacuation
- Migration: Host cũ vẫn đang SỐNG. Bạn chủ động di chuyển máy ảo đi chỗ khác (để bảo trì Host đó).

- Evacuation (Sơ tán): Host cũ đã CHẾT (sập nguồn, lỗi phần cứng đột ngột). Bạn dùng lệnh Evacuation để yêu cầu OpenStack "hồi sinh" máy ảo trên một Host khác dựa trên dữ liệu đĩa (thường yêu cầu Shared Storage như Ceph).

## Lab Migrate

### Mục tiêu bài lab
1. Cold migrate một VM giữa 2 compute node.
2. Resize VM (cold migration kết hợp đổi flavor).
3. Live migrate (block migration – không cần shared storage).
4. Mô phỏng evacuate khi compute node "chết".

### Mô hình lab

```
controller (10.10.34.161)
   ├── nova-api, nova-scheduler, nova-conductor
   ├── nova-novncproxy, placement-api
   └── MariaDB, RabbitMQ, Keystone

compute01  (10.10.34.162)  ── nova-compute + libvirt/KVM
compute02  (10.10.34.163)  ── nova-compute + libvirt/KVM
```

> Lab này giả định bạn đã có OpenStack tối thiểu 1 controller + 2 compute node. Tất cả lệnh chạy trên **controller** trừ khi có ghi rõ `[compute01]` hoặc `[compute02]`.

### Phần 0 – Chuẩn bị môi trường (chạy 1 lần)

```bash
# ==== Trên CONTROLLER ====
# 1. Source admin credential
source /root/admin-openrc

# 2. Kiểm tra 2 compute node UP
openstack compute service list --service nova-compute

# 3. Kiểm tra hypervisor
openstack hypervisor list

# 4. Tạo image + flavor + network nếu chưa có
openstack image list | grep -i cirros || \
  (wget https://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img -O /tmp/cirros.img && \
   openstack image create cirros --disk-format qcow2 --container-format bare --public --file /tmp/cirros.img)

openstack flavor list | grep m1.tiny || \
  openstack flavor create --ram 512 --disk 1 --vcpus 1 m1.tiny
openstack flavor list | grep m1.small || \
  openstack flavor create --ram 2048 --disk 10 --vcpus 1 m1.small

# 5. Tạo network + subnet đơn giản (nếu chưa có)
openstack network show private >/dev/null 2>&1 || \
  openstack network create private
openstack subnet show private-subnet >/dev/null 2>&1 || \
  openstack subnet create --network private --subnet-range 192.168.100.0/24 private-subnet

# 6. Tạo VM test
openstack server create vm-lab \
  --image cirros \
  --flavor m1.tiny \
  --network private \
  --wait

# 7. Xem VM đang chạy trên host nào
openstack server show vm-lab -f value -c OS-EXT-SRV-ATTR:host
```

Ghi nhớ host hiện tại (giả sử là `compute01`). Các phần lab dưới đây giả định VM đang ở `compute01` và sẽ migrate sang `compute02`.

---

### Phần 1 – Cold Migration (Offline)

**Khái niệm**: VM bị tắt → copy disk + định nghĩa sang host mới → bật lại. Downtime = vài chục giây đến vài phút.

```bash
# ==== Trên CONTROLLER ====
# 1. Xem host hiện tại của VM
openstack server show vm-lab -f value -c OS-EXT-SRV-ATTR:host

# 2. Cold migrate (Nova tự chọn host đích qua scheduler)
openstack server migrate vm-lab

# 3. Theo dõi trạng thái — VM sẽ qua: ACTIVE → RESIZE → VERIFY_RESIZE
watch -n 2 "openstack server show vm-lab -f value -c status -c OS-EXT-STS:task_state -c OS-EXT-SRV-ATTR:host"

# Nhấn Ctrl+C để thoát watch khi status = VERIFY_RESIZE

# 4. Xác nhận hoàn tất migration (commit)
openstack server migrate confirm vm-lab

# 5. Kiểm tra host mới
openstack server show vm-lab -f value -c OS-EXT-SRV-ATTR:host

# 6. (Tùy chọn) Nếu thấy có vấn đề, có thể revert thay vì confirm:
# openstack server migrate revert vm-lab
```

**Cold migrate với target host cụ thể** (yêu cầu admin role, OpenStack 2.56+):

```bash
openstack server migrate vm-lab --host compute02 --wait
openstack server migrate confirm vm-lab
```

**Debug nếu cold migrate fail**:

```bash
openstack server show vm-lab -f value -c fault
tail -n 100 /var/log/nova/nova-scheduler.log
ssh compute01 tail -n 100 /var/log/nova/nova-compute.log
ssh compute02 tail -n 100 /var/log/nova/nova-compute.log
```

---

### Phần 2 – Resize VM (Cold migration + đổi flavor)

**Khái niệm**: Resize thực chất là cold migration kết hợp đổi flavor. VM có thể đổi cả CPU/RAM/Disk và (có thể) chuyển host.

```bash
# ==== Trên CONTROLLER ====
# 1. Xem flavor hiện tại
openstack server show vm-lab -f value -c flavor

# 2. (Bắt buộc với cùng host) Bật allow_resize_to_same_host nếu chỉ có 1 compute
sudo crudini --set /etc/nova/nova.conf DEFAULT allow_resize_to_same_host True
sudo systemctl restart openstack-nova-api openstack-nova-scheduler openstack-nova-conductor

# 3. Resize sang flavor lớn hơn
openstack server resize --flavor m1.small vm-lab

# 4. Đợi đến trạng thái VERIFY_RESIZE
watch -n 2 "openstack server show vm-lab -f value -c status -c flavor -c OS-EXT-SRV-ATTR:host"

# 5. Confirm
openstack server resize confirm vm-lab

# 6. Verify flavor mới
openstack server show vm-lab -f value -c flavor
```

**Lưu ý**: Cirros image có thể không tự resize root disk. Với image production (Ubuntu Cloud), `cloud-init growpart` sẽ tự mở rộng partition.

---

### Phần 3 – Live Migration (Block Migration – không cần shared storage)

**Khái niệm**: VM vẫn chạy trong suốt quá trình. Downtime chỉ vài mili-giây. Block migration copy disk + RAM qua mạng (chậm hơn shared-storage live migration).

#### 3.1 Chuẩn bị live migration (chạy 1 lần)

```bash
# ==== Trên CẢ 2 compute (compute01 và compute02) ====
# 1. Đảm bảo libvirt cho phép TCP listen
sudo tee /etc/libvirt/libvirtd.conf <<'EOF'
listen_tls = 0
listen_tcp = 1
auth_tcp = "none"
listen_addr = "0.0.0.0"
EOF

# 2. Bật listen TCP (Ubuntu)
sudo sed -i 's/^#LIBVIRTD_ARGS=.*/LIBVIRTD_ARGS="--listen"/' /etc/default/libvirtd 2>/dev/null || true
sudo sed -i 's/^LIBVIRTD_ARGS=.*/LIBVIRTD_ARGS="--listen"/' /etc/default/libvirtd 2>/dev/null || true

# (Trên RHEL/CentOS dùng socket activation – bỏ qua bước trên)
# sudo systemctl mask libvirtd.service
# sudo systemctl enable --now libvirtd-tcp.socket libvirtd.socket

sudo systemctl restart libvirtd

# 3. Bật permit_post_copy cho safe live migration
sudo crudini --set /etc/nova/nova.conf libvirt live_migration_scheme tcp
sudo crudini --set /etc/nova/nova.conf libvirt live_migration_inbound_addr "$(hostname -I | awk '{print $1}')"
sudo crudini --set /etc/nova/nova.conf libvirt live_migration_permit_post_copy True
sudo crudini --set /etc/nova/nova.conf libvirt live_migration_permit_auto_converge True

sudo systemctl restart openstack-nova-compute

# 4. Test SSH/TCP giữa 2 host
# Trên compute01:
sudo virsh -c qemu+tcp://compute02/system list
# Phải in ra danh sách VM của compute02 (có thể rỗng) - không lỗi auth
```

#### 3.2 Thực hiện Live Migration

```bash
# ==== Trên CONTROLLER ====
# 1. Xem host hiện tại
openstack server show vm-lab -f value -c OS-EXT-SRV-ATTR:host

# 2. Ping VM liên tục từ network namespace (để thấy downtime)
# Mở terminal khác và chạy:
sudo ip netns exec qdhcp-$(openstack network show private -f value -c id) ping 192.168.100.X
# (Thay 192.168.100.X bằng IP thật của vm-lab, lấy bằng: openstack server show vm-lab -f value -c addresses)

# 3. Live block migrate sang host khác
openstack server migrate vm-lab --live-migration --block-migration --host compute02 --wait

# 4. Kiểm tra: VM phải ở status ACTIVE, host đã đổi, ping chỉ mất 1-2 packet
openstack server show vm-lab -f value -c status -c OS-EXT-SRV-ATTR:host
```

**Cú pháp cũ (deprecated nhưng vẫn dùng được)**:
```bash
nova live-migration --block-migrate vm-lab compute02
```

#### 3.3 Theo dõi tiến trình live migration

```bash
# ==== Trên CONTROLLER ====
# Liệt kê migration đang chạy
openstack server migration list --server vm-lab

# Show chi tiết một migration
openstack server migration show vm-lab <migration-id>

# Force complete (nếu memory dirty rate quá cao, VM không converge)
openstack server migration force complete vm-lab <migration-id>

# Abort nếu cần
openstack server migration abort vm-lab <migration-id>
```

#### 3.4 Verify network trên host mới

```bash
# ==== Trên compute02 (host đích) ====
sudo virsh list --all
# Phải thấy VM vm-lab đang running

# Xem tap interface đã được plug vào OVS chưa
sudo ovs-vsctl show | grep tap

# Xem log
sudo tail -n 50 /var/log/nova/nova-compute.log
```

---

### Phần 4 – Mô phỏng Evacuate (sơ tán khi compute "chết")

**Khái niệm**: Evacuate dùng khi compute node đã DOWN (tắt nguồn, mất mạng). Nova sẽ rebuild VM trên host khác từ disk còn lưu (yêu cầu shared storage hoặc boot-from-volume).

> ⚠️ Lab evacuate **chỉ chạy được nếu có shared storage** (Ceph/NFS) hoặc VM boot từ Cinder volume. Với ephemeral disk local, data sẽ mất.

```bash
# ==== Bước 1: Trên CONTROLLER ====
# Tạo VM boot từ volume (để evacuate được khi host chết)
openstack server create vm-evac \
  --image cirros \
  --flavor m1.tiny \
  --network private \
  --boot-from-volume 2 \
  --wait

# Xem host hiện tại
openstack server show vm-evac -f value -c OS-EXT-SRV-ATTR:host
# Giả sử ở compute01

# ==== Bước 2: Mô phỏng "host chết" ====
# Tắt nova-compute trên compute01 (KHÔNG migrate)
ssh compute01 sudo systemctl stop openstack-nova-compute
ssh compute01 sudo systemctl stop libvirtd
# (Nếu muốn realistic hơn: ssh compute01 sudo shutdown -h now)

# Trên controller, đợi service được mark DOWN (~60s)
watch -n 5 "openstack compute service list --service nova-compute"

# Force disable để evacuate được
openstack compute service set --disable --disable-reason "simulate-failure" compute01 nova-compute

# ==== Bước 3: Evacuate ====
openstack server evacuate vm-evac --host compute02

# ==== Bước 4: Verify ====
openstack server show vm-evac -f value -c status -c OS-EXT-SRV-ATTR:host
# Status: ACTIVE, host: compute02

# ==== Bước 5: Dọn dẹp - bật lại compute01 ====
ssh compute01 sudo systemctl start libvirtd
ssh compute01 sudo systemctl start openstack-nova-compute
openstack compute service set --enable compute01 nova-compute
```

---

### Phần 5 – Bảng tóm tắt các loại migration

| Loại | Lệnh | VM đang chạy? | Cần shared storage? | Downtime |
|---|---|:---:|:---:|---|
| **Cold migrate** | `openstack server migrate <vm>` | ❌ (bị tắt) | Không | Vài phút |
| **Resize** | `openstack server resize --flavor <f> <vm>` | ❌ | Không | Vài phút + đổi flavor |
| **Live migrate (shared)** | `openstack server migrate <vm> --live-migration` | ✅ | ✅ (Ceph/NFS) | Mili-giây |
| **Live block migrate** | `openstack server migrate <vm> --live-migration --block-migration` | ✅ | Không | Vài giây |
| **Evacuate** | `openstack server evacuate <vm> --host <h>` | ❌ (host chết) | ✅ hoặc boot-from-volume | Phụ thuộc rebuild |

### Phần 6 – Cleanup sau lab

```bash
# Xóa VM test
openstack server delete vm-lab vm-evac --wait

# Xóa volume còn dư
openstack volume list -f value -c ID -c Status | grep available | awk '{print $1}' | xargs -r openstack volume delete

# Tắt allow_resize_to_same_host nếu đã bật cho lab
sudo crudini --del /etc/nova/nova.conf DEFAULT allow_resize_to_same_host
sudo systemctl restart openstack-nova-api openstack-nova-scheduler openstack-nova-conductor
```

### Phần 7 – Troubleshooting nhanh

| Triệu chứng | Nguyên nhân | Cách fix |
|---|---|---|
| `No valid host was found` khi migrate | Scheduler không tìm host khác đủ tài nguyên | Check `nova-scheduler.log`, xem RAM/Disk free các compute |
| Live migrate fail: `Connection refused` | libvirt chưa bật TCP listen | Kiểm tra `/etc/libvirt/libvirtd.conf` + restart libvirtd |
| Live migrate fail: `CPU doesn't match` | CPU model 2 host khác nhau | Set `cpu_mode = custom` + chọn `cpu_model` chung |
| VM stuck ở MIGRATING | Memory dirty quá nhanh, không converge | `openstack server migration force complete` |
| Sau evacuate VM ở ERROR | Host gốc chưa được disable | `openstack compute service set --disable ...` rồi evacuate lại |
| Cold migrate báo `same host` | Mặc định không cho migrate cùng host | Set `allow_migrate_to_same_host = True` (chỉ lab) |

**Log quan trọng cần xem khi debug**:
```bash
# Trên controller
tail -f /var/log/nova/nova-api.log
tail -f /var/log/nova/nova-scheduler.log
tail -f /var/log/nova/nova-conductor.log

# Trên 2 compute (source + target)
tail -f /var/log/nova/nova-compute.log
tail -f /var/log/libvirt/libvirtd.log
```

Grep theo `request-id` để trace toàn bộ flow:
```bash
REQ_ID=$(openstack --debug server migrate vm-lab 2>&1 | grep -oP 'req-[a-f0-9-]+' | head -1)
grep "$REQ_ID" /var/log/nova/*.log
```
