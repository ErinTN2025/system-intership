# VLAN Trunking Protocol
VLAN Trunking Protocol(VTP) là một giao thức do Cisco phát triển dùng để quản lý và phân phối thông tin VLAN giữa các switch trong cùng một VTP domain. Nó giúp tự động đồng bộ, cầu hình VLAN giữa nhiều Switch, thay vì phải tạo thủ công từng VLAN trên từng thiết bị.
## 1. Kết nối Trunk
- Kết nối “trunk” là liên kêt Point-to-Point giữa các cổng trên switch với router hoặc với các switch khác trên mạng cho phép truyền nhiều VLAN (Virtual Local Area Network) qua một đường truyền duy nhất.
- Vì kỹ thuật này cho phép dùng chung một kết nối vật lý cho dữ liệu của các VLAN đi qua nên dể phân biệt được chúng là dữ liệu của VLAN nào, người ta gắn vào các gói tin một dấu hiệu gọi là “tagging”. Hay nói cách khác là dùng một kiểu đóng gói riêng cho các gói tin di chuyển qua đường “trunk” này. Giao thức được sử dụng là 802.1Q (dot1 q).
- Mục đích: Tiết kiệm cáp, kết nối nhiều VLAN giữa các thiết bị mà không cần cáp riêng cho từng VLAN.

## Chuẩn IEEE 802.1Q(DOT1Q)

![vlantag](../images/VLANtag.png)

### Khái niệm
- IEEE 802.1Q là một chuẩn giao thức mạng do IEEE phát triển, dùng để hỗ trợ VLAN (Virtual Local Area Network) trên mạng Ethernet.
- Mục đích chính: Cho phép gắn thẻ (tagging) các frame Ethernet để phân biệt dữ liệu thuộc các VLAN khác nhau khi truyền qua một trunk link giữa các thiết bị mạng (switch-switch hoặc switch-router).
- Dot1Q là chuẩn phổ biến nhất để thực hiện VLAN trunking, thay thế cho chuẩn ISL (Inter-Switch Link) độc quyền của Cisco, nhờ tính tương thích cao và hiệu quả.
### Cách hoạt động
  - **Tagging (gắn thẻ):** Khi một frame từ một VLAN đi qua trunk port, switch gắn một VLAN tag (thường là 802.1Q tag, 4 byte) vào header của frame. Tag này chứa thông tin về VLAN ID(12 bit, hỗ trợ tối đa 4096 VLAN). Frame được gửi qua trunk link đến thiết bị khác (switch hoặc router).
  - **Xử lý ở đầu nhận**: Thiết bị nhận (switch/router) đọc VLAN tag, xác định frame thuộc VLAN nào (VD: VLAN 10).
  Switch tách tag ra và chuyển frame đến các port thuộc VLAN tương ứng (hoặc xử lý tiếp nếu là router). Nếu frame thuộc native VLAN (mặc định VLAN 1 trên Cisco), nó không được gắn tag để tiết kiệm băng thông và tương thích với thiết bị không hỗ trợ 802.1Q.
  - **Truyền qua Trunk** Trunk Link thường là Ethernet hoặc quang mang frame của nhiều VLAN, mỗi frame được gắn tag để phân biệt (trừ native VLAN). Các thiết bị phải cấu hình trunk port với giao thức 802.1Q và danh sách VLAN được phép (allowed VLANs).
  - **Native VLAN**: Frame của Native VLAN đi qua Trunk mà không gắn Tag, giúp tương thích với thiết bị không hỗ trợ VLAN hoặc giảm xử lý cho VLAN mặc định. Nếu hai đầu Trunk có Native VLAN khác nhau(miscòniguration), có thể gây lỗi (VLAN mismatch).
  - **Ứng dụng**: Kết nối switch-switch: Cho phép nhiều VLAN (VD: VLAN 10, 20, 30) chia sẻ một cáp. Router-on-a-Stick: Router dùng một giao diện trunk để định tuyến giữa các VLAN. Mạng doanh nghiệp lớn: Quản lý lưu lượng VLAN hiệu quả, tách biệt dữ liệu các phòng ban.
### Thành phần của IEEE 802Q.1

![alt](../images/8021Q.png)

