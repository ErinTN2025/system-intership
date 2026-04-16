# Tổng quan về project Nova trong OpenStack

## 1. Giới thiệu về Compute Service - Nova

**Nova** (OpenStack Compute) là một project core của OpenStack, chịu trách nhiệm chính cho việc cung cấp và quản lý tài nguyên điện toán (compute resources) trong môi trường cloud. Nova cho phép người dùng khởi tạo, quản lý và hủy các **instance** (máy ảo - virtual machines), đồng thời hỗ trợ ngày càng nhiều các workload khác như **bare-metal servers** (qua tích hợp với Ironic) và một số hình thức container hóa.

Nova là thành phần quan trọng nhất trong mô hình **Infrastructure-as-a-Service (IaaS)** của OpenStack. Nó không thực hiện ảo hóa trực tiếp mà đóng vai trò orchestrator: định nghĩa các **drivers** để tương tác với các hypervisor và công nghệ ảo hóa khác nhau chạy trên host (ví dụ: KVM/QEMU qua libvirt, Xen, VMware, Hyper-V, v.v.). Hầu hết các module của Nova được viết bằng Python.

**OpenStack Compute (Nova)** giao tiếp chặt chẽ với các service khác trong OpenStack:
- **Keystone** (Identity): Xác thực và ủy quyền cho người dùng, projects/tenants.
- **Glance** (Image): Lấy image để boot instance.
- **Neutron** (Networking): Quản lý network, port, floating IP cho instance (thay thế hoàn toàn nova-network ở các phiên bản hiện đại).
- **Cinder** (Block Storage): Cung cấp volume lưu trữ khối gắn vào instance.
- **Horizon** (Dashboard): Giao diện web cho người dùng cuối và quản trị viên.
- **Placement**: Theo dõi và phân bổ tài nguyên (resource providers).
- **Ironic**: Hỗ trợ provisioning bare-metal instances.
- Các service khác: Swift (object storage), Barbican (key management), v.v.

Nova hỗ trợ quản lý lifecycle đầy đủ của instance: launch, resize, migrate (cold/live), pause, suspend, reboot, terminate, evacuate, shelve/unshelve, v.v. Nó cũng quản lý truy cập từ users/projects và định nghĩa policies (RBAC).

**Lưu ý quan trọng**: Nova không chứa phần mềm ảo hóa. Nó chỉ cung cấp API và orchestration layer, sử dụng drivers để giao tiếp với hypervisor chạy trên compute node. Kiến trúc của Nova là **shared-nothing**, messaging-based, cho phép scale horizontally rất tốt.

Tính đến release **2026.1 Gazpacho** (phiên bản mới nhất hiện tại), Nova tiếp tục được cải tiến mạnh về hỗ trợ **AI/HPC workloads** (GPU passthrough, vGPU persistence, confidential computing), security (TLS cho consoles, vTPM detection), hardware enablement (PCI passthrough nâng cao với vfio-PCI drivers mới), và simplification cho operators (live migration cải thiện, placement optimizations).

## 2. Các thành phần của Nova

Nova bao gồm nhiều daemon/service riêng biệt, có thể triển khai trên nhiều node (controller node, compute node) để đảm bảo tính sẵn sàng cao và scale. Các thành phần chính giao tiếp qua **message queue** (thường là RabbitMQ, cũng hỗ trợ các AMQP khác như ZeroMQ) và chia sẻ **SQL database**.

Dưới đây là danh sách đầy đủ và cập nhật các thành phần (tính đến 2026):

- **nova-api** (Nova API service):  
  Là điểm tiếp nhận chính các yêu cầu từ người dùng (REST API). Hỗ trợ **OpenStack Compute API** (các microversions hiện tại lên đến 2.x), tương thích một phần với Amazon EC2 API (legacy), và Admin API cho quản trị. Nova-api thực hiện validation, policy enforcement (RBAC), và orchestration ban đầu (ví dụ: tạo instance). Nó chuyển request vào message queue để các service khác xử lý.

