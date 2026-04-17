# Overcommit RAM & CPU
Trong quản trị Cloud nói chung và OpenStack nói riêng, Overcommit (hay Oversubscription) là một kỹ thuật cực kỳ quan trọng để tối ưu hóa chi phí và tài nguyên. Hiểu đơn giản, đây là hành động khai báo vượt quá CPU và RAM trên các node Compute – cho phép tổng tài nguyên cấp phát cho các máy ảo lớn hơn tài nguyên vật lý thực tế của máy chủ.

## 1. Khái niệm Overcommit
Hầu hết các máy ảo (Instance) không bao giờ sử dụng 100% tài nguyên CPU hoặc RAM liên tục.
  - Nếu bạn có 100GB RAM và chỉ cho phép tạo đúng 100GB máy ảo, sẽ có một lượng lớn RAM bị lãng phí vì các máy ảo thực tế chỉ dùng khoảng 20-30%.
  - Overcommit giúp bạn "lấp đầy" phần lãng phí đó bằng cách cho phép tạo thêm máy ảo.

## 2. Overcommit CPU (vCPU)
CPU là tài nguyên "mềm", nghĩa là khi quá tải, hệ thống chỉ chạy chậm lại (xếp hàng đợi) chứ không sập ngay lập tức.
- Tỉ lệ mặc định (Default Ratio) là : 16.0 : 1
- Ý nghĩa: Nếu máy chủ vật lý của bạn có 16 Cores, với tỉ lệ 16:1, Nova Scheduler sẽ cho phép bạn cấp phát tổng cộng lên tới 256 vCPUs cho các máy ảo trên host đó.
- Khi nào nên thay đổi:
  - Tăng lên (ví dụ 32:1): Dùng cho môi trường Lab, Dev/Test, hoặc các ứng dụng Web nhẹ, ít tính toán.
  - Giảm xuống (ví dụ 2:1 hoặc 1:1): Dùng cho các ứng dụng tính toán nặng (High-Performance Computing), Database lớn hoặc Gaming.

**Ý nghĩa 16:1**:
- **Số 1 (Bên phải)**: Đại diện cho **1 Core vật lý** (Physical Core) hoặc 1 luồng xử lý (Thread) thật sự của CPU.
- **Số 16 (Bên trái)**: Đại diện cho **16 Core ảo** (Virtual CPU - vCPU) mà OpenStack "hứa" sẽ cấp cho các máy ảo.
- Nếu bạn đặt tỉ lệ 1:1, máy có 1 cores thì chỉ tạo được đúng 1 vCPU. Cực kỳ phí phạm tài nguyên vì máy ảo thường có rất nhiều thời gian rảnh (Idle).
- Con số 16 là con số mặc định (default) của OpenStack Nova. Các kỹ sư OpenStack cho rằng trong một môi trường điện toán đám mây thông thường, các máy ảo chỉ sử dụng trung bình khoảng 5-10% sức mạnh CPU. Do đó, việc "bán quá tay" gấp 16 lần là một con số an toàn về mặt thống kê.
- Trong thực tế, nếu CPU của bạn hỗ trợ Hyper-Threading (như các dòng Intel Xeon hay AMD EPYC), thì OpenStack sẽ nhìn nhận mỗi Thread là một Core vật lý.
- Nếu server có 16 Cores thật, nhưng có Hyper-Threading  Hệ điều hành nhận diện là 32 Threads.
- Số vCPU tối đa mà Nova cho phép tạo ra được tính như sau:
```bash
Tổng vCPU khả dụng = Số Core vật lý  x Tỉ lệ Overcommit (1x16)
```
- **lưu ý**: Đa số giờ các máy đều là đa luồng (Multi threads nên Số core vật lý giờ không chính xác mà phải là Số logical Processors)

### 2.1 Logical Processor
Để tối ưu hóa, các nhà sản xuất chip (Intel, AMD) sử dụng công nghệ gọi là Hyper-Threading (Siêu phân luồng) hoặc SMT (Simultaneous Multithreading).
  - Physical Core (Nhân vật lý): Là một đơn vị phần cứng thực thụ bên trong CPU, có đầy đủ mạch điện để tính toán.
  - Logical Processor (Nhân logic): Là "ảo ảnh" mà CPU tạo ra để đánh lừa hệ điều hành. Nhờ Siêu phân luồng, 1 nhân vật lý có thể xử lý cùng lúc 2 luồng công việc, khiến hệ điều hành tưởng rằng có 2 nhân.
  - Ví dụ: Nếu bạn mua một CPU có 16 Cores và có hỗ trợ Hyper-Threading, khi bạn vào Task Manager (Windows) hoặc gõ lệnh lscpu (Linux), bạn sẽ thấy hệ thống báo có 32 Logical Processors.

Nova Scheduler không quan tâm bạn có bao nhiêu "cục" phần cứng thật sự; nó nhìn vào số lượng nhân mà hệ điều hành (Hypervisor) báo cáo.
## 3. Overcommit RAM
Khác với CPU, RAM là tài nguyên "cứng". Nếu một máy ảo yêu cầu thêm RAM mà host vật lý đã cạn kiệt, hệ điều hành (Hypervisor) sẽ kích hoạt OOM Killer (Out of Memory Killer) để tiêu diệt các tiến trình nhằm bảo vệ hệ thống. Điều này cực kỳ nguy hiểm.
- Tỉ lệ mặc định(Default Ratio) là : 1.5:1 (Trong các phiên bản mới đôi khi là 1:1 để an toàn).
- Ý nghĩa: Nếu host có 100GB RAM, bạn có thể cấp phát tổng cộng 150GB RAM cho các máy ảo.
- Cơ chế hỗ trợ: Thường đi kèm với kỹ thuật Memory Ballooning (KVM), cho phép thu hồi RAM từ máy ảo đang rảnh để cấp cho máy ảo đang cần.
- Không nên đặt tỉ lệ RAM quá cao (trên 2.0) trừ khi bạn kiểm soát cực tốt hành vi của các ứng dụng bên trong máy ảo.

## 4. Cấu hình 
Cấu hình chỉ số ratio cho CPU và RAM ở file `/etc/nova/nova.conf` trên node Controller.

Bạn không thấy các dòng đó trong file nova.conf là vì: OpenStack sử dụng cơ chế "Default-if-Absent" (Mặc định nếu thiếu).

```bash
[DEFAULT]
cpu_allocation_ratio = 0.0
ram_allocation_ratio = 0.0
disk_allocation_ratio = 0.0
```
Nếu ta để ratio là 0.0 thì chỉ số ratio mặc định của cpu, ram, disk là `16.0`, `1.5`, `1.0`

Sau khi cấu hình, restart lại dịch vụ của nova:
```bash
systemctl restart openstack-nova-api.service
systemctl restart openstack-nova-scheduler.service
systemctl restart openstack-nova-novncproxy.service
systemctl restart openstack-nova-conductor.service
```

## Lưu ý:
OpenStack chỉ hiển thị thống số tài nguyên thật, không hiển thị thông số tài nguyên ảo: