# Cài đặt WordPress trên Ubuntu
## 1) Chuẩn bị & kiểm tra hệ thống
Cập nhật apt:
```bash
sudo apt update && sudo apt upgrade -y
```
Cài các công cụ cần thiết: 
```bash
sudo apt install wget unzip -y
```
## 2) Cài Apache (web server)
```bash
sudo apt install apache2 -y
sudo systemctl start apache2
sudo systemctl enable apache2
sudo systemctl status apache2
```

## 3) Cài MySQL (hoặc MariaDB)
```bash
sudo apt install mysql-server -y
sudo mysql_secure_installation
```
Đăng nhập vào tài khoản `root` của database:
```bash
mysql -u root -p
```

![altimage](../Images/rootmysql.png)

Terminal chuyển sang mysql
- Tạo Database cho WP. Ở đây đặt là `db_wp`
```mysql
CREATE DATABASE db_wp;
```
- Tạo tài khoản riêng để quản lí DB. Tên tài khoản: `admin`, Mật khẩu: `admin`
```mysql
CREATE USER admin@localhost IDENTIFIED BY 'admin';
```
- Cấp quyền quản lý cơ sở dữ liệu cho user mới tạo:
```mysql
GRANT ALL PRIVILEGES ON db_wp.* TO admin@localhost;
```
- Xác thực những thay đổi về quyền:
```mysql
FLUSH PRIVILEGES;
```
**lưu ý**: `GRANT` không còn cho phép tạo user + đặt mật khẩu trong cùng 1 câu lệnh nữa trên MySQL 8 trở lên (Ubuntu, XAMPP, Windows đều vậy).
- Thoát khỏi mysql
```mysql
exit
```
![altimage](../Images/Screenshot_1.png)

### 3.1 Sửa lỗi không thể `mysql -u root -p`
- MySQL root đang dùng auth_socket (Ubuntu mặc định)
```plaintext
sudo mysql
```
Đổi thành dùng password
```bash
ALTER USER 'root'@'localhost'
IDENTIFIED WITH mysql_native_password BY 'yourpassword';

FLUSH PRIVILEGES;
```
Thoát và Test là thành công.

Hoặc bạn cũng có thể tạo USER mới
```mysql
CREATE USER 'admin'@'localhost' IDENTIFIED BY '123456';
GRANT ALL PRIVILEGES ON *.* TO 'admin'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

## 4) Tải và cài đặt WordPress
- Cài gói hỗ trợ `php-gd`:
```bash
sudo apt install php-gd
```
- Tải xuống WordPress phiên bản mới nhất: Nếu chưa cài đặt `wget` thì có thể cài bằng câu lệnh `sudo apt install wget`
```bash
cd /tmp
wget https://wordpress.org/latest.tar.gz
```
- Sau khi tải xong. Ta tiến hành giải nén file `latest.tar.gz`
```bash
tar xzf latest.tar.gz
```
- Copy các file trong thư mục wordpress tới đường dẫn `/var/www/html`
```bash
sudo mv wordpress /var/www/html/wordpress
```

![altimgar](../Images/Wordpressinstall.png)

## 5) Cấu hình WordPress
File cấu hình wordpress:` /var/www/html/wp-config.php`
- Di chuyển tới thư mục `/var/www/html/wordpress`
- File cấu hình wordpress là `wp-config.php`. Tuy nhiên tại đây chỉ có file `wp-config-sample.php`. Tiến hành copy lại file cấu hình như sau:
```bash
cp wp-config-sample.php wp-config.php
```
- Chỉnh sửa file cấu hình `wp-config.php`. Chỉnh lại tên database, username, password đã đặt ở trên. (db_name: `db_wp`, username: `admin`, pass: `admin`) và lưu lại.

![alitmage](../Images/config.png)

## 6) Tạo Apache Virtual Host 
```bash
sudo nano /etc/apache2/sites-available/wordpress.conf
```
```bash
<VirtualHost *:80>
    ServerName wordpress.com
    ServerAlias www.wordpress.com
    DocumentRoot /var/www/html/wordpress

    <Directory /var/www/html/wordpress>
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/wordpress_error.log
    CustomLog ${APACHE_LOG_DIR}/wordpress_access.log combined
</VirtualHost>
```
- Kích hoạt site và module rewrite
```bash
sudo a2ensite wordpress.conf
sudo a2enmod rewrite
sudo systemctl reload apache2
```

## 7) Hoàn tất cài đặt giao diện

![altimage](../Images/wordpressgui.png)

- Nhập các thông tin cần thiết rồi click Install WordPress.

![alitmage](../Images/guiafterlogin.png)

## 8) Phân quyền WordPress
- Phân quyền thư mục `wordpress` cho` user apache` để `user` này được phép tạo các thư mục và lưu trữ các tệp tin tải lên.
```bash
sudo chown -R www-data:www-data /var/www/html/wordpress
# file 644, thư mục 755 (tùy chỉnh nếu cần)
sudo find /var/www/html/wordpress/ -type d -exec chmod 755 {} \;
sudo find /var/www/html/wordpress/ -type f -exec chmod 644 {} \;
```

**Lưu ý**:
`www-data` không phải user của bạn, cũng không phải root.

Nó là user mặc định của Apache/Nginx dùng để chạy web server.

Trên Ubuntu, khi cài Apache hoặc Nginx, hệ thống tự tạo user:

User: `www-data`

Group: `www-data`

Đây là user chuyên để chạy website, không dùng để đăng nhập. Khi Apache phục vụ trang web, nó chạy dưới tài khoản:

WordPress cần Apache ghi file (upload hình, cài plugin, cài theme)

Apache chạy dưới user www-data

Nếu WordPress thuộc sở hữu của trung, Apache không có quyền ghi, dẫn tới lỗi:
- ❌ “Unable to create directory”
- ❌ “Uploads folder is not writable”
- ❌ “Plugin installation failed – permission denied”

![altimage](../Images/uploaddone.png)

Như vậy là bạn đã có thể tiến hành upload ảnh và đăng bài viết lên trang wordpress của mình.