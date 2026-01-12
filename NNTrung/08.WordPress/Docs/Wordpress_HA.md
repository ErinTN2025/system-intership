# Tìm hiểu về Wordpress HA
## 1. WordPress HA là gì?
WordPress HA (High Availability) là kiến trúc triển khai WordPress đảm bảo khả năng sẵn sàng cao, nghĩa là website WordPress luôn hoạt động ổn định, giảm thiểu tối đa thời gian gián đoạn dịch vụ khi xảy ra lỗi phần cứng, lỗi mạng hoặc bảo trì thông qua các tính năng dự phòng, cân bằng tải và đồng bộ hóa dữ liệu.
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

## 4. NFS là gì
- **NFS(Network File System) - Hệ thống tệp qua mạng**: cho phép một máy tính(client) truy cập thư mục hoặc tệp nằm trên máy khác( Server) như thể chúng đang nằm trên ổ cứng cục bộ

### 4.1 Cách hoạt động của NFS
  - **Export(Chia sẻ)**: Trên Server, bạn chỉ định thư mục nào muốn chia sẻ( ví dụ: `/var/www/wordpress`) và cho phép những IP nào được truy cập thông qua `/etc/exports`.
  - **Mount( Kết nối)**: Trên Client, bạn thực hiện lệnh `mount`. Hệ điều hành Client sẽ tạo ra một điểm kết nối ảo trỏ đến địa chỉ IP của Server.
  - **Truy xuất**: Khi người dùng trên Client mở một tệp tin trong thư mục đã mount:
    - Yêu cầu được gửi qua mạng tới Server bằng giao thức RPC (Remote Procedure Call).
    - Server xử lý yêu cầu, đọc/ghi tệp tin trên ổ cứng thực của nó.
    - Server gửi kết quả trả lại cho Client
    - Người dùng thấy kết quả ngay lập tức như đang dùng máy cục bộ

### 4.2 Mục đích của NFS
- **Tập trung dữ liệu**: Bạn chỉ cẩn lưu trữ tệp tin tại một nơi duy nhất(Server). Điều này giúp quản lý và sao lưu(backup) dễ dàng hơn.
- **Chia sẻ tài nguyên**: Nhiều máy Client có thể cùng đọc và ghi vào một thư mục cùng lúc.
- **Tiết kiệm dung lượng**: Các máy Client không cần ổ cứng lớn vì dữ liệu thực tế nằm trên Server.
- **Đồng bộ hóa(Dành cho Wordpress)**: Trong mô hình Load Balancing(Nhiều web server chạy cùng một lúc), NFS đảm bảo rằng khi bạn tải một tấm ảnh lên ở Server 1, thì Server 2 cũng thấy tấm ảnh đó ngay lập tức vì cả 2 đều cùng dùng chung 1 thư mục `/var/www/wordpress` trên NFS Server.

# Lab về NFS
## 1. Môi trường
| **Máy ảo** | **OS** | **Vai trò** |
|------------|--------|-------------|
|Web-server1 | CentOS Stream 9 | Web + NFS Server |
|Web-server2 | Ubuntu 24.04 | Web + NFS Client |
|lb-server | Ubuntu 24.04 | Load Balancer |

**Phần mềm sử dụng**
| **Vai trò** | **Phần mềm** |
|-------------|--------------|
| Web Server | Nginx + PHP + WordPress |
| Load Balancer | Nginx(Reverse Proxy + Load Balancer) |
| Database | MariaDB hoặc MySQL( đặt trên web1) |
| Shared Storage | NFS( chia sẻ thư mục WordPress từ web1 cho web2 ) |

## 2. Cấu hình NFS Server trên web1 (CentOS 9)
### 2.1 Cài đặt NFS server:
```bash
sudo dnf install nfs-utils -y
```
### 2.2 Tạo thư mục wordpress và phân quyền
```bash
sudo mkdir -p /var/www/wordpress
sudo chown -R nodbody:nobody /var/www/wordpress
sudo chmod -R 755 /var/www/wordpress
```
### 2.3 Cấu hình 
```bash
echo "/var/www/wordpress 192.168.70.0/24(rw,sync,no_root_squash)" | sudo tee -a /etc/exports
```
### 2.4 Khởi động dịch vụ NFS
```bash
sudo systemctl enable --now nfs-server
```
## 3. Cấu hình NFS Client trên web2 (Ubuntu)
### 3.1 Cài đặt NFS client
```bash
sudo apt update
sudo apt install nfs-common -y
```
### 3.2 Mở cổng tường lửa trên web1 (nếu firewall đang chạy)
```bash
sudo firewall-cmd --permanent --add-service=nfs
sudo firewall-cmd --permanent --add-service=mountd
sudo firewall-cmd --permanent --add-service=rpc-bind
sudo firewall-cmd --reload
```
### 3.3 Mount thư mục từ `web1`
```bash
sudo mkdir -p /var/www/wordpress
sudo mount 192.168.70.114: /var/www/wordpress /var/www/wordpress
```

Để mount tự động khi khởi động
```bash
echo "192.168.70.114:/var/www/wordpress /var/www/wordpress nfs defaults 0 0" | sudo tee -a /etc/fstab
```
## 4. Cài đặt MariaDB trên web1 (DB dùng chung)
### 4.1 Cài MariaDB:
```bash
sudo dnf install mariadb-server -y
sudo systemctl enable --now mariadb
```
### 4.2 Tạo database Wordpress
```bash
sudo mysql -u root -p 
```
- Lưu ý cấp quyền cho các IP khác cũng truy cập được không chỉ mỗi localhost
```mysql
CREATE DATABASE wordpress;
CREATE USER 'wpuser'@'%' IDENTIFIED BY 'wppassword';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wpuser'@'%';
FLUSH PRIVILEGES;
Exit
```
### 4.3 Mở cổng 3306 nếu cầu:
```bash
sudo firewall-cmd --add-port=3306/tcp --permanent
sudo firewall-cmd --reload
```

