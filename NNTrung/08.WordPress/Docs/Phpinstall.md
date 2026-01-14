# Cài đặt phiên bản php mong muốn trên Rocky hay CentOS 9(Options)
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

### 5.4 Tải wordPress chỉ cần thực hiện trên `web1`
```bash
cd /var/www/wordpress
sudo curl -O https://wordpress.org/latest.tar.gz
sudo tar -xzf latest.tar.gz --strip-components=1
sudo chown -R nginx:nginx(apache/apache) /var/www/wordpress
```
- `Web2` sẽ thấy nội dung vì đã mount NFS rồi.