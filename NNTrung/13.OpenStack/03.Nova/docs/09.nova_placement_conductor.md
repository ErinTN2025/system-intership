# Nova Placement và Nova Conductor


### 1. Nova Placement

**Giới thiệu**  
Placement là dịch vụ riêng biệt (tách ra từ Nova từ bản **Stein 19.0.0**). Trước đó nó nằm trong Nova từ bản **Newton**.  

Placement cung cấp **REST API** và data model để theo dõi **inventory** (tài nguyên sẵn có) và **allocation** (tài nguyên đã cấp) của các **Resource Provider**.  

Placement coi mỗi nơi cung cấp tài nguyên là một Resource Provider

**Mục tiêu chính:**  
- Giúp Scheduler chọn host chính xác, nhanh và scalable.  
- Hỗ trợ nhiều loại tài nguyên phức tạp (CPU, RAM, disk, GPU, PCI, NUMA, shared storage, IP pool…).  
- Tách biệt resource tracking khỏi Nova DB → dễ scale và nâng cấp.

**Các khái niệm cốt lõi cần nhớ**

- **Resource Provider (RP)**:  
  Thực thể cung cấp tài nguyên. Ví dụ:  
  - Compute node (thường là RP root) cung cấp tài nguyên CPU, RAM.  
  - Shared storage pool cung cấp DISK.  
  - IP allocation pool (Neutron) cung cấp IP.  
  - Nested RP (GPU, SR-IOV, disk NVMe…).

- **Resource Classes**:  
  Các loại tài nguyên định lượng (quantitative).  
  Chuẩn: `VCPU`: CPU, `MEMORY_MB`:RAM, `DISK_GB`: DISK, `PCI_DEVICE`, `VGPU`…  
  Có thể định nghĩa custom (`CUSTOM_*`).

- **Inventory**:  
  Số lượng tài nguyên sẵn có trên một RP (ví dụ: 48 VCPU, 256 GB RAM, 10 TB DISK).

- **Allocation**:  
  Tài nguyên đã cấp cho một consumer (thường là instance). Placement ghi nhận allocation để tính usage thực tế.

- **Traits**:  
  Đặc tính định tính (qualitative): đặc điểm cảu Resource Provider – không tiêu thụ được.  

  Ví dụ: `HW_CPU_X86_AVX512`, `COMPUTE_VOLUME_MULTIATTACH`, `CUSTOM_GENERAL_COMPUTE`, `SSD`, `GPU_PASSTHROUGH`…  

  Instance/flavor có thể yêu cầu **required traits** hoặc **forbidden traits**.

- **Aggregates**:  
  Nhóm các Resource Provider (tương tự host aggregates trong Nova nhưng thuộc Placement).  
  Dùng để nhóm theo AZ, rack, hardware type… và áp dụng traits chung.

**Luồng khi tạo Instance**  
0. Khi user tạo VM:
```bash
openstack server create
```
1. nova-api → Scheduler nhận RequestSpec (flavor + image traits + extra specs).  

2. Scheduler gọi Placement API (`GET /allocation_candidates`) → lấy danh sách candidate hosts + allocation proposal.  

3. Scheduler chọn host → claim allocation (`POST /allocations`).  

4. Nếu claim thành công → Conductor/Compute tiến hành spawn.  

5. nova-compute định kỳ report usage về Placement.

Nếu Placement invalid bạn sẽ không tạo được instance mới.

**Lệnh CLI quan trọng**  
```bash
openstack resource provider list
openstack resource provider inventory list <rp-uuid>
openstack resource provider allocation show <instance-uuid>
openstack resource provider trait list <rp-uuid>
openstack resource provider aggregate list <rp-uuid>

# nova-manage
nova-manage placement heal_allocations --verbose          # Sửa allocation bị lệch
nova-manage placement sync_aggregates                     # Đồng bộ aggregate
```

**Cấu hình chính** (nova.conf phần `[placement]`)  
Sử dụng Keystone auth (username/password hoặc service user).  
Quan trọng: `region_name`, `auth_url`, `valid_interfaces=internal`.

**Best practices cho Production**  
- Luôn chạy `nova-manage placement heal_allocations` sau migration/upgrade.  
- Sử dụng traits + aggregates để phân loại hardware (general-purpose, GPU, high-memory…).  
- Giám sát placement-api.log và allocation usage.  
- Placement DB riêng → backup độc lập.

