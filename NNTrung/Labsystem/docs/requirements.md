# Project Requirements

## Functional Requirements

- Người dùng truy cập website
- Người dùng có thể đăng ký tài khoản.
- Người dùng có thể đăng nhập.
- Người dùng có thể upload ảnh.

## Non Functional Requirements

### Security

- Toàn bộ truy cập phải dùng HTTPS.
- Chỉ mở các port cần thiết.

### Availability

- Hệ thống chạy được khi 1 backend bị lỗi.
- Reverse Proxy tự cân bằng tải.

### Database

- Database tách riêng.
- Database có persistent volume.
- Backup database hàng ngày.

### Monitoring

- Có SSH quản trị từ xa
- Có Prometheus.
- Có Grafana.

### Logging

- Có log tập trung.
- Log không mất khi container restart.



### Documentation

- Có README.
- Có sơ đồ kiến trúc.
- Có API Documentation.