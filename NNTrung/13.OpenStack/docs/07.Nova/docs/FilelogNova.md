# File log Nova
**File log của Nova (OpenStack Compute) – Tài liệu cập nhật mới nhất (2025–2026)**

Nova sử dụng thư viện **oslo.log** (phiên bản mới nhất hiện tại là ~8.x) để quản lý logging. Không có thay đổi lớn về cấu trúc file log từ các release gần đây (Epoxy 2025.1, Flamingo 2025.2, và các dev version 33.x). Vị trí và tên file vẫn giữ nguyên như các phiên bản trước (Zed trở lên), chỉ có thêm một số tùy chọn logging mới (JSON format, rotation chi tiết hơn, journald, rate-limit…).

### 1. Vị trí mặc định của các file log
- **Non-container** (cài truyền thống):  
  `/var/log/nova/`

- **Containerized** (Kolla, TripleO, OpenStack Ansible…):  
  `/var/log/containers/nova/`

Mỗi service Nova sẽ ghi log vào file riêng có tên `tên-service.log` (được định nghĩa qua `--log-file` hoặc `log_file` trong `/etc/nova/nova.conf`).

### 2. Danh sách đầy đủ các file log chính của Nova (cập nhật 2025+)

| File log                        | Service tương ứng                          | Chạy trên node nào          | Nội dung chính (giúp gì cho debug/monitor) |
|--------------------------------|--------------------------------------------|-----------------------------|--------------------------------------------|
| **nova-api.log**              | nova-api                                   | Controller / API nodes     | Tất cả API request (create VM, resize, migrate…), **authentication**, quota, policy. Trace request-id đầu tiên. |
| **nova-scheduler.log**        | nova-scheduler                             | Controller                 | Quyết định placement (host selection), filter/weighers, lý do không chọn **host** nào. Rất hữu ích khi VM không khởi tạo được. |
| **nova-conductor.log**        | nova-conductor (có thể multiple)           | Controller                 | RPC giữa các service, database operations (tránh compute trực tiếp query DB). |
| **nova-compute.log**          | nova-compute                               | Compute nodes              | Toàn bộ vòng đời VM (spawn, boot, shutdown, migrate, resize, evacuate…). Libvirt/KVM errors, resource claim, network/VIF plug. **File quan trọng nhất khi debug instance**. |
| **nova-novncproxy.log**       | nova-novncproxy                            | Controller (console)       | Kết nối console noVNC. Debug nếu bị đen màn hình |
| **nova-serialproxy.log**      | nova-serialproxy (nếu dùng serial console) | Controller                 | Serial console access. |
| **nova-spicehtml5proxy.log**  | nova-spicehtml5proxy (nếu dùng SPICE)     | Controller                 | SPICE console. |
| **nova-manage.log**           | nova-manage commands                       | Bất kỳ node nào            | Output của lệnh `nova-manage` (db sync, cell, compute status…). |


### 3. Log bổ sung liên quan (rất hữu ích khi fix bug)
- **Console log của instance**:  
  `/var/lib/nova/instances/<instance-uuid>/console.log`  
  → Log boot/shutdown bên trong VM (kernel, cloud-init, lỗi hardware pass-through…).
- **Libvirt log** (hypervisor): `/var/log/libvirt/libvirtd.log` → lỗi KVM/QEMU.

### 4. Cấu hình logging (cập nhật từ nova 33.x / oslo.log mới nhất)
Chỉnh trong file `/etc/nova/nova.conf` (phần `[DEFAULT]`):

```ini
[DEFAULT]
log_dir = /var/log/nova
log_file = nova.log                # nếu muốn tất cả vào 1 file (không khuyến khích)
debug = True                       # Bật chi tiết (DEBUG) – chỉ dùng khi debug
use_json = True                    # Log dạng JSON (dễ parse bằng ELK/Loki)
use_journal = True                 # Dùng journald (systemd)
log_rotation_type = size           # Hoặc interval
max_logfile_size_mb = 100
max_logfile_count = 10
default_log_levels = nova=INFO,oslo=WARNING,libvirt=ERROR
logging_context_format_string = %(asctime)s.%(msecs)03d %(process)d %(levelname)s %(name)s [%(request_id)s %(user_identity)s] %(instance)s %(message)s
```

- `--log-config-append /etc/nova/logging.conf`: Dùng file config logging Python chi tiết (nếu cần custom handler, filter…).
- Rate limiting: `rate_limit_interval`, `rate_limit_burst` → tránh log flood.

### 5. Cách sử dụng log để kiểm tra, giám sát và fix bug (best practice)

1. **Trace một request (rất quan trọng)**  
   Mỗi API call có **request-id** (dạng `req-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).  
   Ví dụ:  
   ```bash
   grep "req-abc123" /var/log/nova/*.log
   ```  
   → Theo dõi toàn bộ flow: API → Scheduler → Conductor → Compute.

2. **Debug instance cụ thể**  
   Dùng `instance_uuid` hoặc `instance` trong log:  
   ```bash
   grep "<uuid-cua-vm>" /var/log/nova/nova-compute.log
   ```

3. **Các lỗi phổ biến & vị trí log**
   - VM không tạo được → Scheduler (không đủ host) hoặc Compute (libvirt error, image download, network plug).
   - Console không mở → novncproxy.log.
   - Migrate/resize fail → compute.log trên source + target node.
   - Boot loop → console.log của instance.

4. **Giám sát production**
   - Dùng **Loki + Grafana**, ELK, Fluentd, hoặc OpenStack Telemetry + Prometheus exporter.
   - Alert trên ERROR/CRITICAL + traceback.
   - Theo dõi kích thước log (nếu bật DEBUG thì log tăng rất nhanh).

5. **Mẹo fix bug nhanh**
   - Bật `debug = True` → restart service → reproduce issue → grep request-id.
   - Xem traceback (luôn có ở level ERROR).
   - Kiểm tra phiên bản Nova (`nova-manage --version` hoặc `openstack compute service list`).

### Tài liệu tham khảo
- Nova latest docs: https://docs.openstack.org/nova/latest/ (phần Configuration → oslo.log options)
- oslo.log configuration: https://docs.openstack.org/oslo.log/latest/

