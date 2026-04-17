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