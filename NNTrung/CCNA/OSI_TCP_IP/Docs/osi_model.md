<h1 style="text-align: center;">OSI MODEL</h1>

## Mục lục

1. [Khái quát về mô hình OSI](#1-khái-quát-về-mô-hình-osi )   
    1.1 [Mô hình OSI là gì](#11-mô-hình-osi-là-gì)         
    1.2 [Tại sao chúng ta cần mô hình OSI](#12-tại-sao-chúng-ta-cần-mô-hình-osi)
2. [Các tầng trong mô hình OSI](#2-các-tầng-trong-mô-hình-osi)  
    2.1 [Tầng vật lý](#21-tầng-vật-lý-physical-layer)  
    2.2 [Tầng liên kết dữ liệu](#22-tầng-liên-kết-dữ-liệu-data-link-layer)  
    2.3 [Tầng mạng](#23-tầng-mạng-network-layer)  
    2.4 [Tầng giao vận](#24-tầng-giao-vận-transport-layer)  
    2.5 [Tầng phiên](#25-tầng-phiên-session-layer)  
    2.6 [Tầng trình diễn](#26-tầng-trình-diễn-presentation-layer)  
    2.7 [Tầng ứng dụng](#27-tầng-ứng-dụng-application-layer)  
3. [Workflow với mô hình OSI](#3-workflow-với-mô-hình-osi)

## 1. Khái quát về mô hình OSI

#### 1.1 Mô hình OSI là gì
- OSI (Open Systems Interconnection) là mô hình tham chiếu kết nối các hệ thống mở, một mô hình được phát triển bởi tổ chức quốc tế và tiêu chuẩn hóa (ISO). Nó mô tả cách các thiết bị mạng và phần mềm giao tiếp với nhau qua các tầng (Layers). Mục tiêu chính của mô hình OSI là tạo ra 1 chuẩn chung cho việc truyền thông mạng, giúp các nhà sản xuất thiết bị mạng và phần mềm có thể tương thích với nhau một cách dễ dàng.
#### 1.2 Tại sao chúng ta cần mô hình OSI 
 Chúng ta cần có mô hình OSI vì nhiều lý do nhưng sau đây là các ý chính tiêu biểu.
- Reduces complexity: Chia thành nhiều nhóm công việc, mỗi nhóm có các công việc tương tự nhau. Các công việc được chia ra, chuyên biệt hóa, mỗi vùng, mỗi tổ chức chỉ phải xử lý chuyên biệt, riêng 1 công việc mà không cần xử lý từ đầu đến cuối.
- Standardizes interfaces: Quy định chung 1 chuẩn bắt buộc các nhà sản xuất khi đã tham gia vào phải tuân theo, đảm bảo giao tiếp được giữa người dùng với người dùng qua các hãng khác nhau.
- Facilitates modular engineering: Tạo điều kiện để chuyên môn hóa cho kỹ sư, một công ty chuyên biệt giải quyết 1 tầng sẽ đạt hiệu quả cao hơn việc phải làm tất cả các công việc.
- Ensures interoperable technology: Đảm bảo tích tương thích về mặt công nghệ, thiết bị của các hãng khác nhau có thể giao tiếp được với  nhau.
- Accelerates evolution: Kỹ năng tăng cao, tốc độ và năng suất cũng sẽ tăng.
- Simplifies teaching and learning: Tạo điều kiện thuận lợi để học và giảng dạy khi chia ra các lớp.

## 7 Layers trong mô hình OSI
![altimage](../Images/OSI_model.png)
![altimage](../Images/osi_layer.png)

#### 1.1 Physical Layer (Tầng Vật Lý)
- Tầng Physical là tầng số 1. Thấp nhất trong mô hình OSI, chịu trách nhiệm truyền 1 dòng bit qua 1 đường truyền vật lý cụ thể.
- Không cần quan tâm đến dữ liệu nghĩa là gì, nó chỉ lo chuyển đổi dữ liệu thành tín hiệu vật lý và truyền đi qua môi trường vật lý. Bit 0 và 1 trong máy tính sẽ được biến thành Dòng điện (cáp đồng), Ánh sáng(Cáp quang), Sóng vô tuyến(Wi-Fi, Bluetooth). Nó sẽ tạo ra một đường truyền vật lý ổn định và đáng tin cậy để tầng cao hơn có thể gửi và nhận dữ liệu.
- **Chức năng chính**: 
    - Truyền bit: Chuyển bit 0/1 thành tín hiệu vật lý và ngược lại. 
    - Xác định đặc tính tín hiệu: Điện áp, cường độ sóng, tần số và bước sóng.
    - Quy định đầu nối và giao diện: Kiểu giắc cắm, chân cắm, chuẩn cáp (RJ45, USB, v.v.).
    - Điều khiển chế độ truyền: Simplex(một chiều),Half-Duplex, Full-Duplex.
    - Đồng bộ bit: Đảm bảo người gửi và nhận hiểu đúng điểm bắt đầu/ kết thúc bit.
    - Cách đấu nối vật lý: Topology vật lý: Bus, Star, Ring, Mesh.
    - Chuẩn hóa tốc độ truyền: Tốc độ bit (bit rate): bao nhiêu bit/ giây (bps).

- **Ví dụ thiết bị & công nghệ**:
  - Cáp xoắn đôi(UTP/STP): mang tín hiệu điện,  Cáp quang(Fiber): Mang tín hiệu ánh sáng, Card mạng (NIC): Chuyển đổi tín hiệu giữa máy tính và cáp, Hub: Thiết bị thu và phát tín hiệu điện, Repeater: Khuếch đại tín hiệu để đi xa hơn. Đầu nối RJ45, cổng USB, jack cáp quang: Chuẩn đầu cắm. WI-FI adapter, Bluetooth: Chuẩn tín hiệu thành sóng vô tuyến.

![altimage](../Images/Physical_Layer.png)
#### 1.2 DataLink Layer
- Điều khiển việc truy nhập vào đường truyền vật lý, định nghĩa **format dữ liệu** và làm thế nào để dạng dữ liệu đó tiếp cận vào đường truyền vật lý. Cung cấp cơ chế dò lỗi. Thực hiện chức năng giao tiếp với các lớp bên trên.

#### 1.3 Network Layer
- Chịu trách nhiệm cho việc phân bố dữ liệu từ điểm này đến điểm kia một cách tối ưu nhất: định tuyến các gói dữ liệu, chọn ra một đường đi tối ưu nhất. Định nghĩa một giao thức để chọn đường đi tối ưu nhất. ( Giao thức định tuyến). Cung cấp địa chỉ logic và lựa chọn đường đi.

#### 1.4 Transport Layer
- Quản lý kết nối END TO END: Xử lý các vấn đề truyền dẫn giữa các hosts. Đảm bảo dữ liệu được truyền tải một cách đáng tin cậy. Đảm bảo duy trì và kết thúc các đường mạch ảo. Cung cấp cơ chế sửa lỗi, dò lỗi tin cậy, cơ chế phục hồi thông tin bằng điều khiển luồng.

#### 1.5 Session Layer
- Giải quyết vấn đề Làm thế nào các ứng dụng có thể truy cập vào được đường truyền này.
- Truyền thông Interhost (Giao tiếp giữa các máy chủ) bằng cách thiết lập, quản lý và kết thúc các phiên trao đổi trong ứng dụng. Đứng ra tổ chức các phiên kết nối để phân biệt giữa ứng dụng và các kết nối ứng dụng với nhau.

#### 1.6 Presentation Layer
- Giải quyết ứng dụng này truyền chưa chắc ứng dụng kia đã hiểu --> cần người phiên dịch.
- Đảm bảo dữ liệu có thể đọc được bởi thiết bị nhận, tổ chức, format, structure lại dữ liệu. thương lượng cú pháp truyền cho application Layer. Cung cấp cơ chế mã hóa. Đảm bảo 2 tầng application ở 2 đầu có thể nói chuyện được với nhau.

#### 1.7 Application Layer
- Giao tiếp trực tiếp với người dùng, cung cấp các dịch vụ mạng như là email, file,..etc.., cung cấp user authentication. (cơ chế xác thực người dùng)

#### How does OSI model work?
- Từ Sender khi gửi 1 tập User Data qua bên máy nhận phải đi qua các tầng từ Application tới các bit nhị phân ở Physical Layer, đầu tiên đi vào tầng Application sẽ được đóng một cái header ( Header chính là phần vào đầu, là phần thông tin quản lý của một gói tin, địa chỉ, tính chất, đặc tính sử dụng,...). Khi toàn bộ được đưa xuống lớp Presentation, nó sẽ được bọc thêm 1 lớp Header nữa và coi toàn bộ những thứ trên thành một lớp dữ liệu... Toàn bộ gói tin lớp trên -> data lớp dưới.
- Riêng ở lớp thứ 2 bọc thêm kiểm tra lỗi FCS.
- Khi đi xuống lớp Physical toàn bộ sẽ được chuyển thành các cái bits.
- Ở phía Receiver, tiến trình được diễn ra ngược lại. Dòng bits nhị phân đi vào đường truyền vật lý và được đưa dần, bóc tét dần lên phía Application Layer.

**Tiến trình truyền thông ngang hàng**
- Đơn vị dữ liệu của lớp Transport: Segments, Network: Packets, Data-Link: Frames, Physical: bits.

---

<h1 style="text-align: center;">TCP/IP</h1>

## TCP/IP Transport Layer 