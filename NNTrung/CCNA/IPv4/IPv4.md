# IPv4

![Ipv4](https://www.cloudns.net/blog/wp-content/uploads/2023/03/IPv4-Address-Format.png)

## Định nghĩa
[IPv4](https://vi.wikipedia.org/wiki/IPv4) (Internet Protocol version 4) là phiên bản thứ tư của giao thức Internet (IP), IPv4 hoạt động ở tầng 3 (Network Layer) của mô hình OSI (Open Systems Interconnection). Tầng này chịu trách nhiệm định tuyến các gói dữ liệu từ nguồn đến đích qua các mạng khác nhau.

## Mục đích của IPv4
- Cung cấp địa chỉ duy nhất cho từng host.
- Xác định đường đi của các thiết bị từ thiết bị gửi đến thiết bị nhận.
- Chia nhỏ dữ liệu thành các packets nhỏ để truyền qua mạng và ghép lại ở đích.
- Bao gồm kiểm tra tổng thể để phát hiện lỗi trong quá trình truyền.

## Đặc điểm chính
- Địa chỉ dài 32 bit, biểu diễn thành 4 số thập phân(192.168.1.1)
- 32 bits địa chỉ của IP được chia thành 4 nhóm (dạng phân nhóm - dotted format), mỗi nhóm gồm 8 bits (gọi là một octet), các nhóm này phân cách nhau bởi dấu chấm. 
- Không được tích hợp sẵn bảo mật
- Số lượng địa chỉ giới hạn khoảng 4,3 tỷ thiết bị. Do số lượng địa chỉ giới hạn, IPv4 đang dần bị thay thế bởi IPv6.

## Phân loại các lớp địa chỉ IPv4

### Lớp A
- Dải địa chỉ: 1.0.0.0 đến 126.0.0.0
  - Được sử dụng cho các tổ chức lớn với lượng địa chỉ lớn. Mỗi địa chỉ A có thể hỗ trợ 16 triệu máy.

### Lớp B
- Dải địa chỉ : 128.0.0.0 đến 191.255.0.0
  - Được sử dụng cho các tổ chức phân bố trung bình. Mỗi địa chỉ B hỗ trợ khoảng 65000 máy.

### Lớp C
- Dải địa chỉ: 192.0.0.0 đến 223.255.255.0  
  - Được sử dụng cho các tổ chức nhỏ với nhu cầu địa chỉ ít. Mỗi địa chỉ C hỗ trợ khoảng 254 máy.

### Lớp D
- Dải địa chỉ: 224.0.0.0 đến 239.255.255.255
  - Được sử dụng truyền tải đa điểm dữ liệu đến nhiều thiết bị.

### Lớp E (Dự trữ)
- Dải địa chỉ: 244.0.0.0 đến 255.255.255.255
  - Được sử dụng dự trữ và thử nghiệm.

**_Ví dụ: 192.168.0.1_**

**1 địa chỉ IPv4 có 2 phần** là _phần mạng_ và _phần network_
- 192.168 là phần network: thuốc lớp C
- 0.1 là thiết bị cụ thể, 0 là số hiệu mạng con, 1 là thiết bị cụ thể trong mạng con đó.
- 192.168.0 là phần mạng, tất cả các thiết bị chung mạng sẽ có cấu trúc như này
- Địa chỉ này giúp các thiết bị nhận biết, liên lạc với nhau và với router tại tầng mạng của mô hình OSI.

## IPv1, 2, 3
Các địa chỉ IPv1, IPv2 và IPv3 có tồn tại nhưng:
- Những phiên bản này là các bản thiết kế thử nghiệm ban đầu khi phát triển giao thức Internet Protocol (IP) cho ARPANET.

- Chúng chưa bao giờ được tiêu chuẩn hóa thành giao thức công cộng.

- Chúng chỉ tồn tại trong nội bộ các nhóm nghiên cứu. 

## IPv5 

- IPv5 có tồn tại, nhưng nó là tên của một giao thức Internet Stream Protocol (ST, hoặc ST-II) để thử nghiệm truyền tải voice/video streaming qua IP.

- Nó không phải là kế thừa trực tiếp của IPv4 — mà chỉ dùng chung hạ tầng.

- Không trở thành chuẩn phổ biến.

- Khi chuẩn bị phát triển IP thế hệ tiếp theo, người ta tránh dùng số 5 để không nhầm lẫn với Stream Protocol → đặt tên là IPv6.

## IP public và IP private

**IP Public**

- IP Public  là địa chỉ IP được cung cấp bởi nhà cung cấp dịch vụ Internet (ISP) và được sử dụng để xác định thiết bị hoặc mạng của bạn trên Internet. Mỗi thiết bị kết nối trực tiếp với Internet đều có một địa chỉ IP công cộng duy nhất (trên toàn cầu).

- IP Private là địa chỉ IP được sử dụng trong các mạng nội bộ (LAN) như trong gia đình, công ty hoặc trường học. Các địa chỉ này không thể truy cập trực tiếp từ Internet và được dùng để giao tiếp giữa các thiết bị trong cùng một mạng nội bộ.

## Multicast và Broadcast

**1 Broadcast (Phát sóng rộng rãi)**

- Broadcast là hình thức gửi dữ liệu từ một thiết bị tới tất cả các thiết bị khác trong cùng một mạng LAN hoặc subnet.
- Gói tin broadcast sẽ được gửi đến địa chỉ IP đặc biệt (ví dụ: 255.255.255.255 trong IPv4), tất cả các thiết bị trong mạng sẽ nhận được dữ liệu này.
- Broadcast thường được sử dụng trong các giao thức như ARP, DHCP.
- Nhược điểm: Tiêu tốn băng thông mạng vì tất cả các thiết bị đều phải xử lý gói tin, dễ gây “ngập lụt” mạng (broadcast storm) nếu sử dụng quá mức.


**2 Multicast (Phát sóng nhóm)**

- Multicast là hình thức gửi dữ liệu từ một thiết bị đến một nhóm các thiết bị nhất định (không phải tất cả).
- Chỉ những thiết bị đăng ký (tham gia nhóm multicast) mới nhận được dữ liệu này.
- Địa chỉ multicast trong IPv4 thường nằm trong dải 224.0.0.0 đến 239.255.255.255.
- Multicast rất hữu ích cho các ứng dụng truyền hình trực tuyến, hội nghị video, hoặc truyền dữ liệu đến nhiều người cùng lúc mà không phải gửi nhiều bản tin giống nhau (tiết kiệm băng thông).

| Tiêu chí            | Broadcast                    | Multicast                          |
|---------------------|-----------------------------|------------------------------------|
| Đối tượng nhận      | Tất cả trong mạng           | Một nhóm thiết bị nhất định        |
| Địa chỉ IP dùng     | 255.255.255.255 (IPv4)      | 224.0.0.0 – 239.255.255.255        |
| Tiết kiệm băng thông| Không                       | Có                                 |
| Ứng dụng            | ARP, DHCP                   | Truyền hình, Video Conference      |

## Subnet, Subnet Mask và Prefix

**Subnet**

- Subnet (mạng con) là một phần nhỏ của một mạng lớn hơn, được tạo ra bằng cách chia nhỏ một mạng IP lớn thành các mạng nhỏ hơn.
- Mỗi subnet hoạt động như một mạng độc lập trong phạm vi tổng thể, giúp quản lý và sử dụng tài nguyên mạng hiệu quả hơn, tăng tính bảo mật và giảm thiểu lưu lượng broadcast.

**Subnet Mask**

- Subnet mask là dãy số 32 bit được dùng với địa chỉ IP để xác định phần nào là địa chỉ mạng và phần nào là địa chỉ host trong một địa chỉ IP.
- Subnet mask thường được viết dưới dạng thập phân, ví dụ: 255.255.255.0.
- Các bit “1” trong subnet mask xác định phần địa chỉ mạng, còn các bit “0” xác định phần host.

**Prefix**

- Prefix là cách viết khác của subnet mask, biểu diễn bằng số lượng bit “1” liên tiếp trong subnet mask (ký hiệu /n).
- Ví dụ:
  - Subnet mask 255.255.255.0 tương đương với prefix /24 (vì có 24 bit “1”).
  - 255.255.255.128 tương đương với /25.