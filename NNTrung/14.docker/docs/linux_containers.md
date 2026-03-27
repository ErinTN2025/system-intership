# Tổng quan về Linux Container (LXC)

## 1. Khái niệm

**Linux Containers (LXC)** là một công nghệ ảo hóa ở **cấp hệ điều hành (OS - level virtualization)**. Containers cho phép chạy nhiều môi trường cô lập(isolated envirmonets) trên cùng một nhân Linux (Linux Kernel), mà không cần phải tạo máy ảo riêng biệt.

Container là một đơn vị đóng gói (packaging) chứa toàn bộ môi trường cần thiết để chạy một ứng dụng (code, runtime, thư viện, biến môi trường, file cấu hình…). Nó chia sẻ kernel của hệ điều hành host, khác hoàn toàn với máy ảo (VM) phải có kernel riêng.

Mỗi container giống như một "máy tính nhỏ":
- có **file system riêng**
- có **process riêng**
- có **network interface riêng**
- Dùng chung **kernel** của hệ điều hành host.

```text
Nói cách khác: Containers chia sẻ kernel nhưng cô lập không gian người dùng (user space).
```

## 2. Cách container hoạt động (công nghệ nền tảng)

### 2.1 Namespaces (cô lập tài nguyên)

Namespace tạo ra "bản sao" của một loại tài nguyên, khiến container thấy một thế giới riêng biệt. Namespaces cung cấp sự cô lập (isolation) cho các tài nguyên hệ thống.

Mỗi container có thể thấy và dùng tài nguyên riêng của nó.

| Namespace | Công dụng chính | Ví dụ thực tế |
|-----------|-----------------|---------------|
| PID | Cô lập danh sách process | Container 1 thấy PID 1 là init của nó |
| Mount (mnt) | Cô lập hệ thống file (mount points)| Container có root filesystem riêng|
| Network (net)| Cô lập network stack (interface, IP, port…)| Mỗi container có IP riêng hoặc dùng bridge |
| UTS| Cô lập hostname và domain name| Container có hostname riêng|
| IPC| Cô lập cơ chế giao tiếp giữa process| Message queues, semaphores riêng|
| User| Cô lập user/group ID (UID/GID mapping)| Root trong container ≠ root trên host|
| Cgroup| Cô lập và giới hạn tài nguyên (cgroups v2)| (thường kết hợp với cgroup namespace) |
| Time| Cô lập đồng hồ (từ kernel 5.6) |Ít dùng|

Khi tạo container, kernel sẽ gán các namespace mới cho process đầu tiên (entrypoint) của container.

### 2.2 Control Groups (cgroups) - Giới hạn và kế toán tài nguyên
- cgroups v1 (cũ) và cgroups v2 (mặc định từ kernel 4.5+, được khuyến khích dùng).
- Cho phép giới hạn dùng tối đa bao nhiêu: CPU, Memory, I/O (blkio), Network bandwidth, số process, freeze/thaw…
- Theo dõi mức tiêu thụ tài nguyên
- Ngăn container chiếm dụng toàn bộ hệ thống
- Cgroup controller chính: cpu, memory, io, pids, devices, freezer…

### 2.3 Các cơ chế bổ trợ quan trọng
- **Capabilites**: Loại bỏ một số quyền root nguy hiểm (ví dụ: CAP_SYS_ADMIN, CAP_NET_ADMIN...).
- **Seccomp (Secure Computing)**: Bộ lọc syscall (chỉ cho phép một số system call nhất định).
- **SELinux/ AppArmor**: Mandatory Access Control (MAC) để giới hạn thêm.
- **Overlay filesystem/ Union filesystem**: (overlay2, aufs, btrfs…): cho phép nhiều layer chồng lên nhau -> image layer rất tiết kiệm dung lượng (layer chỉ chứa sự thay đổi).

