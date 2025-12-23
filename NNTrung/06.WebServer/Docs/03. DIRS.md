# DIRECTIVES APACHE

## A. TRÊN CENTOS 9

### I. TOÀN BỘ FILE VÀ DIRECTORY QUAN TRỌNG

#### 1. `/etc/httpd/` # Thư mục cấu hình chính của Apache  

├── `conf/`                                     # Các file cấu hình chính  
│   ├── `httpd.conf`                            # File config chính nhất, chỉnh hết ở đây  
│   └── `magic`                                 # File nhận diện loại file (MIME type)  
│  
├── `conf.d/`                                   # Thư mục config phụ (tự động load khi khởi động)  
│   ├── `autoindex.conf`                        # Cấu hình hiển thị danh sách file trong thư mục  
│   ├── `userdir.conf`                          # Cấu hình thư mục cá nhân user (vd: ~username)  
│   ├── `welcome.conf`                          # Trang chào mừng mặc định khi vào localhost  
│   ├── `ssl.conf`                              # Cấu hình HTTPS/SSL (cần cài mod_ssl)  
│   └── `*.conf`                                # ĐẶT FILE VIRTUAL HOST TÙY CHỈNH Ở ĐÂY  
│  
├── `conf.modules.d/`                           # Thư mục quản lý các module (plugin) của Apache  
│   ├── `00-mpm.conf`                           # Cấu hình xử lý đa luồng/đa tiến trình  
│   ├── `00-optional.conf`                      # Các module tùy chọn, không bắt buộc  
│   ├── `00-proxy.conf`                         # Module làm proxy/load balancer  
│   ├── `00-ssl.conf`                           # Module hỗ trợ SSL/TLS  
│   ├── `00-systemd.conf`                       # Tích hợp với systemd của Linux  
│   ├── `10-h2.conf`                            # Hỗ trợ HTTP/2 (nhanh hơn HTTP/1.1)  
│   ├── `10-proxy_h2.conf`                      # Proxy HTTP/2  
│   └── `README`                                # File hướng dẫn về modules  
│  
├── `logs` -> `/var/log/httpd/`                   # Link tắt đến thư mục log  
├── `modules` -> `/usr/lib64/httpd/modules/`      # Link tắt đến thư mục chứa module  
├── `run` -> `/run/httpd/`                        # Dữ liệu runtime (PID, socket...)  
└── `state` -> `/var/lib/httpd/`                  # Dữ liệu trạng thái của Apache  
  
#### 2. `/var/www/` # Thư mục chứa nội dung website
  
├── `html/`                                     # Thư mục gốc website mặc định (DocumentRoot)  
│   └── `index.html`                            # Trang chủ - file đầu tiên hiển thị  
│  
├── `cgi-bin/`                                  # Thư mục chứa script CGI (Perl, Python, Shell...)  
│   └── (rỗng hoặc có các script CGI)  
│  
└── `error/`                                    # Thư mục chứa trang lỗi tùy chỉnh  
    ├── `HTTP_BAD_GATEWAY.html.var`             # Trang lỗi 502 Bad Gateway  
    ├── `HTTP_BAD_REQUEST.html.var`             # Trang lỗi 400 Bad Request  
    ├── `HTTP_FORBIDDEN.html.var`               # Trang lỗi 403 Forbidden (không có quyền)  
    ├── `HTTP_GONE.html.var`                    # Trang lỗi 410 Gone  
    ├── `HTTP_INTERNAL_SERVER_ERROR.html.var`   # Trang lỗi 500 Internal Server Error  
    ├── `HTTP_LENGTH_REQUIRED.html.var`         # Trang lỗi 411 Length Required  
    ├── `HTTP_METHOD_NOT_ALLOWED.html.var`      # Trang lỗi 405 Method Not Allowed  
    ├── `HTTP_NOT_FOUND.html.var`               # Trang lỗi 404 Not Found (không tìm thấy)  
    ├── `HTTP_NOT_IMPLEMENTED.html.var`         # Trang lỗi 501 Not Implemented  
    ├── `HTTP_PRECONDITION_FAILED.html.var`     # Trang lỗi 412 Precondition Failed  
    ├── `HTTP_REQUEST_ENTITY_TOO_LARGE.html.var`# Trang lỗi 413 Request Too Large  
    ├── `HTTP_REQUEST_TIME_OUT.html.var`        # Trang lỗi 408 Request Timeout  
    ├── `HTTP_REQUEST_URI_TOO_LARGE.html.var`   # Trang lỗi 414 URI Too Long  
    ├── `HTTP_SERVICE_UNAVAILABLE.html.var`     # Trang lỗi 503 Service Unavailable  
    ├── `HTTP_UNAUTHORIZED.html.var`            # Trang lỗi 401 Unauthorized (chưa đăng nhập)  
    ├── `HTTP_UNSUPPORTED_MEDIA_TYPE.html.var`  # Trang lỗi 415 Unsupported Media Type  
    ├── `HTTP_VARIANT_ALSO_VARIES.html.var`     # Trang lỗi 506 Variant Also Negotiates  
    ├── `README`                                # Hướng dẫn tùy chỉnh error pages  
    ├── `contact.html.var`                      # Template trang liên hệ admin  
    └── `include/`                              # Các file include cho error pages  
  
