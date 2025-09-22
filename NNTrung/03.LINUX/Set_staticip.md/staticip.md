## Trên Ubuntu 24.04

Mở file cấu hình `netplan` (thường nằm trong `/etc/netplan/`):

```plaintext
sudo vim /etc/netplan/50-cloud-init.yaml
```

Kết quả:

![network card configuration file](./images/card_configuration_ubuntu.png)

Ấn `i` để chỉnh sửa nội dung, chỉnh sửa nội dung trong [ipv4] thành:

![reconfig card](./images/reconfig_card_ubuntu.png)

- `ens33`: Tên card mạng.
- `dhcl3: no`: tắt DHCP để dùng IP tĩnh.
- `addresses: - 192.168.3.70/24` địa chỉ IP và subnet mask.
- `gateway4: 192.168.3.1` gateway

Chỉnh sửa xong, ấn `Esc` để thoát khỏi chế độ `Insert`. Tiếp đó nhập `:wq` và `Enter` để lưu cấu hình.

Sau khi thực hiện thay đổi, cần restart để áp dụng thay đổi:

```plaintext
sudo netplan apply
```