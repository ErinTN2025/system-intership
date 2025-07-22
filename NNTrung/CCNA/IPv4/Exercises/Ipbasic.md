## 1. Cho biết địa chỉ nào sau đây có thể dùng cho host:
- 150.100.255.255
- 175.100.255.18
- 195.234.253.0
- 100.0.0.23
- 188.258.221.176
- 127.34.25.189
- 224.156.217.73

- **150.100.255.255** thuộc lớp B nên 2 octet đầu là network, 2 octet sau là host, có tất cả phần host đều là bit "1" nên không thể dùng làm địa chỉ host. --> địa chỉ broadcast.
- **175.100.255.18** thuộc lớp B nên có 2 octet đầu là network, 2 octet sau là host, phù hợp dùng làm địa chỉ host.
- **195.234.253.0** thuộc lớp C nên có 3 octet đầu là network, 1 octet sau là host, có tất cả bit phần host là 0 nên là địa chỉ mạng, không phù hợp làm địa chỉ host.
- **100.0.0.23**  phù hợp làm địa chỉ host.
- **188.258.221.176** 1 octet chỉ từ 0-255 258 vượt quá địa chỉ IP không hợp lệ.
- **127.34.25.289** đây là địa chỉ IP loopback.
- **224.156.217.73** thuộc lớp D dùng làm địa chỉ IP multicast, không phù hợp làm địa chỉ Host.

Vậy địa chỉ phù hợp chỉ có: 175.100.255.18, 100.0.0.23 