#### 3.`/var/log/httpd/` # Thư mục chứa file log của Apache  
  
├── `access_log`                                # Log ghi lại TẤT CẢ request truy cập  
├── `error_log`                                 # Log ghi lại TẤT CẢ lỗi xảy ra  
├── `ssl_access_log`                            # Log HTTPS access (nếu dùng SSL)  
├── `ssl_error_log`                             # Log lỗi HTTPS  
└── `ssl_request_log`                           # Log chi tiết SSL handshake  
  
#### 4.`/usr/lib64/httpd/modules/` # Thư mục chứa các module của Apache (file .so)  
  
├── `mod_access_compat.so`                      # Module tương thích access control cũ  
├── `mod_actions.so`                            # Module thực thi action dựa trên MIME type  
├── `mod_alias.so`                              # Module tạo alias URL (đổi đường dẫn)  
├── `mod_allowmethods.so`                       # Module giới hạn HTTP methods cho phép  
├── `mod_auth_basic.so`                         # Module xác thực cơ bản (username/password)  
...  
  
#### 5.`/usr/sbin/` # Thư mục chứa các lệnh quản trị Apache
  
├── `httpd`                                     # File chương trình Apache chính  
├── `apachectl`                                 # Script điều khiển Apache (start/stop/restart)  
├── `htcacheclean`                              # Dọn dẹp cache disk  
├── `rotatelogs`                                # Công cụ xoay vòng log files  
├── `suexec`                                    # Chạy CGI với quyền user khác  
└── `fcgistarter`                               # Khởi động FastCGI processes  
  
#### 6.`/usr/bin/` # Công cụ tiện ích Apache  
  
├── `ab`                                        # Apache Benchmark - test tải website  
├── `htdbm`                                     # Quản lý password trong DBM database  
├── `htdigest`                                  # Tạo file digest authentication  
├── `htpasswd`                                  # Tạo/quản lý file password (CỰC HAY DÙNG!)  
├── `httxt2dbm`                                 # Chuyển text file sang DBM  
└── `logresolve`                                # Phân giải IP thành hostname trong log  

#### 7.`/run/httpd/` # Thư mục runtime (tạm thời khi Apache chạy)  
  
├── `httpd.pid`                                 # File chứa Process ID của Apache  
└── (socket files)                            # Các Unix socket files nếu có  

#### 8.`/var/lib/httpd/`                              # Dữ liệu state của Apache  
  
└── (runtime state data)                      # Dữ liệu trạng thái tạm thời  
  