- **nova-api-metadata** (Nova Metadata API):  
  Cung cấp metadata service cho instance (user-data, meta-data theo chuẩn cloud-init). Thường chạy trên compute node hoặc controller, đặc biệt quan trọng trong môi trường multi-host hoặc khi sử dụng legacy nova-network. Instance truy cập qua link-local address (169.254.169.254).

- **nova-compute**:  
  Daemon chạy trên mỗi **compute node**. Chịu trách nhiệm trực tiếp tạo, hủy, và quản lý lifecycle của instance thông qua **hypervisor APIs**.  
  Các driver phổ biến:  
  - libvirt (KVM, QEMU, Xen, LXC/LXD)  
  - VMwareAPI  
  - Hyper-V, XenServer/XCP, v.v.  
  - Ironic driver cho bare-metal.  

  Quá trình khá phức tạp: nova-compute nhận task từ queue, thực hiện lệnh hệ thống (libvirt calls), cập nhật trạng thái instance, và báo cáo resource usage lên Placement. Nó cũng xử lý live migration, resize, và các hành động liên quan đến hypervisor.

- **nova-placement-api** (Placement service):  
  Được tách ra từ Nova từ bản **Newton** (2016) và vẫn là thành phần độc lập quan trọng. Placement theo dõi inventory và allocation của **resource providers** (compute node, shared storage pool, IP pool, GPU, FPGA, v.v.).  
  Nó hỗ trợ scheduling phức tạp: một instance có thể lấy CPU/RAM từ compute node, disk từ Cinder/Ceph, IP từ Neutron, và accelerators từ các provider riêng. Placement sử dụng **resource classes** (VCPU, MEMORY_MB, DISK_GB, CUSTOM_*, v.v.) và **traits** (HW_CPU_X86_AVX, etc.) để matching chính xác.  
  Trong các release gần đây (Dalmatian/Epoxy/Gazpacho), Placement được tối ưu hơn cho AI workloads với hỗ trợ GPU/vGPU persistence và PCI devices.

- **nova-scheduler**:  
  Service chịu trách nhiệm chọn compute host phù hợp cho instance mới (hoặc migrate/resize). Nó sử dụng **filter scheduler** (các filter như RamFilter, CpuFilter, AvailabilityZoneFilter, ComputeFilter, PCI passthrough filters, v.v.) kết hợp **weighers** (điểm số để chọn host tốt nhất).  
  Từ Pike trở đi, scheduler tương tác chặt chẽ với Placement để lấy thông tin resource usage thời gian thực. Nova-scheduler đặt request vào queue sau khi nhận từ nova-api.

- **nova-conductor**:  
  Module trung gian quan trọng, hoạt động như proxy giữa **nova-compute** và database. Nó loại bỏ hoàn toàn kết nối trực tiếp từ compute node đến DB (tăng security và scalability). Conductor xử lý các task phức tạp cần phối hợp (build instance, resize, migrate, object conversion). Có hai loại: **nova-conductor** (RPC) và **nova-cells** conductor trong môi trường cells v2.

- **nova-consoleauth** (Console Authentication):  
  Xác thực token cho console proxies. Dịch vụ này phải chạy cùng với các proxy console. Trong các deployment hiện đại, nó có thể được scale trong cluster.

- **nova-spicehtml5proxy**:  
  Cung cấp proxy cho truy cập console SPICE qua trình duyệt HTML5. Hỗ trợ remote desktop tốt hơn VNC ở một số trường hợp.

- **nova-xvpvncproxy** / **nova-novncproxy**:  
  Proxy cho VNC connection.  
  - **nova-xvpvncproxy**: Hỗ trợ OpenStack-specific Java client (legacy).  
  - **nova-novncproxy** (thường dùng hơn): Hỗ trợ noVNC (HTML5-based, phổ biến nhất hiện nay).

  **Cập nhật security**: Từ Dalmatian (2024.2), Nova hỗ trợ **TLS cho SPICE consoles** và tự động detect **virtual Trusted Platform Module (vTPM)** nếu libvirt >= 8.0 và swtpm được cài đặt.

