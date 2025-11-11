# DHCP Lab
### 1. Cài gói DHCP server
```plaintext
sudo apt update
sudo apt install isc-dhcp-server -y
```
`isc-dhcp-server`: gói phần mềm máy chủ DHCP của ISC.

- **Kiểm tra interface mạng**: 
```ruby
ip a
```
![altimage](../Images/ipens33.png)

Hoặc kiểm tra với câu lệnh:
```ruby
apt list --installed isc-dhcp-server
```
hoặc
```ruby
dpkg -l | grep isc-dhcp-server
```

- **Xác định interface cấp IP**
```plaintext
sudo nano /etc/default/isc-dhcp-server
```
Sửa card mạng Interfaces IPv4: `INTERFACESv4="ens33"`

`Ctrl O` + `Enter` + `Ctrl X`

### 2. Đặt IP tĩnh cho DHCP Server
Truy cập:
```plaintext
sudo nano /etc/netplan/50-cloud-init.yaml
```
![altimage](../Images/staticipconfig.png)

Áp dụng
```ruby
sudo netplan apply
```

### 3. Cấu hình DHCP Server
Sửa file cấu hình DHCP
```ruby
sudo vim /etc/dhcp/dhcpd.conf
```
Thêm cấu hình:
```plaintext
option domain-name "nhom2.local";

default-lease-time 600;
max-lease-time 7200;
authoritative;

subnet 192.168.172.0 netmask 255.255.255.0 {
  range 192.168.172.10 192.168.172.50;
  option routers 192.168.172.1;
  option subnet-mask 255.255.255.0;
  option domain-name-servers 8.8.8.8, 1.1.1.1;
}
```

![altimage](../Images/dhcp.png)

- `default-lease-time 600`: Thiết lập thời gian thuê mặc định (default lease time) cho các địa chỉ IP được cấp phát bởi DHCP server là 600 giây (10 phút).
- `max-lease-time 7200`: Thiết lập thời gian thuê tối đa mà DHCP server sẽ cấp phát cho một client là 7200 giây (2 giờ). Khi client yêu cầu thời gian thuê dài hơn, server sẽ không cấp phát quá thời gian này.
- `authoritative`: Khai báo rằng DHCP server này là có thẩm quyền (authoritative) cho các subnet được cấu hình trong file này. Server sẽ phản hồi các yêu cầu DHCP ngay cả khi nó không chắc chắn về cấu hình mạng.
- `subnet 192.168.172.0 netmask 255.255.255.0 { ... }`:
  - `subnet 192.168.172.0`: Xác định địa chỉ mạng của subnet là `192.168.172.0`.
  - `netmask 255.255.255.0`: Xác định subnet mask cho subnet này là `255.255.255.0`.
  - `range 192.168.186.100 192.168.172.150`: Dải địa chỉ DCP có thể cấp phát.
  - `option routers 192.168.172.1`: `192.168.172.1` là địa chỉ IP của router (cổng mặc định - default gateway) mà các client sẽ sử dụng để truy cập các mạng khác bên ngoài subnet này.
  - `option domain-name-servers 8.8.8.8, 1.1.1.1`: Thiết lập tùy chọn `domain-name-servers` cho các client trong subnet. Các client sẽ sử dụng các địa chỉ IP `8.8.8.8` (máy chủ DNS của Google) và `1.1.1.1` (máy chủ DNS của Cloudflare) này để phân giải tên miền thành địa chỉ IP.

Khởi động DHCP Server
```plaintext
sudo systemctl restart isc-dhcp-server
sudo systemctl status isc-dhcp-server
```

![altimage](../Images/statusdhcpiscserver.png)

Sau khởi động lại `sudo systemctl start isc-dhcp-server`

### 4. Cấu hình mạng trên CentOS dùng DHCP
Sửa file
```plaintext
sudo vim /etc/NetworkManager/system-connections/ens33.nmconnection
```

![alitmgae](../Images/dhcpsetting.png)

Khởi động lạ NetworkManager để áp dụng:
```plaintext
sudo systemctl restart NetworkManager
```

Kiểm tra ip

### 5. Kiểm tra cấp phát trên DHCP server (DHCP Logs)
Sử dụng lệnh:
```plaintext
cat /var/lib/dhcp/dhcpd.leases
```

![alitmgae](../Images/dhcpcheck.png)

- IP: `192.168.172.11` đã được cấp.
- `starts`: Thời điểm bắt đầu lease – nghĩa là thời điểm client nhận được IP.
- `ends`: Thời điểm kết thúc lease – sau đó client cần gia hạn (renew) hoặc lấy IP mới.
- `cltt` (Client Last Transaction Time): Thời điểm cuối cùng client thực hiện giao dịch với DHCP server (giống starts nếu là lần đầu).
- `binding state active`:  Trạng thái binding hiện tại là active → IP này đang được sử dụng.
- `next binding state free`: Khi lease hết hạn, trạng thái tiếp theo sẽ là free → IP này sẽ sẵn sàng để cấp phát lại.
- `rewind binding state free`: Khi thực hiện "rewind" (quay lui cấu hình trước khi server restart), IP này cũng sẽ trở lại trạng thái free.
- `00:0c:29:d1:31:37`: Địa chỉ MAC address của client được cấp phát IP.
- `uid "\001\000\014)\32117"`: UID của client (Unique Identifier), thường được DHCP client tạo ra để phân biệt trong các môi trường không có MAC cố định (VD: DHCP relay, VPN...).

#### Xem log DHCP server
```plaintext
sudo journalctl -u isc-dhcp-server
```

![altimage](../Images/dhcplogs.png)

#### Xem log DHCP Clients
- Trên Ubuntu
```plaintext
sudo journalctl -u systemd-networkd | grep DHCP
```

![altimage](../Images/filelogclient.png)

- Trên CentOS 9
```plaintext
sudo journalctl -u NetworkManager | grep -i dhcp
sudo journalctl -fu NetworkManager | grep -i dhcp (realtime)
```
![altimage](../Images/logcentos.png)

Nếu là Server:
```plaintext
sudo journalctl -u named
sudo journalctl -fu named
```

