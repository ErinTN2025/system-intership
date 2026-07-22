# Triển khai 
## 1. Cấu hình cơ bản
### 1.1 Cập nhập hệ thống
```bash
sudo apt update 
sudo apt upgrade -y 
```
- Kiểm tra phiên bản hệ điều hành
```bash
lsb_release -a
```
### 1.2 Thiết lập Timezone
```bash
# Chỉnh sửa
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
# Check
timedatectl
```
- Đồng bộ thời gian bằng chrony
```bash
sudo apt install chrony -y
sudo apt install status chrony
```
- Set server giờ nội bộ: `sudo nano /etc/chrony/chrony.conf`
```bash
# Lấy Load balancer làm gốc
sudo tee /etc/chrony/chrony.conf > /dev/null <<'EOF'
pool ntp.ubuntu.com iburst maxsources 4
# Cho phép các node trong subnet đồng bộ về node này
allow 10.0.40.0/24
# Nếu mất internet vẫn tự phát giờ
local stratum 10
driftfile /var/lib/chrony/chrony.drift
makestep 1.0 3
rtcsync
EOF
sudo systemctl restart chrony

# Các Server còn lại trỏ đến Load balancer
sudo tee /etc/chrony/chrony.conf > /dev/null <<'EOF'
server controller01 iburst prefer
pool ntp.ubuntu.com iburst maxsources 2
driftfile /var/lib/chrony/chrony.drift
makestep 1.0 3
rtcsync
EOF
sudo systemctl restart chrony
```
### 1.3 Thiết lập locale
```bash
sudo update-locale LANG=C.UTF-8
# Check 
locale
```
### 1.4 Hostname
```bash
sudo hostnamectl set-hostname LB
sudo hostnamectl set-hostname web1
sudo hostnamectl set-hostname web2
sudo hostnamectl set-hostname db
sudo hostnamectl set-hostname monitor
# Khai báo thêm trong hosts
sudo nano /etc/hosts 
```
### 1.5 Tắt Cloud-init
- Tắt cloud-init tránh tình trạng ghi đè
```bash
sudo nano /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
```
- Điền nội dung:
```bash
network: {config: disabled}
```
- Tắt cloud-init ghi đè host
```bash
sudo sed -i 's/^manage_etc_hosts:.*/manage_etc_hosts: false/' /etc/cloud/cloud.cfg
grep -q '^manage_etc_hosts:' /etc/cloud/cloud.cfg || \
  echo 'manage_etc_hosts: false' | sudo tee -a /etc/cloud/cloud.cfg
```
### 1.6 Cấu hình IP tĩnh
```bash
sudo nano 50-cloud-init.yaml
```
- Chỉnh sửa IP tĩnh: VD mẫu load balancer (những cái khác tương tự)
```yaml
network:
    ethernets:
        ens33:
            addresses:
              - 10.0.10.10/24
            routes:
              - to: default
                via: 10.0.10.1
            nameservers:
              addresses:
                - 8.8.8.8
        ens34:
            addresses:
              - 10.0.20.19/24
        ens35:
            addresses:
              - 10.0.40.36/24
    version: 2
```
NIC ens33 sẽ được cấu hình là card Interface ra Internet.

```bash
sudo netplan try
sudo netplan apply
```

### 1.7 Quản lý Iptables
- Đầu tiên đưa về trạng thái trắng
```bash
# Xem rules hiện tại 
sudo iptables -L -n -v
# Xóa các rules và chain hiện tại 
sudo iptables -F
sudo iptables -X
sudo iptables -t nat -F
sudo iptables -t nat -X
sudo iptables -t mangle -F
sudo iptables -t mangle -X
# Drop các 3 chiều traffic mặc định tới server
sudo iptables -P INPUT DROP
sudo iptables -P OUTPUT DROP
sudo iptables -P FORWARD DROP
# Chỉ cho phép giao tiếp nội bộ local 
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A OUTPUT -o lo -j ACCEPT
```
- Cho phép các kết nối đã được thiết lập, Rule này sẽ cho phép packet trả lời của các kết nối đã được mở hợp lệ.
```bash
sudo iptables -A INPUT  -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```
- Cho phép SSH (mở port 22)
```bash
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A OUTPUT -p tcp --sport 22 -j ACCEPT
```
- Cho phép DNS (`apt` cần phân giải tên miền)
```bash
# UDP
sudo iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
sudo iptables -A INPUT  -p udp --sport 53 -j ACCEPT
# TCP
sudo iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
sudo iptables -A INPUT  -p tcp --sport 53 -j ACCEPT
```
- Cho phép HTTP và HTTPS
```bash
# HTTP
sudo iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT  -p tcp --sport 80 -j ACCEPT
# HTTPS
sudo iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```
- Sau khi thêm cần kiểm tra kỹ
```bash
sudo iptables -L -n -v
```

Backend 1+2:
```bash
# Trên web1 — INPUT chain

# 1. Cho phép traffic MỚI đúng port 5000, chỉ từ LB
iptables -A INPUT -p tcp -s 10.0.20.19 --dport 5000 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# 2. Cho phép traffic TRẢ VỀ của các kết nối đã được thiết lập (không quan tâm port cụ thể)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# 3. Mặc định drop hết còn lại
iptables -P INPUT DROP
```

### 1.8 Cài đặt OpenSSH
```bash
sudo apt install openssh-server -y
sudo systemctl enable ssh
sudo systemctl start ssh
# Check
sudo systemctl status ssh
```

### 1.9 Disable Swap
```bash
# Check
sudo swap --show
# tắt
sudo swapoff -a 
```

### 1.10 Cài đặt docker engine  
- Nên cài đặt phiên bản cụ thể của Docker để dễ quản lý và đồng bộ
- Thêm thư viện của Docker vào kho lưu trữ apt
```bash
# Thêm khóa GPG chính thức của Docker:
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Thêm kho lưu trữ vào Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
```
```bash
sudo apt list --all-versions docker-ce
```

```bash
$ VERSION_STRING=5:29.6.0-1~ubuntu.22.04~jammy
$ sudo apt install docker-ce=$VERSION_STRING docker-ce-cli=$VERSION_STRING containerd.io docker-buildx-plugin docker-compose-plugin
```