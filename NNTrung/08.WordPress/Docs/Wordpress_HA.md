# Tìm hiểu về Wordpress HA
## 1. WordPress HA là gì?
WordPress HA (High Availability) là kiến trúc triển khai WordPress đảm bảo khả năng sẵn sàng cao, nghĩa là website WordPress luôn hoạt động ổn định, giảm thiểu tối đa thời gian gián đoạn dịch vụ khi xảy ra lỗi phần cứng, lỗi mạng hoặc bảo trì.
## 2. Tại sao cần HA cho WordPress?
- Website không bị downtime, đảm bảo trải nghiệm người dùng.
- Hạn chế mất doanh thu (đối với website thương mại điện tử).
- Tăng độ tin cậy và uy tín của hệ thống.
## 3. Kiến trúc WordPress HA cơ bản
### 3.1 Load Balancer (Cân bằng tải):

- Phân phối request đến nhiều server backend chạy WordPress.

- Ví dụ: Nginx, HAProxy hoặc AWS Elastic Load Balancing.

### 3.2 Nhiều Web Server chạy WordPress:

- Các instance WordPress chạy song song (ngang hàng).

- Mã nguồn đồng bộ qua NFS, EFS, GlusterFS hoặc CI/CD.

### 3.3 Database Cluster:

- MySQL replication (Master-Slave hoặc Multi-Master).

- Hoặc dùng dịch vụ Database Managed (Amazon RDS Multi-AZ).

### 3.4 Shared Storage (Lưu trữ chung):

- Chia sẻ thư mục wp-content/uploads giữa các node.

- Có thể dùng NFS, EFS (AWS), hoặc plugin đồng bộ S3.

### 3.5 Health Check + Failover:

- Giám sát dịch vụ, tự động chuyển hướng traffic khi server hỏng.

# Lab về WordPress HA
### 1. Môi trường
| **Máy ảo** | **OS** | **Vai trò** |
|------------|--------|-------------|
|Web-server1 | CentOS Stream 9 | Web  |
|Web-server2 | Ubuntu 24.04 | 