### 4.4 Check Bind Database
```bash
sudo ss -lntp | grep 3306
```
- Nếu thấy : `127.0.0.1:3306` -> chỉ local 
- Phải mở Bind
```bash
sudo nano /etc/my.cnf.d/mariadb-server.cnf
[mysqld]
bind-address = 0.0.0.0
sudo systemctl restart mariadb
```

### 4.5 SELinux của Rocky Linux chặn Apache/PHP kết nối DB từ xa
WordPress dùng PHP → chạy dưới context `httpd_t`

SELinux mặc định CẤM `httpd `connect DB qua network

- Kiểm tra: `getenforce` nếu ra `Enforcing` Thì phải sửa:
- Cho phép connect MySQL từ xa vĩnh viễn:
```bash
sudo setsebool -P httpd_can_network_connect_db 1
sudo systemctl restart httpd
sudo systemctl restart php-fpm
sudo setenforce 0
```

## 5. Cài đặt PHP + Nginx + WordPress trên web1 và web2
### 5.1 Trên web-server1 (CentOS):
```bash
sudo dnf install nginx php php-fpm php-mysqlnd -y
```
### 5.2 Trên web-server2 (ubuntu):
```bash
sudo apt install nginx php-fpm php-mysql -y
```
### 5.3 Sửa phiên bản php nếu không trùng giữa Rocky và Ubuntu (Options)
- **Dừng dịch vụ**: `sudo systemctl stop php-fpm`
- **Gỡ toàn bộ PHP & Extension**: 
```bash
sudo dnf remove -y 'php*'
rpm -qa | grep php
```
- **Reset module PHP**: `sudo dnf module reset php -y`
- **Cài Remi repo (chuẩn RHEL/Rocky)**
```bash
sudo dnf install -y epel-release
sudo dnf install -y https://rpms.remirepo.net/enterprise/remi-release-9.rpm
```
- **Chọn PHP version**: 
```bash
dnf module list php
sudo dnf module enable php:remi-8.4 -y
```
- **Cài PHP + extensions cần thiết cho WordPress**
```bash
sudo dnf install -y \
php php-fpm php-mysqlnd php-gd php-xml \
php-mbstring php-curl php-zip php-opcache
```
- **Bật FPM**: `sudo systemctl enable --now php-fpm`
- **Check lại phiên bản**
```bash
php -v
php-fpm -v
rpm -q php-fpm
```
- **Check trên Ubuntu**
```bash
ls /usr/sbin | grep php-fpm
php -v
```
### 5.4 Tải wordPress chỉ cần thực hiện trên `web1`
```bash
cd /var/www/wordpress
sudo curl -O https://wordpress.org/latest.tar.gz
sudo tar -xzf latest.tar.gz --strip-components=1
sudo chown -R nginx:nginx(apache/apache) /var/www/wordpress
```
- `Web2` sẽ thấy nội dung vì đã mount NFS rồi.
### 5.5 Cấu hình Nginx trên cả web 1 và 2
File `/etc/nginx/conf.d/wordpress.conf`:
```bash
# web1 (CentOS)
server {
    listen 80;
    server_name 192.168.70.114;

    root /var/www/wordpress;
    index index.php index.html;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_pass unix:/run/php-fpm/www.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }
}

# web2 (Ubuntu)
server {
    listen 80;
    server_name 192.168.70.126;

    root /var/www/wordpress;
    index index.php index.html;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_pass unix:/run/php/php8.4-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }
}
```
  - Tùy OS mà socket PHP khác nhau, kiểm tra bằng:
  ```bash
  sudo find /run -name "*.sock"
  ```
## 6. Cài đặt Load Balancer trên Ib-server (Ubuntu)
### 6.1 Cài đặt Nginx
```bash
sudo apt install nginx -y
```
### 6.2 Cấu hình `/etc/nginx/sites-available/wordpress-lb`:
```bash
upstream wordpress_backend {
    server 192.168.70.114;
    server 192.168.70.126;
}

server {
    listen 80 default_server;
    server_name _;

    location / {
        proxy_pass http://wordpress_backend;
        proxy_http_version 1.1;

        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_redirect off;
    }
}
```
Kích hoạt soft-link
```bash
sudo ln -s /etc/nginx/sites-available/wordpress-lb /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 6.3 NGINX trên LOAD BALANCER trả 404 TRƯỚC KHI proxy vào backend.
- Backend 192.168.70.114 HOẠT ĐỘNG TỐT
```bash
curl -I http://192.168.70.114/wp-login.php
→ 200 OK
```
- Load Balancer `192.168.70.124` trả `404` từ chính **NGINX LB**
```bash
Server: nginx/1.24.0 (Ubuntu)
→ 404 Not Found
```
- REQUEST CHƯA HỀ ĐI TỚI BACKEND, NGINX LB đang dùng default site / wrong server block
```bash
#BACKEND
Server: nginx/1.20.1
X-Powered-By: PHP
#LB
Server: nginx/1.24.0 (Ubuntu)
Content-Length: 162
```
- Disable Site mặc định của Ubuntu: `sudo rm -f /etc/nginx/sites-enabled/default`
## 7. Kiểm tra hệ thống
- **Mở trình duyệt truy cập**:
```bash
http://192.168.70.124
```