- **The message queue**:  
  Trung tâm giao tiếp không đồng bộ giữa các daemon (oslo.messaging). Thường dùng **RabbitMQ**, hỗ trợ ZeroMQ, Kafka (experimental). Tất cả các service như API, Scheduler, Conductor, Compute đều giao tiếp qua queue.

- **SQL Database**:  
  Lưu trữ trạng thái của toàn bộ hạ tầng: instances, flavors, keypairs, security groups, networks (nếu dùng legacy), projects, quotas, v.v.  
  Nova hỗ trợ tất cả database tương thích SQLAlchemy: **MySQL/MariaDB** (khuyến nghị cho production), PostgreSQL, SQLite (chỉ test). Trong thực tế, hầu hết deployment dùng Galera Cluster cho MySQL/MariaDB để HA.

**Các thành phần khác đáng chú ý (không phải daemon riêng nhưng quan trọng)**:
- **Cells v2**: Hỗ trợ scale lớn bằng cách chia cloud thành nhiều "cells" (mỗi cell có scheduler và compute riêng, chia sẻ placement và API).
- **Nova Compute Drivers**: Hỗ trợ rộng rãi, bao gồm confidential computing (SEV, SEV-ES, TDX trên AMD/Intel).
- **PCI Passthrough & GPU/vGPU**: Được cải tiến mạnh trong Epoxy 2025.1 và Gazpacho 2026.1, hỗ trợ live migration với vfio-PCI drivers mới (ví dụ: Nvidia GRID).

**Deprecated/Legacy**:
- **nova-network**: Đã deprecated từ lâu, hoàn toàn thay bằng Neutron.
- Một số console proxy cũ hoặc EC2 API compatibility bị giảm hỗ trợ.
- nova-consoleauth đôi khi được tích hợp hoặc scale khác đi trong deployment hiện đại.

## 3. Kiến trúc của Nova

Kiến trúc Nova là **messaging-based, shared-nothing architecture**, cho phép triển khai phân tán cao:

- **DB (SQL Database)**: Lưu trữ persistent state.
- **API Layer**: Nhận HTTP/REST requests từ người dùng/CLI/Horizon, validate, và gửi task vào message queue (hoặc gọi trực tiếp Placement).
- **Scheduler**: Quyết định host phù hợp dựa trên filters/weighers + Placement queries.
- **Conductor**: Xử lý orchestration phức tạp, database proxy, object versioning.
- **Compute**: Thực thi trên hypervisor, báo cáo resource usage lên Placement.
- **Placement**: Theo dõi tài nguyên thời gian thực (inventory, allocation, traits).

**Sơ đồ kiến trúc cơ bản**:

```
Người dùng / Horizon / CLI
          ↓ (REST API)
     nova-api  ←→  Keystone (auth)
          ↓ (message queue / Placement HTTP)
nova-scheduler  ←→  Placement API (resource tracking)
          ↓ (message queue)
     nova-conductor  ←→  SQL Database
          ↓ (message queue)
     nova-compute (trên mỗi host)  ←→  Hypervisor (libvirt/KVM, etc.)
          ↑↓
     nova-api-metadata / Console Proxies (noVNC, SPICE)
          ↑↓
Neutron (network) + Cinder (storage) + Glance (image)
```

**Quy trình khởi tạo instance điển hình** (boot flow):
1. Người dùng gọi nova boot qua API.
2. nova-api validate → gọi Placement để claim resources → gửi request vào queue.
3. nova-scheduler chọn host phù hợp.
4. nova-conductor phối hợp (tạo block device mapping, network info).
5. nova-compute trên host được chọn: download image từ Glance, tạo VM qua hypervisor, attach network (Neutron), attach volume (Cinder), inject metadata.
6. Cập nhật trạng thái vào DB qua conductor và báo cáo usage lên Placement.

**Các cải tiến kiến trúc gần đây**:
- Tích hợp sâu hơn với Placement cho scheduling chính xác (hỗ trợ NUMA, hugepages, CPU pinning, accelerators).
- Hỗ trợ **multi-cell** và **edge computing** deployments.
- Cải thiện live migration và evacuate cho zero-downtime.
- Tối ưu cho AI/HPC: persistent vGPU, one-time-use passthrough devices, confidential computing.