#### 9.`/usr/share/httpd/` # Dữ liệu dùng chung của Apache  
  
├── `error/`                                    # Template các trang lỗi  
│   └── (error page templates)  
├── `icons/`                                    # Các icon mặc định cho autoindex  
│   ├── `small/`                               # Icons nhỏ  
│   ├── `README`                               # Hướng dẫn  
│   ├── `a.gif`, `apache_pb.gif`, `back.gif`...   # Các file icon  
│   └── (nhiều icons khác)  
├── `noindex/`                                  # Assets cho trang welcome mặc định  
│   ├── `css/`                                 # File CSS  
│   └── `images/`                              # Hình ảnh  
└── `manual/`                                   # Tài liệu Apache (nếu cài package httpd-manual)  
  
#### 10.`/etc/sysconfig/` # Cấu hình hệ thống  

└── `httpd`                                     # Biến môi trường cho Apache  
  
#### 11.`/etc/systemd/system/` # Override systemd services  
  
└── `httpd.service`                            # Override service (nếu có)  
  
#### 12.`/usr/lib/systemd/system/` # Systemd units mặc định  

├── `httpd.service`                            # Service chính của Apache  
├── <httpd@.service>                           # Template chạy nhiều instance Apache  
├── `httpd.socket`                            # Socket activation  
└── `htcacheclean.service`                     # Service dọn cache tự động  
  
#### 13./var/cache/httpd/ # Thư mục cache của Apache  

└── (cache files nếu bật mod_cache)          # File cache nếu dùng module cache  
  
#### 14.`/etc/logrotate.d/` # Cấu hình tự động xoay vòng log  

└── `httpd`                                    # Rules để rotate log Apache tự động  

### II. SCRIPT BACKUP TOÀN BỘ CONFIG

```bash
#!/bin/bash
# Backup Apache config

BACKUP_DIR="/root/apache_backup_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

# Backup configs
cp -r /etc/httpd/conf/ "$BACKUP_DIR/"
cp -r /etc/httpd/conf.d/ "$BACKUP_DIR/"
cp -r /etc/httpd/conf.modules.d/ "$BACKUP_DIR/"

# Backup website
cp -r /var/www/ "$BACKUP_DIR/"

# Backup logs (10000 dòng cuối)
tail -10000 /var/log/httpd/access_log > "$BACKUP_DIR/access_log"
tail -10000 /var/log/httpd/error_log > "$BACKUP_DIR/error_log"

# Lưu thông tin hệ thống
httpd -V > "$BACKUP_DIR/httpd_version.txt"
httpd -M > "$BACKUP_DIR/httpd_modules.txt"
httpd -S > "$BACKUP_DIR/httpd_vhosts.txt"

# Nén lại
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "✅ Backup completed: $BACKUP_DIR.tar.gz"
```

Lưu thành `backup_apache.sh` và chạy:

```bash
chmod +x backup_apache.sh
sudo ./backup_apache.sh
```

### III. CÁC LỆNH QUAN TRỌNG TRÊN CENTOS 9