### 2. Nova Conductor
OpenStack Nova Conductor là một service trung gian(middleware) hay còn là 1 deamon service trong OpenStack. Nó đóng vai trò xử lý logic phức tạp và truy cập database thay cho compute node.

Compute không được phép truy cập DB trực tiếp mà phải đi qua Conductor.

**Vai trò**  
Conductor là **database proxy** và **task coordinator**.  
Nó ngăn nova-compute kết nối trực tiếp đến database, thay vào đó tất cả các thao tác DB phức tạp đều đi qua RPC đến Conductor.

**Chức năng chính**  
- Xử lý các task cần phối hợp: build instance, resize, migrate, evacuate, rebuild…  
- Object versioning & conversion (hỗ trợ rolling upgrade).  
- Proxy tất cả database operations từ compute nodes.  
- Trong **Cells v2**: Có super conductor (cell0) và per-cell conductor.

**Luồng cũ vs Luồng mới (với Conductor)**  
**Cũ (không Conductor)**: Compute kết nối trực tiếp DB → kém an toàn, khó upgrade.  
**Mới**:  
- nova-compute gọi RPC đến Conductor.  
- Conductor thực hiện DB operation và trả kết quả.  
- Scheduler và API cũng tương tác qua Conductor khi cần.

**Lợi ích chính**

**Bảo mật**  
- Compute node bị compromise → không thể trực tiếp truy cập hoặc sửa DB.  
- Conductor kiểm soát tất cả truy vấn từ compute.

**Nâng cấp (Rolling Upgrade)**  
- Conductor duy trì compatibility layer.  
- Có thể upgrade control plane (API, Conductor, Scheduler, Placement) trước, compute node upgrade sau.  
- Compute cũ vẫn giao tiếp được với DB schema mới qua Conductor.

**Scale & Maintainability**  
- Tách biệt trách nhiệm: Compute chỉ lo hypervisor (libvirt/QEMU), Conductor lo orchestration và DB.  
- Dễ scale Conductor horizontally (workers).

**Cấu hình quan trọng** (nova.conf phần `[conductor]`)
```ini
[conductor]
workers = 8          # Số worker process (thường = số CPU cores)
```

**Lệnh quản lý**  
```bash
openstack compute service list | grep conductor

nova-manage db online_data_migrations --max-count 100   # Chạy sau upgrade
nova-manage cell_v2 ...                                 # Liên quan Cells
```

**Log**: `/var/log/nova/nova-conductor.log`

**Best practices**  
- Không bao giờ để nova-compute connect trực tiếp DB (conductor phải luôn bật).  
- Scale Conductor theo số lượng compute nodes và tần suất tạo/migrate VM.  
- Sau mọi upgrade Nova → chạy `nova-manage db online_data_migrations`.  
- Giám sát RPC queue và worker utilization của Conductor.

### Tóm tắt so sánh
| Tiêu chí              | Placement                              | Conductor                                  |
|-----------------------|----------------------------------------|--------------------------------------------|
| **Chức năng**         | Theo dõi & claim tài nguyên            | Proxy DB + phối hợp task                   |
| **Service**           | Riêng (placement-api)                  | Thuộc Nova (nova-conductor)                |
| **Database**          | Placement DB riêng                     | Nova API DB + Cell DB                      |
| **Tương tác chính**   | Với Scheduler (allocation_candidates)  | Với nova-compute (RPC)                     |
| **Ảnh hưởng khi down**| Không tạo VM mới được                  | Task dài (migrate, build) bị ảnh hưởng     |
| **Lệnh quản lý**      | `nova-manage placement ...`            | `nova-manage db ...`                       |

**Lưu ý**  
- Placement = “Resource Scheduling Brain” của Nova.  
- Conductor = “Safe Database Bridge” giữa Compute và Control Plane.  
- Hai service này là nền tảng cho Cells v2, rolling upgrade và scheduling phức tạp (GPU, NUMA, traits).  
- Luôn kiểm tra heal_allocations và online_data_migrations sau thay đổi lớn.

**Tham khảo**  
- Placement: https://docs.openstack.org/placement/latest/  
- Nova Architecture: https://docs.openstack.org/nova/latest/admin/architecture.html  
- Configuration: https://docs.openstack.org/nova/latest/configuration/config.html  

