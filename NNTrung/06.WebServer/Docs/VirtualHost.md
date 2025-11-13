# II. Cấu hình Virtual Host trong Apache (Cấu hình nhiều website trên 1 web server)
### 1. Trên Ubuntu
#### 1. Tạo thư mục cấu trúc
- Cấu trúc thư mục sẽ lưu trữ dữ liệu của người dùng khi truy cập vào website. Bạn cần tạo thư mục gốc(`/var/www/directory`) cho mỗi tên miền, ví dụ: `mywebsite1.com` và `mywebsite2.com`:
```plaintext
sudo mkdir -p /var/www/mywebsite1.com
sudo mkdir -p /var/www/mywebsite1.com
```
#### 2. Cấp quyền truy cập
```plaintext
sudo chown -R $Aaaaaaa:$Aaaaaaa /var/www/mywebsite1.com
sudo chown -R $Aaaaaaa:$Aaaaaaa /var/www/mywebsite2.com
sudo chmod -R 755 /var/www
```
#### 3. Tạo file `index.html`
```plaintext
sudo touch /var/www/mywebsite1/index.html
sudo touch /var/www/mywebsite2/index.html
```
#### 4. Tạo file cấu hình cho VirtualHosts
Apache mặc định có site `/etc/apache2/sites-available/000-default.conf`. Ta tạo site riêng để quản lý dễ hơn:

```plaintext
sudo nano /etc/apache2/sites-available/mywebsite1.conf
sudo nano /etc/apache2/sites-available/mywebsite2.conf
```
- Thêm nội dung ở `mywebsite1.com`
```html
<VirtualHost *:80>
    ServerAdmin admin@mywebsite1.com
    ServerName mywebsite1.com
    ServerAlias www.mywebsite1.com
    DocumentRoot /var/www/mywebsite1.com

    <Directory /var/www/mywebsite1.com>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/mywebsite1_error.log
    CustomLog ${APACHE_LOG_DIR}/mywebsite1_access.log combined
</VirtualHost>
```
- Thêm nội dung ở `mywebsite2.com`
```html
<VirtualHost *:801>
    ServerAdmin admin@mywebsite2.com
    ServerName mywebsite2.com
    ServerAlias www.mywebsite2.com
    DocumentRoot /var/www/mywebsite2.com

    <Directory /var/www/mywebsite2.com>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/mywebsite2_error.log
    CustomLog ${APACHE_LOG_DIR}/mywebsite2_access.log combined
</VirtualHost>
```
#### 5. Kích hoạt VirtualHost
- Chạy lệnh cấu hình
```plaintext
sudo a2ensite mywebsite1.conf
sudo a2ensite mywebsite2.conf
```
- `a2ensite`: viết tắt của "Apache 2 enable site".
tạo các liên kết tượng trưng (symbolic links) từ các tệp cấu hình Virtual Host trong thư mục `/etc/apache2/sites-available/` đến thư mục `/etc/apache2/sites-enabled/`.
- Apache chỉ đọc các tệp cấu hình trong thư mục `sites-enabled/`, do đó, việc tạo liên kết tượng trưng này kích hoạt cấu hình Virtual Host.
- Tắt site mặc định( Nếu cần):
```plaintext
sudo a2dissite 000-default.conf
```
- Kiểm tra lỗi cú pháp:
```plaintext
sudo apachectl configtest
```
- Khởi động lại Apache:
```plaintext
sudo systemctl restart apache2
```
#### 6. Cấu hình file hosts(Trên máy cục bộ vì truy cập website tại đó hoặc trên con VM)
**Trên máy cục bộ (Windows)**:

Mở file `C:\Windows\System32\drivers\etc\hosts` trên Notepad với quyền Admin.

Thêm vào cuối file
```bash
192.168.60.133 mywebsite1.com
192.168.60.133 mywebsite2.com
```
### 2. Trên CentOS 9