```bash
# Quản lý service
sudo systemctl start httpd          # Khởi động
sudo systemctl stop httpd           # Dừng
sudo systemctl restart httpd        # Khởi động lại (dừng hẳn rồi start)
sudo systemctl reload httpd         # Reload config (không ngắt kết nối)
sudo systemctl status httpd         # Xem trạng thái
sudo systemctl enable httpd         # Tự động khởi động cùng hệ thống
sudo systemctl disable httpd        # Tắt tự động khởi động

# Quản lý modules
sudo httpd -M                       # Xem modules đang bật
sudo vi /etc/httpd/conf.modules.d/00-proxy.conf   # Bật/tắt module bằng cách uncomment dòng LoadModule
sudo dnf install mod_ssl -y         # Cài module SSL
sudo dnf install mod_proxy -y       # Cài module proxy
sudo systemctl reload httpd         # Nạp lại cấu hình sau khi thay đổi module

# Quản lý sites (Virtual Hosts)
sudo vi /etc/httpd/conf.d/mysite.conf        # Tạo virtual host
sudo mv /etc/httpd/conf.d/000-default.conf.disabled  # Tắt site mặc định
sudo systemctl reload httpd                  # Nạp lại cấu hình

# Quản lý configs
sudo vi /etc/httpd/conf/httpd.conf           # File config chính
sudo vi /etc/httpd/conf.d/security.conf      # File config phụ (tùy chọn)
sudo systemctl reload httpd                  # Nạp lại cấu hình

# Kiểm tra cấu hình
sudo apachectl configtest           # Test syntax config
sudo apachectl -t                   # Test syntax (ngắn gọn)
sudo apachectl -S                   # Xem virtual hosts
sudo apachectl -M                   # Xem modules đang load
sudo apachectl -V                   # Xem version và compile options

# Firewall & SELinux
sudo firewall-cmd --permanent --add-service=http   # Mở cổng HTTP
sudo firewall-cmd --permanent --add-service=https  # Mở cổng HTTPS
sudo firewall-cmd --reload                         # Nạp lại tường lửa
sudo setsebool -P httpd_can_network_connect 1      # Cho phép Apache kết nối mạng

# Log
sudo tail -f /var/log/httpd/access_log     # Theo dõi access log
sudo tail -f /var/log/httpd/error_log      # Theo dõi error log
sudo less /var/log/httpd/error_log         # Đọc error log
```

## B. TRÊN UBUNTU

### I.TOÀN BỘ FILE VÀ DIRECTORY QUAN TRỌNG

#### 1.`etc/apache2/` # Thư mục cấu hình chính của Apache

├── `apache2.conf`                              # File cấu hình CHÍNH NHẤT của Apache  
├── `envvars`                                   # Các biến môi trường (user, group, đường dẫn...)  
├── `magic`                                     # File nhận diện loại file tự động  
├── `ports.conf`                                # Cấu hình các PORT mà Apache lắng nghe (80, 443...)  
│  
├── `mods-available/`                          # Thư mục chứa TẤT CẢ modules có thể dùng (chưa bật)  
│   ├── `access_compat.load`                   # Module tương thích với cách phân quyền cũ  
│   ├── `actions.load`                         # Module chạy action theo loại file  
│   ├── `alias.load`                           # Module tạo bí danh cho đường dẫn URL  
│   ├── `allowmethods.load`                    # Module giới hạn các phương thức HTTP được phép  
|   ├──  ....  
│   ├── `userdir.conf`                         # File cấu hình userdir  
│   ├── `usertrack.load`                       # Theo dõi người dùng bằng cookie  
│   ├── `vhost_alias.load`                     # Virtual hosting động  
│   └── `xml2enc.load`                         # Mã hóa XML  
│  
├── `mods-enabled/`                            # Thư mục chứa modules đang BẬT (link tượng trưng)  
│   ├── `access_compat.load` -> `../mods-available/access_compat.load`  
│   ├── `alias.load` -> `../mods-available/alias.load`  
│   ├── `auth_basic.load` -> `../mods-available/auth_basic.load`  
│   ├── `authn_core.load` -> `../mods-available/authn_core.load`  
│  
├── `conf-available/`                          # Các file cấu hình bổ sung có sẵn (chưa bật)  
│   ├── `charset.conf`                         # Cấu hình bảng mã ký tự  
│   ├── `localized-error-pages.conf`           # Trang lỗi đa ngôn ngữ  
│   ├── `other-vhosts-access-log.conf`         # Log cho các virtual hosts khác  
│   ├── `security.conf`                        # Cấu hình bảo mật (QUAN TRỌNG!)  
│   └── `serve-cgi-bin.conf`                   # Cấu hình thư mục CGI  
│  
├── `conf-enabled/`                            # Các file cấu hình đang BẬT (link tượng trưng)  
│   ├── `charset.conf` -> `../conf-available/charset.conf`  
│   ├── `localized-error-pages.conf` -> `../conf-available/localized-error-pages.conf`  
│   ├── `other-vhosts-access-log.conf` -> `../conf-available/other-vhosts-access-log.conf`  
│   ├── `security.conf` -> `../conf-available/security.conf`  
│   └── `serve-cgi-bin.conf` -> `../conf-available/serve-cgi-bin.conf`  
│  
├── `sites-available/`                         # Tất cả Virtual Hosts có sẵn (chưa chạy)  
│   ├── `000-default.conf`                     # Virtual host mặc định (HTTP)  
│   ├── `default-ssl.conf`                     # Virtual host mặc định (HTTPS)  
│   └── `*.conf`                               # ĐẶT FILE VIRTUAL HOST TÙY CHỈNH Ở ĐÂY  
│  
├── `sites-enabled/` # Virtual Hosts đang CHẠY (link tượng trưng)  
│   └── `000-default.conf` -> `../sites-available/000-default.conf`  
│  
└── `conf.d/`                                  # Thư mục config bổ sung (ít dùng, lỗi thời)  
  
