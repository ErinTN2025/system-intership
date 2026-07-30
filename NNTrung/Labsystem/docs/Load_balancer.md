# Load balancer
## 1. Quản lý User
```bash
nobody               UID=65534 HUMAN    /usr/sbin/nologin
lb                   UID=1000  HUMAN    /bin/bash
```
- Lấy lb làm user do người phụ trách làm lb quyết định, vậy nên ta cấp đúng quyền sudo cho riêng user lb: sửa trong: `sudo nano /etc/sudoers`, file sudoers đảm bảo chỉ có quyền read ngay cả cho người sở hữu
- Check bằng:
```bash
getent group sudo
```

## 2. Cài đặt auditd 
```bash
sudo apt install -y auditd audispd-plugins

sudo systemctl enable --now auditd
sudo systemctl status auditd

```
- Xác định quyền truy cập cho thư mục ssh và audit: root có toàn quyền, group root và người khác chỉ có quyền xem.
```bash
sudo ls -lh /etc | grep -E "audit|ssh"
```
```bash
drwxr-xr-x  4 root root   4.0K Jul 22 08:58 ssh
drwxr-x--- 4 root root   4.0K Jul 24 06:55 audit
```
- Check kỹ càng đảm bảo chỉ người sở hữu có quyền write cho các thư mục bên trong, các nhóm khác chỉ read + execute hoặc chỉ read.

## 3. Dockercompose
- tạo 1 file `dockercompose.yml`
```bash
sudo mkdir monitor && cd monitor
sudo nano docker-compose.yml
```
```yaml
# docker-compose.yml
services:
  haproxy:
    image: haproxy:2.9-alpine
    container_name: haproxy
    restart: unless-stopped
    ports:
      - "443:443"
    volumes:
      - ./haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
      - /opt/ca/certs:/usr/local/etc/haproxy/certs:ro
    networks:
      - front
      - back
  node_exporter:
    image: prom/node-exporter:latest
    container_name: node_exporter
    restart: unless-stopped
    pid: host
    network_mode: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/host/root:ro,rslave
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/host/root'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
  blackbox_exporter:
    image: prom/blackbox-exporter:latest
    container_name: blackbox_exporter
    restart: unless-stopped
    ports:
      - "10.0.40.36:9115:9115"
    volumes:
      - ./blackbox/blackbox.yml:/etc/blackbox_exporter/config.yml:ro
    command:
      - '--config.file=/etc/blackbox_exporter/config.yml'
    networks:
      - back
    cap_add:
      - NET_RAW
  promtail:
    image: grafana/promtail:2.9.0
    container_name: promtail
    restart: unless-stopped
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./promtail/promtail-config.yml:/etc/promtail/config.yml:ro
    command:
      - '-config.file=/etc/promtail/config.yml'
    networks:
      - back

networks:
  front:
    driver: bridge
  back:
    driver: bridge
```
## 4. Blackbox_exporter config
```bash
mkdir -p blackbox && cd blackbox
```
```yaml
# blackbox/blackbox.yml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: [200, 301, 302]
      method: GET
      preferred_ip_protocol: "ip4"
  tcp_connect:
    prober: tcp
    timeout: 5s

  icmp_ping:
    prober: icmp
    timeout: 5s
```
## 5. HAproxy config
```bash
mkdir -p haproxy && cd haproxy
```
```bash
# haproxy/haproxy.cfg
global
    log stdout format raw local0
    maxconn 4096

defaults
    log global
    mode http
    option httplog
    timeout connect 5s
    timeout client 50s
    timeout server 50s

frontend fe_https
    bind *:443 ssl crt /usr/local/etc/haproxy/certs/lb.pem
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https
    default_backend be_web

backend be_web
    mode http
    balance roundrobin
    server web1 10.0.20.20:5000 check
    server web2 10.0.20.21:5000 check
```
## 6. Promtail Config
```bash
mkdir -p promtail
```
```yaml
# promtail/promtail-config.yml (LB)
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://10.0.40.40:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
      - target_label: 'host'
        replacement: 'lb'
```
## 7. LB làm CA nội bộ + TLS cho HA Proxy
### 7.1 Tạo Root CA trên LB
```bash
sudo mkdir -p /opt/ca/{private,certs}
cd /opt/ca

sudo openssl genrsa -out private/ca.key 4096
sudo chmod 400 private/ca.key

sudo openssl req -x509 -new -nodes -key private/ca.key -sha256 -days 365 \
    -out certs/ca.crt \
    -subj "/C=VN/ST=HN/O=Flasky-Lab/CN=Flasky-Lab-Root-CA"
```
### 7.2 Tạo cert cho chính LB
```bash
cd /opt/ca

sudo openssl genrsa -out private/lb.key 2048
sudo openssl req -new -key private/lb.key -out certs/lb.csr \
  -subj "/C=VN/ST=HN/O=Flasky-Lab/CN=flasky.lab.local"

sudo tee certs/lb.ext > /dev/null <<'EOF'
subjectAltName = DNS:flasky.lab.local, IP:10.0.10.10 
EOF

sudo openssl x509 -req -in certs/lb.csr -CA certs/ca.crt -CAkey private/ca.key \
  -CAcreateserial -out certs/lb.crt -days 825 -sha256 -extfile certs/lb.ext

sudo cat certs/lb.crt private/lb.key | sudo tee certs/lb.pem > /dev/null
sudo chmod 644 /opt/ca/certs/lb.pem
```

