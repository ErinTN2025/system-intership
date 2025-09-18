# User và Group trong Linux
### Khái niệm User trong Linux
- User đại diện cho một thực thể( thường là một người) hoặc một tiến trình có thể tương tác với hệ thống. Mỗi user có một danh tính riêng và được hệ thống xác thực khi đăng nhập hoặc thực hiện các tác vụ.
- **User ID(UID)**: Mỗi user được gán một số định danh duy nhất gọi là User ID(UID). UID được sử dụng bởi kernel để xác định user khi thực hiện các hoạt động liên quan đến quyền truy cập.
  - UID 0: Thường dành cho root user (superuser).
  - UID 1-999 (hoặc một khoảng tương tự): Thường dành cho các system user và service account, được hệ thống hoặc các ứng dụng tạo ra để chạy các dịch vụ.
  - UID 1000 trở lên (hoặc một khoảng tương tự): Thường dành cho các regular user (người dùng thông thường).