#### 2.`/var/www/` # Thư mục chứa nội dung các website  

├── `html/`                                    # Thư mục gốc website mặc định  
│   └── `index.html`                           # Trang chủ mặc định  
│  
└── (các thư mục website khác của bạn)         # Đặt các website khác ở đây  
  
#### 3.`/var/log/apache2/` # Thư mục chứa tất cả file log  

├── `access.log`                               # Log ghi lại TẤT CẢ request truy cập  
├── `error.log`                                # Log ghi lại TẤT CẢ lỗi xảy ra  
├── `other_vhosts_access.log`                  # Log của các virtual hosts khác  
└── `*.log`                                    # Các file log tùy chỉnh của từng site  
  
#### 4.`/usr/lib/apache2/modules/` # Thư mục chứa tất cả các module (link tượng trưng)  

├── `mod_access_compat.so`                     # Module tương thích kiểm soát truy cập cũ  
├── `mod_actions.so`                           # Module thực thi action theo loại MIME  
├── `mod_alias.so`                             # Module tạo bí danh URL  
├── `mod_allowmethods.so`                      # Giới hạn các phương thức HTTP được phép  
├──....  
├── `mod_userdir.so`                           # Thư mục người dùng  
├── `mod_usertrack.so`                         # Theo dõi người dùng  
├── `mod_vhost_alias.so`                       # Bí danh virtual host  
└── `mod_xml2enc.so`                           # Mã hóa XML  
  
#### 5.`/usr/sbin/` #Thư mục chứa các lệnh quản trị Apache  

├── `apache2`                                  # File chương trình Apache chính  
├── `apache2ctl`                               # Script điều khiển Apache (QUAN TRỌNG!)  
├── `a2enmod`                                  # Lệnh BẬT module (QUAN TRỌNG!)  
├── `a2dismod`                                 # Lệnh TẮT module  
├── `a2ensite`                                 # Lệnh BẬT virtual host (QUAN TRỌNG!)  
├── `a2dissite`                                # Lệnh TẮT virtual host  
├── `a2enconf`                                 # Lệnh BẬT config  
├── `a2disconf`                                # Lệnh TẮT config  
├── `a2query`                                  # Lệnh tra cứu thông tin cấu hình Apache  
├── `htcacheclean`                             # Công cụ dọn dẹp cache đĩa  
├── `rotatelogs`                               # Công cụ xoay vòng file log  
└── `suexec`                                   # File thực thi suexec  
  
#### 6.`/usr/bin/` # Thư mục công cụ tiện ích  

├── `ab`                                       # Apache Benchmark - công cụ test tải (CỰC HAY!)  
├── `htdbm`                                    # Quản lý mật khẩu DBM database  
├── `htdigest`                                 # Tạo file mật khẩu digest  
├── `htpasswd`                                 # Tạo/quản lý file htpasswd (CỰC HAY DÙNG!)  
├── `httxt2dbm`                                # Chuyển đổi text sang DBM  
└── `logresolve`                               # Phân giải IP thành hostname trong log  
  
