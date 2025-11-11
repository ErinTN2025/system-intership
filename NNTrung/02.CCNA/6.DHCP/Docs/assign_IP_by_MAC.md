# Cấp phát IP theo địa chỉ MAC
## CentOS và Windows
### Xác định MAC của client
Kiểm tra địa chỉ MAC
- `ip a`: Ubuntu

![altimage](../Images/maclinux.png)

- `ipconfig /all`: Window

![altim](../Images/Macwindow.png)

### Chỉnh sửa file cấu hình DHCP server
Mở file cấu hình:
```plaintext
sudo nano /etc/dhcp/dhcpd.conf
```