## 3. Khác nhau giữa Container, Máy ảo (VM) và WSL-2
| Tiêu chí               | Linux Containers                              | Virtual Machine (VM)                                       | WSL2                                       |
| ---------------------- | --------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------ |
| **Kiến trúc**          | OS-level virtualization (chia sẻ kernel host) | Hardware-level virtualization (hypervisor như KVM, VMware) | Lightweight VM dựa trên Hyper-V            |
| **Kernel**             | Dùng chung kernel Linux host                  | Mỗi VM có kernel riêng                                     | Kernel Linux riêng (Microsoft build)       |
| **Cô lập (Isolation)** | Trung bình (namespaces + cgroups)             | **Cao nhất** (tách biệt hoàn toàn)                         | Cao (gần VM) nhưng tích hợp Windows        |
| **Hiệu suất**          | **Gần native (~98-99%)**                      | Thấp hơn (overhead 5–20%)                                  | Gần native, thường tốt hơn VM truyền thống |
| **Khởi động**          | Rất nhanh (ms → vài giây)                     | Chậm (30s → vài phút)                                      | Nhanh (vài giây)                           |
| **Tài nguyên**         | Rất nhẹ, dùng chung                           | Nặng (RAM/CPU riêng)                                       | Thấp → trung bình (dynamic memory)         |
| **Kích thước**         | Nhỏ (MB → vài trăm MB)                        | Lớn (GB)                                                   | Trung bình                                 |
| **Portability**        | **Cao nhất** (image chạy mọi nơi)             | Trung bình                                                 | Thấp (gắn với Windows)                     |
| **OS hỗ trợ** ⚠️       | Chỉ Linux (native)                            | **Chạy mọi OS** (Linux, Windows, BSD…)                     | Chỉ Linux trên Windows                     |
| **Tích hợp Windows**   | Thấp                                          | Trung bình                                                 | **Rất cao (native)**                       |
| **Docker support**     | Native, tốt nhất                              | Có nhưng nặng                                              | **Rất tốt (Docker Desktop backend)**       |
| **Bảo mật**            | Trung bình (phụ thuộc kernel)                 | **Cao nhất**                                               | Cao (VM isolation)                         |
| **Networking**         | Linh hoạt (bridge, overlay, service mesh)     | Giống máy thật                                             | NAT + integration với Windows              |
| **Storage**            | Layered filesystem (overlayfs)                | Disk ảo (VMDK, QCOW2)                                      | File system tích hợp Windows               |
| **GUI / Desktop**      | Có nhưng cần config (X11/Wayland)             | Tốt                                                        | **Rất tốt (WSLg)**                         |
| **Use case chính**     | Microservices, CI/CD, Kubernetes              | Multi-OS, production isolation, lab                        | Dev trên Windows, chạy tool Linux          |

# II. Các thành phần chính của Linux Container

![altimage](../images/Gemini_Generated_Image_a621j1a621j1a621.png)

**Lớp A**: Linux Kernel 
- Quản lý mọi tài nguyên phần cứng (CPU, RAM, Ổ đĩa, Mạng). Nếu không có Kernel, container không thể tồn tại.

- Container không có Kernel riêng. Chúng "dùng chung" Kernel với máy chủ (Host). Vì vậy, lớp A này chính là nơi Kernel "phân chia" chính nó để tạo ra các không gian riêng biệt cho mỗi container.

## 1. Namespaces 
Namespaces thực hiện việc "che mắt" và "phân chia" hệ thống thành các không gian khác nhau. Đây là tính năng quan trọng nhất để tạo ra "ảo giác" cho container. Nó khiến container nghĩ rằng nó đang là một máy ảo độc lập, trong khi thực tế nó chỉ là một tiến trình (process) bình thường.
## 2. cgroups (Control Groups) - Quản lý tài nguyên
Nếu một container bị lỗi và chiếm toàn bộ CPU/RAM của máy chủ, tất cả các container khác sẽ bị "chết đứng". cgroups ra đời để ngăn chặn điều này. Nó cho phép bạn đặt giới hạn cứng:
- **CPU**: Container A chỉ được dùng tối đa 50% của 1 CPU.
- **RAM**: Container B chỉ được dùng tối đa 2GB RAM. Nếu dùng quá, nó sẽ bị Kernel "kill" (lỗi OOM - Out of Memory) để bảo vệ hệ thống.
- **I/O (Đĩa/Mạng)**: Giới hạn tốc độ đọc/ghi dữ liệu.

## 3. Overlay/Union Filesystem Drivers - Lưu trữ