#### 7.`/run/apache2/` # Thư mục runtime (tạm thời khi Apache chạy)  

├── `apache2.pid`                              # File chứa Process ID của Apache  
└── (các file socket)                          # Các Unix socket files nếu có  
  
#### 8.`/var/lib/apache2/` # Thư mục dữ liệu trạng thái  

└── (dữ liệu trạng thái runtime)               # Dữ liệu trạng thái tạm thời  
  
`/usr/share/apache2/`                          # Thư mục dữ liệu dùng chung  
├── `error/`                                   # Các template trang lỗi  
├── `icons/`                                   # Các icon mặc định  
│   ├── `small/`                               # Icons kích thước nhỏ  
│   └── (nhiều file .gif, .png)                # Các file icon  
├── `default-site/`                            # Tài nguyên site mặc định  
└── `build/`                                   # Các script build  
  
#### 9.`/etc/default/` # Thư mục cấu hình mặc định  

└── `apache2`                                  # Biến môi trường cho Apache  
  
#### 10.`/usr/lib/systemd/system/` # Thư mục systemd service files  

├── `apache2.service`                          # File service chính  
├── `apache2@.service`                         # Template instance  
└── `apache-htcacheclean.service`              # Service dọn cache tự động  
  
#### 11.`/var/cache/apache2/` # Thư mục cache  

└── `mod_cache_disk/`                          # Cache đĩa (nếu bật module)  
  
#### 12.`/etc/logrotate.d/` # Thư mục cấu hình xoay vòng log  

└── `apache2`                                  # Quy tắc xoay vòng log Apache tự động  
  
#### 14.`/usr/share/doc/apache2/` # Thư mục tài liệu  

└── `README.Debian.gz`                         # Hướng dẫn dành cho Debian/Ubuntu

### II. CÁC LỆNH QUAN TRỌNG TRÊN UBUNTU (QUAN TRỌNG)

```bash
# Quản lý service
sudo systemctl start apache2        # Khởi động
sudo systemctl stop apache2         # Dừng
sudo systemctl restart apache2      # Khởi động lại (dừng hẳn rồi start)
sudo systemctl reload apache2       # Reload config (không ngắt kết nối)
sudo systemctl status apache2       # Xem trạng thái
sudo systemctl enable apache2       # Tự động khởi động cùng hệ thống
sudo systemctl disable apache2      # Tắt tự động khởi động

# Quản lý modules
sudo a2enmod rewrite               # Bật module rewrite
sudo a2enmod ssl                   # Bật module SSL
sudo a2enmod headers               # Bật module headers
sudo a2enmod proxy                 # Bật module proxy
sudo a2enmod proxy_fcgi            # Bật proxy FastCGI (PHP-FPM)
sudo a2dismod mpm_prefork          # Tắt module prefork
sudo a2dismod status               # Tắt module status

# Quản lý sites (Virtual Hosts)
sudo a2ensite mysite.conf          # Bật virtual host
sudo a2dissite 000-default.conf    # Tắt virtual host mặc định

# Quản lý configs
sudo a2enconf security             # Bật config security
sudo a2disconf charset             # Tắt config charset

# Kiểm tra cấu hình
sudo apache2ctl configtest         # Test syntax config
sudo apache2ctl -t                 # Test syntax (ngắn gọn)
sudo apache2ctl -S                 # Xem virtual hosts
sudo apache2ctl -M                 # Xem modules đang load
sudo apache2ctl -V                 # Xem version và compile options

# Query thông tin
sudo a2query -m                    # List modules enabled
sudo a2query -s                    # List sites enabled
sudo a2query -c                    # List configs enabled
sudo a2query -a                    # List all info

# Log
sudo tail -f /var/log/apache2/access.log      # Theo dõi access log
sudo tail -f /var/log/apache2/error.log       # Theo dõi error log
sudo less /var/log/apache2/error.log          # Đọc error log
```

