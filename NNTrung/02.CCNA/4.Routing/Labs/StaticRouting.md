# STATIC ROUTING LAB
![altimage](../Images/Staticroutinglab.png)

## 1. Mục tiêu

- Cấu hình địa chỉ IP cho PC và Router
- Thiết lập kết nối giữa hai mạng:
  - 192.168.1.0/24
  - 192.168.2.0/24
- Cấu hình định tuyến (Static Route hoặc RIP)
- Kiểm tra khả năng liên lạc giữa hai đầu mạng

---

## 2. Sơ đồ địa chỉ IP

### 2.1 LAN bên trái
| Thiết bị | Interface | IP Address | Subnet Mask |
|----------|-----------|------------|-------------|
| PC0 | NIC | 192.168.1.10 | 255.255.255.0 |
| Router4 | G0/0 | 192.168.1.1 | 255.255.255.0 |

Default Gateway của PC0: `192.168.1.1`

---

### 2.2 LAN bên phải
| Thiết bị | Interface | IP Address | Subnet Mask |
|----------|-----------|------------|-------------|
| Laptop0 | NIC | 192.168.2.10 | 255.255.255.0 |
| Router2 | G0/0 | 192.168.2.1 | 255.255.255.0 |

Default Gateway của Laptop0: `192.168.2.1`

---

### 2.3 Kết nối giữa các Router (/30)

| Kết nối | Network | Router A | Router B |
|----------|----------|-----------|-----------|
| R4 – R0 | 10.0.1.0/30 | 10.0.1.1 | 10.0.1.2 |
| R0 – R2 | 10.0.2.0/30 | 10.0.2.1 | 10.0.2.2 |
| R2 – R3 | 10.0.3.0/30 | 10.0.3.1 | 10.0.3.2 |
| R3 – R4 | 10.0.4.0/30 | 10.0.4.1 | 10.0.4.2 |

Subnet mask cho các mạng /30: `255.255.255.252`

---

## 3. Cấu hình Router
Lưu ý: Sau khi cấu hình IP phải dùng `no shutdown` để bật interface.

### 3.1 Router4

```bash
enable
configure terminal

interface g0/0
ip address 192.168.1.1 255.255.255.0
no shutdown

interface s0/0/0
ip address 10.0.1.1 255.255.255.252
no shutdown

interface s0/0/1
ip address 10.0.4.2 255.255.255.252
no shutdown
```

### 3.2 Router0
```bash
enable
configure terminal

interface s0/0/0
ip address 10.0.1.2 255.255.255.252
no shutdown

interface s0/0/1
ip address 10.0.2.1 255.255.255.252
no shutdown
```

### 3.3 Router 2
```bash
enable
configure terminal

interface g0/0
ip address 192.168.2.1 255.255.255.0
no shutdown

interface s0/0/0
ip address 10.0.2.2 255.255.255.252
no shutdown

interface s0/0/1
ip address 10.0.3.1 255.255.255.252
no shutdown
```

### 3.4 Router 3
```bash
enable
configure terminal

interface s0/0/0
ip address 10.0.3.2 255.255.255.252
no shutdown

interface s0/0/1
ip address 10.0.4.1 255.255.255.252
no shutdown
```

## 4. Cấu hình định tuyến

- Cấu trúc chung của lệnh: `ip route <destination-network> <subnet-mask> <next-hop-ip | exit-interface>`

### 4.1 Static Route
- Router 4
```bash
ip route 192.168.2.0 255.255.255.0 10.0.1.2
```

- Router 0
```bash
ip route 192.168.1.0 255.255.255.0 10.0.1.1
ip route 192.168.2.0 255.255.255.0 10.0.2.2
```

- Router 3
```bash
ip route 192.168.1.0 255.255.255.0 10.0.2.1
```

- Router 4
```bash
ip route 192.168.1.0 255.255.255.0 10.0.4.2
ip route 192.168.2.0 255.255.255.0 10.0.3.1
```

### 5. Kiểm tra cấu hình mạng

```bash
show ip interface brief
```