- Frame 802Q.1 [Destination MAC | Source MAC | 802.1Q Tag | Type/Length | Data | FCS]
- 802Q.1 Tag gồm: 
  - **Tag protocol Identifier (TPID)** (2byte):
    - Giá trị cố định: **0x8100**, cho biết Frame này dùng chuẩn 802.1Q
    - Giúp thiết bị nhận diện Frame có VLAN Tag.
  - **Tag Control Information (TCI)** (2byte):
    - Priority Code Point (PCP) (3bit): Xác định độ ưu tiên (0-7) cho QoS (Quality of Service), dùng để ưu tiên lưu lượng trong mạng đông.
    - Drop Eligible Indicator (DEI) (1bit): Chỉ định frame có thể bị drop khi mạng tắc nghẽn (thường dùng cho QoS).
    - VLAN Identifier (VID) (12 bit): Xác định VLAN ID(1-4094; 0 và 4095 dành riêng ).
  - **Frame Size**: tối đa 1522

  **Thành phần liên quan**
    - **Trunk Port**: Port trên Switch, Router được cấu hình để mang nhiều VLAN, sử dụng 802.1Q Tagging.
    - **Native VLAN**: VLAN không cần Tag (mặc định VLAN 1).
    - **Allowed VLANs**: Danh sách VLAN được phép đi qua Trunk, cấu hình để giới hạn lưu lượng.
    - **Hỗ trợ 802.1Q**: Hầu hết Switch hiện đại (Cisco, Juniper, Hp) hỗ trợ 802.1Q để xứ lý Tagging, detagging.

## 2. Khái niệm
- VTP hoạt động ở Data Link Layer theo mô hình OSI.
- Cho phép một switch (thường là server mode) quản lý danh sách VLAN và truyền thông tin đó cho các switch khác (client mode).
- Khi VLAN mới được thêm, xóa hoặc đổi tên ở switch server, các switch client cùng domain sẽ tự động cập nhật cấu hình VLAN của mình.
## 3. Hoạt động của VTP
- VTP gửi thông điệp quảng bá qua “VTP domain” mỗi 5 phút một lần, hoặc khi có sự thay đổi xảy ra trong quá trình cấu hình VLAN. Một thông điệp VTP bao gồm “rivision-number”, tên VLAN (VLAN name), số hiệu VLAN.
- Bằng sự cấu hình VTP Server và việc quảng bá thông tin VTP tất cả các switch đều đồng bộ về tên VLAN và số liệu VLAN của tất cả các VLAN.
- Một trong những thành phần quan trọng trong các thông tin quảng bá VTP là tham số “revision-number”.  Mỗi thành phần VTP server điều chỉnh thông tin VLAN, nó tăng “revision-number” lên 1, rồi sau đó VTP Server mới gửi thông tin quảng bá VTP đi. Khi một switch nhận một thông điệp VTP với “revision-number” lớn hơn, nó sẽ cập nhật cấu hình VLAN.

![altimg](../images/vtpvlan.png)

- Switch ở chế độ VTP Server có thể tạo, chỉnh sửa và xóa VLAN. VTP server lưu cấu hình VLAN trong NVRAM của nó. VTP Server gửi thông điệp ra tất cả các cổng” trunk”.
- Switch ở chế độ VTP client không tạo, sửa và xóa thông tin VLAN. VTP Client có chức năng đáp ứng theo mọi sự thay đổi của VLAN từ Server và gửi thông điệp ra tất cả các cổng “trunk” của nó. VTP Client đồng bộ cấu hình VLAN trong hệ thống.
- Switch ở chế độ transparent sẽ nhận và chuyển tiếp các thông điệp quảng bá VTP do các switch khác gửi đến mà không quan tâm đến nội dung của các thông điệp này. Nếu “transparent switch” nhận thông tin cập nhật VTP nó cũng không cập nhật vào cơ sở dữ liệu của nó; đồng thời nếu cấu hình VLAN của nó có gì thay đổi, nó cũng không gửi thông tin cập nhật cho các switch khác. Trên “transparent switch” chỉ có một việc duy nhất là chuyển tiếp thông điệp VTP. Switch hoạt động ở “transparent-mode” chỉ có thể tạo ra các VLAN cục bộ. Các VLAN này sẽ không được quảng bá đến các switch khác.

![altimg](../images/vtpmodes.png)

## Access Port và Trunk Port