# DIRS TREE NGINX

## I. TRÊN CentOS 9 / RHEL / Rocky / AlmaLinux

Nginx được cài từ package nginx (repo EPEL hoặc AppStream).

```bash
Cấu trúc thư mục:
/etc/nginx/                         # Thư mục cấu hình chính của Nginx  
├── nginx.conf                      # File config chính (global)  
├── conf.d/                         # Nơi chứa các site (Virtual Host)  
│   ├── default.conf                # Site mặc định (HTTP)  
│   ├── example.conf                # (Tự tạo) site khác  
│  
├── modules/                        # Cấu hình load module (.so)  
│  
├── mime.types                      # Khai báo kiểu MIME cho file tĩnh  
└── fastcgi_params, scgi_params...  # Các file cấu hình CGI, Proxy  

Thư mục dữ liệu & log:  
/usr/share/nginx/html/              # Web root mặc định (index.html)  
├── index.html                      # Trang chào mặc định  
│  
/var/log/nginx/                     # Log lỗi và truy cập  
├── access.log  
└── error.log  
  
Service & PID:
/run/nginx.pid                      # File lưu PID của process  
/usr/lib/systemd/system/nginx.service  # File khởi động Nginx  
```

Tạo website mới:  

→ Chỉ cần tạo file trong /etc/nginx/conf.d/ như:

```bash
sudo nano /etc/nginx/conf.d/mywebsite.conf
```

-> rồi chỉnh root `/usr/share/nginx/html/mywebsite`;

## II. TRÊN Ubuntu / Debian

Nginx ở Ubuntu có cấu trúc “rõ ràng hơn” cho quản lý nhiều site.

```bash
Cấu trúc thư mục:
/etc/nginx/                         # Thư mục cấu hình chính  
├── nginx.conf                      # File config global  
├── sites-available/                # Chứa các site có thể bật (available)  
│   ├── default  
│   └── mywebsite.conf  
│  
├── sites-enabled/                  # Liên kết (symlink) tới site đang bật  
│   ├── default -> ../sites-available/default  
│   └── mywebsite.conf -> ../sites-available/mywebsite.conf  
│  
├── snippets/                       # Chứa các đoạn config tái sử dụng  
├── conf.d/                         # Cấu hình global phụ  
└── mime.types  
  
Thư mục dữ liệu & log:
/var/www/html/                      # Web root mặc định  
├── index.nginx-debian.html  
│  
/var/log/nginx/                     # Log truy cập và lỗi  
├── access.log  
└── error.log
```  

## III. SO SÁNH NGINX TRÊN CENTOS9 & UBUNTU

| Thành phần          | CentOS 9                        | Ubuntu                                     |
| ------------------- | ------------------------------- | ------------------------------------------ |
| File config chính   | `/etc/nginx/nginx.conf`         | `/etc/nginx/nginx.conf`                    |
| Thư mục site        | `/etc/nginx/conf.d/`            | `/etc/nginx/sites-available/` + `/etc/nginx/sites-enabled/` |
| Web root mặc định   | `/usr/share/nginx/html/`        | `/var/www/html/`                           |
| Log                 | `/var/log/nginx/`               | `/var/log/nginx/`                          |
| Lệnh reload         | `sudo systemctl reload nginx`   | `sudo systemctl reload nginx`              |
| Cấu hình nhiều site | Tạo file `.conf` trong `conf.d` | Dùng `a2ensite` kiểu riêng (manual symlink)|

## IV. TỔNG KẾT

**CentOS**: đơn giản, mọi VirtualHost nằm hết trong `/etc/nginx/conf.d/`.

**Ubuntu**: chia 2 tầng (available/enabled) để bật/tắt site dễ dàng.