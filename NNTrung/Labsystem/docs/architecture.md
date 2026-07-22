# Kiến Trúc Triển Khai Hệ Thống Flasky

## 1. Mô Hình Triển Khai (Deployment Model)

Tổng số lượng: **5 VMs** 

| VM / Thành phần | Số lượng | Mô tả chức năng |
| --- | --- | --- |
| **Load Balancer & Gateway** | 1 | Cân bằng tải, tiếp nhận và điều hướng traffic |
| **Backend** | 2 | Chạy ứng dụng web, xử lý logic, giảm tắc nghẽn traffic |
| **Database+Cache+MinIO** | 1 | Lưu trữ dữ liệu hệ thống <br>• **Cache :** Quản lý cache (Redis)<br> |
| **Monitoring** | 1 | Theo dõi, giám sát & quản lý tài nguyên hệ thống<br> • **CI/CD:** Tự động hóa đóng gói, kiểm thử & triển khai phần mềm • **Backup Script:** Tự động sao lưu dữ liệu, phòng chống sự cố<br>|



## 2. Cấu Hình Hệ Điều Hành (OS Configurations)

Các tham số cấu hình chung dưới đây được áp dụng đồng bộ cho các máy trong hệ thống.

| Thông số / Service        | Cấu hình áp dụng                                                 |
| ------------------------- | ---------------------------------------------------------------- |
| **Hệ điều hành (OS)**     | Ubuntu Server 22.04.5 LTS (Jammy Jellyfish)                      |
| **Timezone**              | Asia/Ho_Chi_Minh (UTC+7)                                         |
| **Time Synchronization**  | Chrony                                                           |
| **Locale**                | C.UTF-8                                                          |
| **Hostname**              | Theo vai trò của từng máy (proxy, app01, app02, db, monitor,...) |
| **DNS Server**            | 8.8.8.8                                                          |
| **SSH Server**            | OpenSSH Server                                                   |
| **Firewall**              | Iptables                                                         |
| **Swap**                  | Disable                                                          |
| **System Update**         | apt update && apt upgrade (Update mới nhất ngày 20/07/2026)      |
| **Docker**         | docker cli, docker engine bản 29.6.0-1 ubuntu.22.04 jammy, containerd.io, docker-buildx-plugin, docker-compose-plugin                                      |

## 3. Những phần mềm cài đặt trên từng máy
### 3.1 Load Balancer
- HA Proxy 
- Openssh client
- node_exporter
- auditd
### 3.2 Web1+2
- Promtail
- Openssh client
- node_exporter
- auditd
### 3.3 DB+MinIO+Cache
Quản trị:
- Openssh cli
- auditd
Database:
- MariaDB
- node_exporter
- mysql_exporter
Backend Storage 1 trong 2 phương án dưới đây:
- NFS Share
- MinIO
- auditd
- Redis: lưu cache

### 3.4 Monitor quản lý
Monitoring:
- Prometheus
- Grafana
- Loki (nếu giữ)
- Docker (chạy 3 service trên dạng container)

Backup:
- Cron (có sẵn trong OS, chỉ cần viết script + đăng ký lịch)
- mariadb-client (để chạy lệnh mysqldump từ xa tới VM db)
- mc (MinIO Client) hoặc rsync (đẩy file backup từ VM db về đây, hoặc ngược lại)
- gzip (nén file backup trước khi lưu)

CI/CD:
- GitHub Actions self-hosted runner
- Docker cli (runner cần Docker để build image)
- Ansible hoặc chỉ cần SSH client (để deploy sang web1/web2 sau khi build xong)

Quản trị:
- OpenSSH Server
- Auditd

## 4. Network

![altimage](../image/Screenshot_51.png)

| Services | IP Subnet | 
|----------|-----------|
| Public - Frontend | 10.0.10.0/24 | 
| Application | 10.0.20.0/24 | 
| Backend/Data | 10.0.30.0/24 | 
| Management | 10.0.40.0/24 |

Lý do phải chia Subnet: 
- Đảm bảo security, đường truyền của Flask server tới database không ai ngoài Flask và Server thấy được.
- Giảm broadcast domain, đặc biệt khi mạng lớn.
- QoS ưu tiên traffic
- Tối ưu vận hành
---

## 5. VM desin

| **VM** | **IP**|  **Memory**| **Processors** | **Hard Disk( bao gồm cả OS)** |
|---|----|----|---|--|
| LB | NIC 1: 10.0.10.10 - NIC 2: 10.0.20.19 - NIC 3: 10.0.40.36 | 2GB | 2 | 20GB (1 ổ sda) | 
| web1 | NIC 1: 10.0.20.20 - NIC 2: 10.0.30.28 - NIC 3: 10.0.40.37 | 2GB | 2 | 20GB (1 ổ sda)  |
| web2 | NIC 1: 10.0.20.21 - NIC 2: 10.0.30.29 - NIC 3: 10.0.40.38| 2GB | 2 | 20GB (1 ổ sda) |
| db+MinIO+cache | NIC 1: 10.0.30.30 - NIC 2: 10.0.40.39 | 2GB | 2 | 20GB (1 ổ sda) |
| Monitor | NIC 1: 10.0.40.40 | 3GB | 2 | 20GB (1 ổ sda) |

