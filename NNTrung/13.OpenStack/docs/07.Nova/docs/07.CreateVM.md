# Quá trình khởi tạo máy ảo trong OpenStack Nova 

Khi bạn nhấn nút “Launch Instance” trên Horizon hoặc chạy lệnh `openstack server create`, OpenStack Nova sẽ phối hợp nhiều thành phần để tạo ra một máy ảo (instance) hoàn chỉnh.  

#### 1. Tổng quan kiến trúc Nova hiện đại

OpenStack Nova hoạt động theo mô hình **phân tán** rõ ràng:

- **Controller Node** (máy chủ quản lý): Chứa các dịch vụ “não bộ” như nova-api, nova-scheduler, nova-conductor và Placement API. Đây là nơi nhận lệnh, kiểm tra quyền, lập kế hoạch và điều phối.
- **Compute Node** (máy chủ tính toán): Chạy **nova-compute** và hypervisor (thường là KVM/QEMU). Đây là nơi máy ảo thực sự được tạo và chạy.

Các thành phần giao tiếp với nhau chủ yếu qua **Message Queue** (thường là RabbitMQ) để đảm bảo tính linh hoạt và khả năng mở rộng.

**Sơ đồ tổng quát đơn giản**:

```
Người dùng (Horizon / CLI)
        ↓ (REST API + Token từ Keystone)
   Controller Node
   ├── nova-api
   ├── nova-scheduler     ←→ Placement API (kiểm tra tài nguyên)
   ├── nova-conductor     ←→ Database (MySQL)
   └── Message Queue (RabbitMQ)
        ↓
   Compute Node
   └── nova-compute → Libvirt → KVM/QEMU → Máy ảo thực tế
        ↔ Neutron (mạng)   ↔ Cinder (ổ cứng)   ↔ Glance (image)
```

#### 2. Quy trình khởi tạo máy ảo chi tiết (Workflow)

Quy trình được chia thành 5 giai đoạn chính để dễ theo dõi:

**Giai đoạn 1: Xác thực và Chuẩn bị Yêu cầu**

1. **Xác thực người dùng qua Keystone**  
   - Bạn đăng nhập bằng username/password hoặc application credential. 
   - Keystone trả về một **token** (scoped token) chứa thông tin quyền hạn trong project cụ thể.
   - Client chọn project mục tiêu và request scoped token để làm việc với các service trong project đó
   - Scoped token chứa: user_id, project_id, roles, endpoints catalog, và thời hạn hết hạn

2. **Nova API nhận yêu cầu**  
   Yêu cầu tạo máy ảo (POST `/servers`) được gửi đến **`nova-api`**.  
   `Nova-api` kiểm tra:
   - Xác thực scoped token ngược lại với Keystone thông qua middleware `keystoneauth`
   - Policy engine (`policy.yaml`) kiểm tra quyền của user với action `compute:create`, Người dùng có quyền tạo máy ảo không? (kiểm tra policy)
   - Flavor, image, network, quota có đủ không?

   Nếu hợp lệ, Nova tạo bản ghi instance trong database với trạng thái **BUILDING** và gửi nhiệm vụ đến scheduler qua message queue.

**Giai đoạn 2: Lập kế hoạch và Chọn máy chủ (Scheduling)**

3. **Nova Scheduler làm việc**  
   Scheduler nhận yêu cầu và hỏi **Placement API** để tìm các compute node còn đủ tài nguyên (CPU, RAM, Disk…).

4. **Áp dụng bộ lọc (Filters) và tính điểm (Weighers)**  
   - **Filters**: Loại bỏ các máy chủ không phù hợp (ví dụ: không đủ RAM, không cùng Availability Zone, image không tương thích…).
   - **Weighers**: Chấm điểm các máy chủ còn lại và chọn máy chủ tốt nhất (thường ưu tiên máy chủ còn nhiều tài nguyên).

5. Scheduler cập nhật database và gửi lệnh “tạo và chạy máy ảo” đến **nova-compute** trên máy chủ được chọn.

**Giai đoạn 3: Xử lý trên Compute Node**

6. **Nova-compute nhận lệnh**  
   Nova-compute gọi nova-conductor để lấy đầy đủ thông tin instance (không kết nối trực tiếp database để tăng bảo mật).

