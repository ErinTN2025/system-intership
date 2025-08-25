# Routing Protocols
## 1. Khái niệm
- Routing Protocol là tập hợp các quy tắc mà router sử dụng để trao đổi thông tin định tuyến với nhau, từ đó xây dựng và duy trì Routing Table.
- Khác với Routed Protocol( ví dụ: IP, IPv6) vốn chỉ là giao thức được định tuyến.
- Routing Protocol: cách các router nói chuyện với nhau để tìm đường.
- Routed Protocol: dữ liệu thực tế(IP packet) được gửi đi nhờ bảng định tuyến đó.

## 2. Chức năng của Routing Protocol
- Khám phá mạng lưới (network discovery)
- Trao đổi thông tin định tuyến với các router khác.
- Xác định đường đi tốt nhất( best path selection).
- Cập nhật bảng định tuyến khi có sự thay đổi topology(link down, thêm mạng mới...).
- Hỗ trợ cơ chế dự phòng(redundancy) và cân bằng tải (load balancing).

## 3. Phân loại Routing Protocol
- Interior Gateway Protocols (IGP) - chạy trong một hệ tự quản(AS- Autonomous System)
- Distance Vector Protocols:
  - RIP(Routing Information Protocol): đơn giản, metric = số hop, chậm, ít dùng hiện nay.
  - IGRP(Interior Gateway Routing Protocol - Cisco proprietary).
- Advanced Distance Vector/ Hybrid:
  - EIGRP (Enhaced IGRP - Cisco propretary): metric dựa trên băng thông, delay, tin cậy, tải.
- Link State Protocols:
  - OSPF(Open Shortest Path First): dùng thuật toán Dijkstra, metric dựa trên cost, hội tụ nhanh.
  - IS-IS(Intermediate System to Intermediate System): tương tự OSPF, hay dùng trong backbone của ISP.
- Exterior Gateway Protocols(EGP) - chạy giữa các AS(giữa các ISP với nhau)
  - BGP(Border Gateway Protocol): giao thức định tuyến "xương sống của Internet".
    - Sử dụng Path Vector(dựa vào AS-PATH, policies).
    - Rất linh hoạt, hỗ trợ chính sách định tuyến phức tạp.