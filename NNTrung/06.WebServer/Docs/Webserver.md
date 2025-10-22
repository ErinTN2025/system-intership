# Web Server
### 1. Khái niệm
Web Server (máy chủ web) là một phần mềm hoặc máy tính có nhiệm vụ lưu trữ, xử lý và phân phối nội dung web (HTML, CSS, JS, hình ảnh, video...) đến trình duyệt của người dùng qua giao thức HTTP hoặc HTTPS. 

### 2. Cấu trúc của Web Server
| Phần                     | Mô tả                                                                      |
| ------------------------ | -------------------------------------------------------------------------- |
| **Phần cứng (Hardware)** | Là máy tính vật lý hoặc máy ảo, có cấu hình mạnh, lưu trữ dữ liệu website. |
| **Phần mềm (Software)**  | Là chương trình xử lý yêu cầu web (ví dụ: NGINX, Apache, LiteSpeed, IIS).  |

### 3. Cách thức hoạt động của Web Server

![altimage](../Images/webserverworks.png)

- **Client gửi request**: Trình duyệt gửi một yêu cầu HTTP/HTTPS đến địa chỉ IP của máy chủ (ví dụ: `GET /index.html`).
- **DNS phân giải tên miền**: Tên miền (`example.com`) được chuyển thành địa chỉ IP của server.
  - Tìm kiếm ở trong cache
  - Gửi các yêu cầu tìm kiếm tới DNS Servers. ( Bất kì website nào đều phải đăng kkys địa chỉ IP khi tạo trên webserver)
- **Trình duyệt yêu cầu full URL**: Sau khi biết địa chỉ IP, trình duyệt yêu cầu full URL từ web server.
- **Kết nối TCP/SSL**: Trình duyệt thiết lập kết nối với web server qua cổng: 80 (HTTP),  443 (HTTPS)
- **Web Server nhận yêu cầu**: Phần mềm (NGINX, Apache...) đọc yêu cầu và xác định file hoặc dịch vụ cần trả về.
- **Xử lý yêu cầu**: Nếu là file tĩnh (HTML, ảnh, video): gửi thẳng về.
  - Nếu là nội dung động (PHP, Python, Node.js...): chuyển cho Application Server xử lý (qua CGI, FastCGI, proxy...).

  ![altimahe](../Images/Webserverreply.png)

- **Trả phản hồi (Response)**: Server gửi lại nội dung + mã trạng thái HTTP (ví dụ: `200 OK`, `404 Not Found`).
- **Client hiển thị nội dung**: Trình duyệt hiển thị trang web cho người dùng.

### 4. Web Server xử lý loại dữ liệu
| Loại dữ liệu      | Ví dụ                                    | Xử lý bởi                                           |
| ----------------- | ---------------------------------------- | --------------------------------------------------- |
| **File tĩnh**     | HTML, CSS, JS, PNG, JPG                  | Web Server (ví dụ NGINX)                            |
| **Nội dung động** | Trang PHP, Python Flask, Node.js Express | Application Server (chạy qua web server trung gian) |


https://www.linkedin.com/pulse/how-do-web-servers-work-priyanka-kumari/