7. **Chuẩn bị Image từ Glance**  
   Tải image về (hoặc dùng bản cache sẵn tại `/var/lib/nova/instances/_base/`).  
   Tạo đĩa ảo cho máy mới bằng công nghệ **copy-on-write** (qcow2) để tiết kiệm dung lượng.

8. **Cấu hình mạng qua Neutron**  
   Nova yêu cầu Neutron tạo port mạng, cấp IP, áp dụng security group (tường lửa). Neutron trả về thông tin mạng cho nova-compute.

9. **Gắn ổ cứng (nếu có volume từ Cinder)**  
   Nếu máy ảo boot từ volume hoặc có volume gắn thêm, Nova sẽ yêu cầu Cinder gắn volume vào máy ảo.

**Giai đoạn 4: Khởi động máy ảo thực tế**

10. **Tạo file mô tả XML cho Libvirt**  
    Nova-compute tạo file XML mô tả toàn bộ máy ảo (CPU, RAM, đĩa, card mạng, console…).

11. **Khởi chạy qua Hypervisor**  
    Libvirt nhận XML và gọi QEMU/KVM để khởi động máy ảo thật sự.

12. **Cloud-init tự động cấu hình**  
    Khi máy ảo boot, cloud-init đọc thông tin từ **metadata service** (169.254.169.254) hoặc config drive để:
    - Tạo user, đặt mật khẩu
    - Inject SSH key
    - Cấu hình mạng, chạy script khởi động…

    Khi máy ảo chạy ổn định, nova-compute cập nhật trạng thái thành **ACTIVE**.

**Giai đoạn 5: Hoàn tất và Cập nhật**

13. Cập nhật trạng thái trong database và gửi thông báo (notification).
14. Nova-compute báo cáo tài nguyên đã sử dụng lên Placement API để scheduler biết thông tin thời gian thực.
15. Máy ảo sẵn sàng sử dụng qua console (noVNC hoặc SPICE).

#### 3. Tóm tắt quy trình bằng sơ đồ đơn giản

```
Người dùng yêu cầu tạo VM
        ↓
Nova API kiểm tra quyền + quota
        ↓
Nova Scheduler chọn Compute Node phù hợp (dùng Placement)
        ↓
Nova Compute trên node đó nhận lệnh
        ↓
Chuẩn bị Image (Glance) + Mạng (Neutron) + Ổ cứng (Cinder)
        ↓
Tạo XML + Khởi chạy qua Libvirt/KVM
        ↓
Cloud-init cấu hình bên trong máy ảo
        ↓
Trạng thái ACTIVE → Hoàn tất
```

#### 4. Một số tính năng và cải tiến mới (2024–2026)

- **Placement API** độc lập và mạnh mẽ hơn: hỗ trợ theo dõi GPU, vGPU, NUMA, traits (đặc tính phần cứng).
- **Cells v2** là mặc định: giúp OpenStack scale lớn hơn bằng cách chia thành nhiều “cell”.
- **Live migration** cải tiến mạnh (đặc biệt trong Gazpacho 2026.1): hỗ trợ parallel migration và live migration với vTPM (bảo mật cao hơn).
- Bảo mật tốt hơn: mặc định dùng TLS cho giao tiếp nội bộ, tích hợp Barbican quản lý bí mật.
- Hỗ trợ tốt hơn cho AI/HPC và edge computing.

#### 5. Troubleshooting cơ bản (Mẹo debug khi gặp lỗi)

Khi máy ảo không tạo được, bạn có thể kiểm tra theo thứ tự sau:

1. Xem log theo thứ tự:  
   `nova-api.log` → `nova-scheduler.log` → `nova-compute.log`

2. Kiểm tra Placement:  
   `openstack resource provider list`  
   `openstack resource provider usage show <compute-host>`

3. Kiểm tra máy ảo trên compute node:  
   `virsh list --all`

4. Kiểm tra port mạng:  
   `openstack port list --device-id <instance-uuid>`

**Các lỗi thường gặp**:
- **Stuck ở BUILDING**: Scheduler không tìm được host phù hợp → kiểm tra quota hoặc tài nguyên Placement.
- **Image download lỗi**: Kiểm tra kết nối giữa compute node và Glance.
- **Mạng không lên**: Kiểm tra Neutron agent và security group.

---

