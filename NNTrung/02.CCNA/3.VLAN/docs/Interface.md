# Interface
```yaml
networking:
  IFACE: "bond0"
  vlan:
    VLAN_INTERFACE_NAME: "bond0"
```
`IFACE` thường đơn giản là viết tắt của interface — tức card/cổng mạng mà phần mềm sẽ sử dụng. Ở đây interface được chọn có tên là `bond0`.

`bond0` không phải card mạng vật lý. Nó là một interface logic được tạo bằng Linux Bonding, dùng để ghép nhiều NIC vật lý lại với nhau.

Ví dụ:

```
eno1 ──┐
       ├── bond0 ─── IP: 192.168.10.20
eno2 ──┘
```

Mục đích thường là HA/redundancy, tăng băng thông trong một số mode, hoặc kết nối server tới 2 switch.

- Ví dụ rất phổ biến:
```
Server
┌────────────────────────┐
│                        │
│ eno1 ───────── Switch A│
│    \                   │
│     bond0              │
│    /                   │
│ eno2 ───────── Switch B│
│                        │
└────────────────────────┘
```
- Hay ví dụ VLAN trên bond0
```
eno1 ──┐
       ├── bond0 ──┬── bond0.100
eno2 ──┘           │
                   ├── bond0.200
                   │
                   └── bond0.300
```
- Trong đó:
```
bond0
├─ bond0.100   VLAN 100
├─ bond0.200   VLAN 200
└─ bond0.300   VLAN 300
```
- Traffic đi theo kiểu:
```
Application
    ↓
bond0.100
    ↓
802.1Q VLAN tag 100
    ↓
bond0
    ↓
eno1 / eno2
    ↓
Switch
```

| Interface | Ví dụ | Dùng để làm gì |
|---|---|---|
| Physical NIC | `eth0`, `ens33`, `eno1` | Card mạng thật |
| Bond | `bond0` | Ghép nhiều NIC |
| VLAN | `bond0.100`, `ens33.100` | Chia VLAN 802.1Q |
| Bridge | `br0`, `br-ex` | Switch Layer 2 ảo |
| OVS Bridge | `br-int`, `br-ex`, `br-tun` | Switch ảo Open vSwitch |
| veth | `vethabc123` | Nối container/network namespace |
| TAP | `tapXXX` | VM kết nối vào network |
| TUN | `tun0` | Tunnel Layer 3/VPN |
| VXLAN | `vxlan0` | Overlay network |
| Loopback | `lo` | Localhost |
| Dummy | `dummy0` | Interface ảo |
| Wireless | `wlan0` | Wi-Fi |