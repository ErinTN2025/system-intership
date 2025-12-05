# Tìm hiểu về LAMP Stack

![altimage](../Images/LAMP.png)

### I. LAMP là gì ?
LAMP là viết tắt của Linux, Apache, MySQL và ngôn ngữ văn lệnh PHP hay Perl hay Python, là một tập hợp các phần mềm mã nguồn mở được sử dụng phổ biến để xây dựng các trang web và ứng dụng web động.

### II. Ưu điểm của LAMP
Đặc trưng mã nguồn mở mang đến cho LAMP nhiều ưu điểm.
- **Mã nguồn mở**: Miễn phí sử dụng và sửa đổi, cộng đồng hỗ trợ lớn.
- **Linh hoạt**: Có thể tùy chỉnh và mở rộng để đáp ứng nhu cầu đa dạng.
- **Hiệu quả**: Hoạt động ổn định và hiệu quả trên nhiều nền tảng.
- **Dễ sử dụng**: Có nhiều tài liệu hướng dẫn và công cụ hỗ trợ.
### III. Nhược điểm của LAMP
- **Yêu cầu kiến thức kỹ thuật**: Cần có kiến thức về Linux, Apache, MySQL và PHP để cài đặt và cấu hình.
- **Bảo mật**: Cần cập nhật thường xuyên để đảm bảo an ninh mạng.

### III. Thành phần của LAMP
#### 1. Linux
Linux là lớp đầu tiên trong stack. Hệ điều hành này là cơ sở nền tảng cho các lớp phần mềm khác.

#### 2. Apache
Lớp thứ hai bao gồm phần mềm web server, thường là Apache Web (HTTP) Server.

Lớp này nằm trên lớp Linux. Web server chịu trách nhiệm chuyển đổi các web browser sang các website chính xác của chúng.

Đây là phần mềm máy chủ web phổ biến nhất trên mạng với độ an toàn, nhanh chóng, và đáng tin cậy. Bạn có thể tùy chỉnh để Apache hỗ trợ các ngôn nhữ web khác nhau như PHP, CGI / Perl, SSL, SSI, ePerl, và thậm chí ASP.

#### 3. MySQL
Lớp thứ ba là nơi cơ sở dữ liệu database được lưu trữ.

MySQL lưu trữ các chi tiết có thể được truy vấn bằng script để xây dựng một website.

Với tốc độ ổn định; độ bảo mật thông tin cao, dễ sử dụng và có tính khả chuyển, MySQL trở thành hệ quản trị cơ sở dữ liệu nguồn mở phổ biến nhất trên thế giới.

#### 4. PHP
PHP là lớp trên cùng của stack. Các website và ứng dụng web chạy trong lớp này.

PHP được phát triển như là một ngôn ngữ kịch bản trên máy chủ (server-side scripting language). 

# Tìm hiểu về LEMP Stack
**LEMP server** là một server chạy Linux, Nginx (đọc là Engine x), MySql và PHP (hoặc Perl/Python). Nó tương tự như LAMP server ngoại trừ việc web server nền tảng được giám sát bằng Nginx thay vì Apache.

**Nginx**

Nginx (đọc là engine x) là một phần mềm mã nguồn mở cho web serving, reverse proxying, caching, load balancing, media streaming,…Ban đầu nó giống như một web server được thiết kế để cho hiệu suất(performance) và tính ổn định(stability) cao nhất. Ngoài khả năng là 1 Web server, NGINX cũng có thể hoạt động như một proxy server cho email (IMAP, POP3 và SMTP) và reverse proxy và load balancer cho HTTP, TCP, và UDP server.

#### 5. Bảng so sánh

