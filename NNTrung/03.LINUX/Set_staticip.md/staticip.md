## Trên Ubuntu 24.04

Mở file cấu hình `netplan` (thường nằm trong `/etc/netplan/`):

```plaintext
sudo vim /etc/netplan/50-cloud-init.yaml
```

Kết quả:

![network card configuration file](../images/netplanubuntu.png)

Ấn `i` để chỉnh sửa nội dung, chỉnh sửa nội dung trong [ipv4] thành:

![reconfig card](../images/netplanconfig.png)

- `ens33`: Tên card mạng.
- `dhcl3: no`: tắt DHCP để dùng IP tĩnh.
- `addresses: - 192.168.154.128/24` địa chỉ IP và subnet mask.
- `gateway4: 192.168.154.2` gateway: bởi địa chỉ 192.168.154.1 là địa chỉ IP của máy tính thật đóng vai trò là NAT.

Chỉnh sửa xong, ấn `Esc` để thoát khỏi chế độ `Insert`. Tiếp đó nhập `:wq` và `Enter` để lưu cấu hình.

### Routes
- `to:default`: Khi máy tính muốn gửi gói tin đến một địa chỉ IP nào đó mà không nằm trong mạng nội bộ của nó, nó sẽ không biết đường đi. Lúc này hệ thống sẽ tra bảng routing table, nếu ko tìm thấy route cụ thể nào khớp, nó sẽ dùng route mặc định - gửi tất cả ra gateway đó.
  - Nó sẽ kiểu là nếu không biết đi đâu thì đi hướng này.
  - `to: default` → áp dụng cho mọi đích đến không rõ (tức "mọi nơi khác")


Nếu không dùng `to:default` - ta có thể route đến 1 mạng hay 1 subnet cụ thể:
```bash
routes:
  - to: 10.10.0.0/16 # chỉ gói tin đi đến mạng này
    via: 192.168.1.254 # mới đi qua gateway này
```

#### 1. Nhiều default route + metric (ưu tiên gateway chính, dự phòng gateway phụ)
```bash
network:
  version: 2
  ethernets:
    eth0:
      addresses: [192.168.1.10/24]
      routes:
        - to: default
          via: 192.168.1.1
          metric: 100     # ưu tiên cao (số nhỏ hơn = ưu tiên hơn)
    eth1:
      addresses: [192.168.2.10/24]
      routes:
        - to: default
          via: 192.168.2.1
          metric: 200     # dự phòng, chỉ dùng khi route kia chết
```
- Hệ thống sẽ ưu tiên dùng gateway có metric thấp hơn. Nếu interface đó down, tự động chuyển sang gateway còn lại.

#### 2. Định tuyến theo chính sách (Policy-based routing) — mỗi interface đi ra đúng gateway của nó
```bash
network:
  version: 2
  ethernets:
    eth0:
      addresses: [192.168.1.10/24]
      routes:
        - to: default
          via: 192.168.1.1
          table: 100
        - to: 192.168.1.0/24
          via: 0.0.0.0
          table: 100
      routing-policy:
        - from: 192.168.1.10
          table: 100

    eth1:
      addresses: [192.168.2.10/24]
      routes:
        - to: default
          via: 192.168.2.1
          table: 200
        - to: 192.168.2.0/24
          via: 0.0.0.0
          table: 200
      routing-policy:
        - from: 192.168.2.10
          table: 200
```
- `table:100/200`: tạo bảng định tuyến riêng cho từng interface
- `routing-policy: from: ...` nói nếu gói tin có địa chỉ nguồn là IP này, thì tra bảng route số đó.

Sau khi thực hiện thay đổi, cần restart để áp dụng thay đổi:

```plaintext
sudo netplan apply
```

### Phân biệt 
- `addresses`: địa chỉ của chính interface đó:
```yaml
addresses:
  - 192.168.2.10/24
```
- Ở đây `/24` không phải để nói "route tới đâu", mà để nói: "interface này thuộc về mạng nào".
  - `/24` cho hệ thống biết, địa chỉ của tôi là `192.168.2.10`
  - Nhưng cả dải `192.168.2.0-192.168.2.255` là cùng mạng LAN với tôi.
  - Nghĩa là: nếu muốn nói chuyện với bất kỳ máy nào trong dải đó (`192.168.2.1`, `192.168.2.50`,...), tôi gửi thẳng trực tiếp (Layer 2, không cần qua gateway)

- `routes: to:`: đường đi đến mạng khác

- Vậy tại sao không phải /32 cho addresses?:

Vì `/32` nghĩa là "chỉ có đúng 1 địa chỉ, không có mạng nào xung quanh cả" — nếu đặt IP của interface là /32, máy sẽ nghĩ là không có máy nào khác cùng mạng LAN với mình hết, kể cả gateway! Lúc đó nó sẽ không biết cách gửi ARP hay gói tin đến gateway (vì gateway coi như "ở xa", phải qua route khác — mà route đó cũng cần gateway... → vòng lặp vô lý).

Đó là lý do address luôn cần prefix đúng theo subnet mask thật của mạng (`/24`, `/23`, v.v.) — để hệ thống biết ranh giới "gần" (LAN) và "xa" (phải qua gateway) nằm ở đâu.

- Nếu dùng `route to: .../32` nghĩa là nếu muốn đến địa chỉ ip này thì qua gateway này là cấu hình riêng.
## Trên CentOS 9
`Cách 1`:
Mở cấu hình mạng (ens160)

`sudo vim /etc/NetworkManager/system-connections/ens160.nmconnection`

Kết quả

![altimage](../images/staticipcentos.png)

Ấn i để chỉnh sửa nội dung như trên
- `method=manual`: Chỉ định địa chỉ IP tĩnh.
- `address1= 192.168.154.129/24` : địa chỉ IP.

Sau khi chỉnh sửa xong, ấn `esc` để thoát khỏi chế độ `Insert`. Tiếp đó nhập `:wq` và `Enter` để lưu cấu hình.

Sau khi thực hiện thay đổi, cần restart để áp dụng thay đổi:

`sudo systemctl restart NetworkManager`

`Cách 2`: Dùng nmcli (NetworkManager CLI)

Vì trong CentOS 9, User không có quyền dùng sudo nên phải về trạng thái root:
- `su -`: Chuyển từ trạng thái User -> Root
- `nmcli connection show`: Xem danh sách card mạng ( Ở đây chỉ có mình card ens160).
- `sudo nmcli connection modify ens160 ipv4.address 192.168.154.129/24`: đặt IP tĩnh
- `sudo nmcli connection modify ens160 ipv4.gateway 192.168.154.3`: Đặt Gateway
- `sudo nmcli connection modify ens160 ipv4.method manual`: chuyển chế độ IP tĩnh
- `sudo nmcli connection up ens160`: Áp dụng thay đổi.

### Một số lỗi gặp phải khi fix CentOS 9
- Đây là lỗi DNS/network → máy CentOS không phân giải được tên miền mirrors.centos.org.

Khi chạy dnf install, dnf cần kết nối internet để tải metadata của repo. Nếu không ping/resolve được host thì sẽ báo lỗi này.
- Nguyên nhân: Cấu hình IP/DNS sai hoặc không có DNS (thường khi đặt IP tĩnh mà quên thêm nameserver).
- Khi dùng IP tĩnh với nmcli, nhớ phải khai bảo DNS nếu không sẽ lỗi.
```plaintext
nmcli con mod ens33 ipv4.dns "8.8.8.8 8.8.4.4"
nmcli con up ens33
```
