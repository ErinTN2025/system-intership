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
- Địa chỉ này giúp các thiết bị nhận biết, liên lạc với nhau và với router tại tầng mạng của mô hình OSI.