| Tiêu chí                                   | LAMP (Apache)                                                    | LEMP (Nginx)                                                     |
| ------------------------------------------ | ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Web server**                             | Apache HTTP Server                                               | Nginx (Engine-X)                                                 |
| **Mô hình xử lý**                          | Process-driven (mỗi request dùng 1 process hoặc 1 thread)        | Event-driven, non-blocking (một worker xử lý hàng nghìn request) |
| **Kiến trúc**                              | Multi-Process / Multi-Thread                                     | Asynchronous, event-loop                                         |
| **Hiệu năng tổng thể**                     | Tốt cho website vừa và nhỏ                                       | Rất cao, tối ưu website lớn và traffic cao                       |
| **Xử lý request đồng thời**                | Kém hơn khi lượng kết nối tăng cao (tốn RAM mỗi connection)      | Rất tốt, RAM gần như không tăng theo số kết nối                  |
| **Tài nguyên RAM**                         | Tiêu tốn RAM nhiều khi tải cao                                   | Tiêu tốn RAM rất thấp, ổn định dưới tải nặng                     |
| **Tốc độ file tĩnh (CSS/JS/Ảnh)**          | Trung bình                                                       | Rất nhanh (cạnh tranh với CDN nhỏ)                               |
| **Reverse Proxy**                          | Có thể dùng nhưng không tối ưu                                   | Tích hợp sẵn, hoạt động rất mạnh                                 |
| **Xử lý PHP**                              | Thường dùng mod_php hoặc PHP-FPM                                 | Tích hợp chặt với PHP-FPM, hiệu năng cao                         |
| **Hỗ trợ .htaccess**                       | Có hỗ trợ (ưu điểm lớn: cho phép override cấu hình theo thư mục) | Không hỗ trợ, mọi rewrite phải khai báo trong cấu hình Nginx     |
| **Rewrite URL (WordPress, Laravel...)**    | Dễ, chỉ cần chỉnh .htaccess                                      | Khó hơn, phải viết rule thủ công trong server block              |
| **Khả năng mở rộng (Scalability)**         | Vừa phải                                                         | Rất cao – phù hợp microservices, load balancing, API gateway     |
| **TLS/SSL**                                | Tốt                                                              | Rất tốt, hỗ trợ mạnh, kết hợp với OpenSSL và HTTP/2 hiệu quả     |
| **Hỗ trợ HTTP/2 / HTTP/3**                 | HTTP/2 tốt, HTTP/3 hạn chế                                       | HTTP/2 và HTTP/3 triển khai mạnh và ổn định                      |
| **Quản lý kết nối Keep-Alive**             | Ít tối ưu                                                        | Rất tối ưu, phục vụ nhiều kết nối dài                            |
| **Khả năng làm Load Balancer**             | Có nhưng ít dùng                                                 | Rất mạnh – thường dùng làm LB phía trước                         |
| **Khả năng xử lý static hosting**          | Thấp hơn Nginx                                                   | Cực nhanh                                                        |
| **Tương thích CMS (WordPress, Joomla...)** | Rất tốt, dễ cài, ít lỗi config                                   | Tốt nhưng phải config rewrite đúng                               |
| **Tính dễ dùng**                           | Dễ, đặc biệt cho người mới                                       | Khó hơn, cần hiểu cấu hình rõ ràng                               |
| **Cấu hình**                               | Dễ sửa nóng qua `.htaccess`                                      | Chỉnh config phải reload Nginx                                   |
| **Độ linh hoạt cấu hình**                  | Cao (nhờ .htaccess)                                              | Rất cao nhưng tập trung vào file cấu hình duy nhất               |
| **Tính ổn định**                           | Tốt                                                              | Rất ổn định, gần như không crash nếu cấu hình đúng               |
| **Bảo mật**                                | Tốt nhưng nhiều module, dễ misconfig                             | Ít module hơn, attack surface nhỏ hơn                            |
| **Hiệu năng tối đa**                       | Tối đa ở mức trung bình-cao                                      | Rất cao, tiêu chuẩn cho hệ thống lớn                             |
| **Ứng dụng phù hợp**                       | Blog, website nhỏ/trung bình, shared hosting                     | Website lớn, API server, WordPress traffic cao, load balancing   |
| **Dùng phổ biến ở**                        | Shared hosting, server giá rẻ                                    | VPS, Cloud, Enterprise, CDN Layer                                |
| **Khả năng xử lý tải bất ngờ**             | Kém ổn định hơn, dễ hết RAM                                      | Rất ổn định, buffer tốt                                          |
| **Triển khai Production hiện đại**         | Ít được dùng cho kiến trúc lớn                                   | Thường dùng: Nginx + PHP-FPM + Redis + MariaDB                   |
| **Hỗ trợ caching**                         | Không tối ưu bằng Nginx                                          | Rất mạnh: microcache, fastcgi cache                              |
| **Giấy phép**                              | Apache License 2.0                                               | BSD-2-Clause                                                     |
| **Tổng quan**                              | Dễ, linh hoạt, tốt cho người mới                                 | Mạnh, nhanh, tối ưu các hệ thống lớn                             |