## Phương án 2(Tham khảo): Tạo Router giữa các mạng 
- Ta sẽ cài blackbox_exporter chỉ trên mỗi Monitor.
- Điều này đòi hỏi các dải mạng 10.0.10.0/24, 10.0.20.0/24, 10.0.30.0/24, 10.0.40.0/24 phải nhìn thấy nhau. 
- Ta phải tạo thêm 1 VM làm Router trung gian.
- Router VM này sẽ là gateway router cho các dải mạng:
```bash
NIC1: 10.0.10.1/24
NIC2: 10.0.20.1/24
NIC3: 10.0.30.1/24
NIC4: 10.0.40.1/24
```
- Lấy ví dụ blackbox_exporter của monitor muỗn xem cổng `10.0.10.10:443` ở trên Lb trước.
- Ta sẽ buộc phải cấu hình cẩn thận chỉ những gói tin nào được chấp thuận mới được qua.
```bash
# Trên Router VM — bật forwarding CHỈ ở đây
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Baseline: đưa về trắng, drop hết
sudo iptables -F; sudo iptables -X
sudo iptables -t nat -F; sudo iptables -t nat -X
sudo iptables -P INPUT DROP
sudo iptables -P OUTPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A OUTPUT -o lo -j ACCEPT
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# --- ACL cho FORWARD: CHỈ đúng 1 luồng cần thiết ---
# Monitor -> LB:443 (blackbox probe HTTPS public IP)
sudo iptables -A FORWARD -s 10.0.40.40 -d 10.0.10.10 -p tcp --dport 443 \
  -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# Chiều ngược lại (SYN-ACK, data trả lời) của đúng luồng trên
sudo iptables -A FORWARD -s 10.0.10.10 -d 10.0.40.40 -p tcp --sport 443 \
  -m conntrack --ctstate ESTABLISHED -j ACCEPT

# Router KHÔNG NAT — chỉ route thuần túy (cả 2 phía đã biết IP thật của nhau)
```
- Trên Monitor cấu hình route tĩnh để biết đường tới LB public IP:
```bash
# Monitor cần biết: muốn tới 10.0.10.0/24 thì đi qua Router (10.0.40.1)
sudo ip route add 10.0.10.0/24 via 10.0.40.1 dev <interface_monitor>

# Ghi vĩnh viễn (Ubuntu/Debian dùng netplan, ví dụ):
# routes:
#   - to: 10.0.10.0/24
#     via: 10.0.40.1
```
- Tạo 1 bảng Policy based routing trên LB
```bash
# Tạo 1 routing table riêng tên "fromnic1" (số 100)
echo "100 fromnic1" | sudo tee -a /etc/iproute2/rt_tables

# Trong bảng này: mọi traffic đi ra đều qua gateway Router (10.0.10.1)
sudo ip route add default via 10.0.10.1 dev <nic1_interface> table fromnic1

# Rule: TRAFFIC NÀO CÓ SOURCE IP = 10.0.10.10 (tức là traffic trả lời
# cho ai đó đã gửi request TỚI 10.0.10.10) thì dùng bảng "fromnic1"
sudo ip rule add from 10.0.10.10 table fromnic1

# Kiểm tra lại
ip rule list
ip route list table fromnic1
```
- Lý do cần bảng này là bởi:
  - Khi máy Monitor gửi gói tin SYN tới LB
  - Máy LB đáp lại lúc này gói tin của LB có 2 hướng đi 1 là qua NIC 3 của LB do lựa chọn tự động chọn đường đi ngắn nhất: `10.0.40.36` (dù nó có qua hay k thì gói tin vẫn bị drop)
  - Nên là cần bảng để đưa gói tin về hướng đi ban đầu `10.0.10.10 -> 10.0.10.1 -> 10.0.40.1 -> 10.0.40.40`.