## 6. Port Matrix

LB:

| Source   | Destination | Port | Sử dụng cho   |
| -------- | ----------- | ---- | ------------- |
| Internet | LB          | 80   | HTTP          |
| Internet | LB          | 443  | HTTPS         |
| Monitor  | LB          | 22   | SSH           |
| Monitor  | LB          | 9100 | node_exporter |
| LB       | Monitor     | 3100 | Loki          |
| Monitor  | LB  | 9115 | blackbox_exporter   |

Web1 + 2:

| Source   | Destination | Port | Sử dụng cho   |
| -------- | ----------- | ---- | ------------- |
| LB       | Web1/Web2   | 5000 | Reverse Proxy |
| Web1/Web2| DB+MinIO+Cache | 3306 | Database   |
| Web1/Web2| DB+MinIO+Cache | 6379 | Cache      |
| Monitor  | Web1/Web2   | 22   | SSH           |
| Monitor  | Web1/Web2   | 9100 | node_exporter |
| Web1/Web2| Monitor     | 3100 | Loki          |
| Monitor  | Web/Web2  | 9115 | blackbox_exporter   |

DB+MinIO+Cache Server:

| Source   | Destination     | Port | Sử dụng cho     |
| -------- | --------------- | ---- | --------------- |
| Web1/Web2| DB+MinIO+Cache  | 3306 | Database        |
| Web1/Web2| DB+MinIO+Cache  | 6379 | Cache           |
| Web1/Web2| DB+MinIO+Cache  | 9000 | MinIO API       |
| Monitor  | DB+MinIO+Cache  | 22   | SSH             |
| Monitor  | DB+MinIO+Cache  | 9001 | MinIO Console   |
| Monitor  | DB+MinIO+Cache  | 9100 | node_exporter   |
| Monitor  | DB+MinIO+Cache  | 9104 | mysqld_exporter |
| Monitor  | DB+MinIO+Cache  | 9121 | redis_exporter  |
| Monitor  | DB+MinIO+Cache  | 9115 | blackbox_exporter   |
| DB+MinIO+Cache | Monitor   | 3100 | Loki            |

Monitor:

| Source   | Destination | Port | Sử dụng cho          |
| -------- | ----------- | ---- | -------------------- |
| Admin    | Monitor     | 22   | SSH quản trị         |
| LB       | Monitor     | 3100 | Loki nhận log        |
| Web1/Web2| Monitor     | 3100 | Loki nhận log        |
| DB+MinIO+Cache | Monitor | 3100 | Loki nhận log     |
| Monitor  | DB+MinIO+Cache | 3306 | Backup (mysqldump, pull) |
| Monitor  | GitHub (Internet) | 443 | CI/CD pull image/code |


## 7. Audit
- Others không có bất cứ quyền gì 
  - Không phải file công khai chặn hết quyền người ngoài xem hay truy cập.
- Mỗi Service sẽ là 1 system user riêng
  - Đảm bảo khi 1 user bị đụng chạm chỉ 1 dịch vụ bị ảnh hưởng, không lây lan sang các dịch vụ khác.
- Các file thông thường: 750
  - Người sở hữu có toàn quyền, những người trong group được chỉ định chỉ có quyền xem không được chỉnh sửa file.
- File Backup : 700

## 8. Check list
### Chỉ có duy nhất 1 LB
- Hiện tại chỉ có duy nhất 1 LB nếu LB sập thì cả hệ thống cũng sẽ sập theo, đề xuất dùng Keepalive + VIP, khi triển khai thực tế tối thiểu 3 node LB.
### Backend 
- Mô phỏng 2 backend, làm giảm tải cho 1 node duy nhất nhờ cơ chế xoay vòng round robin. Nếu 1 node chết, node còn lại vẫn còn có thể tạm thời chống đỡ.
### Database + Cache + Object Storage
- Thiết kế nên chỉ riêng từng cụm clu
ster Database, Redis, MinIO. Khi 1 cụm bị mất vẫn còn các cụm còn lại lưu thông tin.
### Audit
- Nếu 1 dịch vụ bị đổi quyền sở hữu, daemon của dịch vụ đó sẽ bị crash
- blackbox_exporter là dịch vụ quan sát port trên máy bị tắt đó và báo lại về cho Monitor
- auditd rule xác định thời điểm nào ai đã làm gì chown/chmod, ...
- Loki log theo dõi lỗi Permission denied khi dịch vụ cố khởi động lại.
### Network 
- Cấu hình Iptables chặn các port không cần thiết - thiết kế port matrix trước để tránh nhầm lẫn.
- DNS trỏ đến 1 trong những DNS server public của google: chuẩn bị thêm DNS server dự phòng ngoài 8.8.8.8
- Ghi chép quản lý Network chi tiết cụ thể. Network được chia từng dải cô lập.
- DB, Cache, Redis dùng chung 1 máy ảo nhưng container của chúng chia dải riêng.
### Hardware
- Đo hiệu suất RAM CPU: node-exporter trên từng node và Prometheus ở Monitor để quản 
- Quản lý dung lượng ổ cứng
- Đo tổng số Inode, inode còn trống
### Backup 
- Có định hướng thiết kế backup file bị hỏng
### Datasaved
- MinIO/ Redis không bị mất dữ liệu khi restart 