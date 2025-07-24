<h1 style="text-align: center;">OSI MODEL</h1>

## Seven layers of the OSI model

#### 1. Why we need the OSI model ?
- Reduces complexity: Chia thành nhiều nhóm công việc, mỗi nhóm có các công việc tương tự nhau. Các công việc được chia ra, chuyên biệt hóa, mỗi vùng, mỗi tổ chức chỉ phải xử lý chuyên biệt, riêng 1 công việc mà không cần xử lý từ đầu đến cuối.
- Standardizes interfaces: Quy định chung 1 chuẩn bắt buộc các nhà sản xuất khi đã tham gia vào phải tuân theo, đảm bảo giao tiếp được giữa người dùng với người dùng qua các hãng khác nhau.
- Facilitates modular engineering: Đảm bảo tích tương thích về mặt công nghệ, thiết bị của các hãng khác nhau có thể giao tiếp được với  nhau.
- Ensures interoperable technology
- Accelerates evolution
- Simplifies teaching and learning

##### 1.1 Physical Layer:
- Chức năng truyền 1 dòng bit qua 1 đường truyền vật lý cụ thể, định nghĩa các thủ tục chức năng, đặc tính kỹ thuật cho việc thiết lập duy trì một kết nối vật lý nào đó.
Ví dụ nối giữa PC với switch phải dùng cái gì, vật liệu như nào, bao nhiêu chân, bao nhiêu mét, bit được truyền trong bao nhiêu Volt, tốc độ, phương thức đường truyền.

##### 1.2 DataLink Layer:
- Điều khiển việc truy nhập vào đường truyền vật lý, định nghĩa **format dữ liệu** và làm thế nào để dạng dữ liệu đó tiếp cận vào đường truyền vật lý. Cung cấp cơ chế dò lỗi. Thực hiện chức năng giao tiếp với các lớp bên trên.

##### 1.3 Network Layer:
- Chịu trách nhiệm cho việc phân bố dữ liệu từ điểm này đến điểm kia một cách tối ưu nhất: định tuyến các gói dữ liệu, chọn ra một đường đi tối ưu nhất. Định nghĩa một giao thức để chọn đường đi tối ưu nhất. ( Giao thức định tuyến). Cung cấp địa chỉ logic và lựa chọn đường đi.

##### 1.4 Transport Layer:
- Quản lý kết nối END TO END: Xử lý các vấn đề truyền dẫn giữa các hosts. Đảm bảo dữ liệu được truyền tải một cách đáng tin cậy. Đảm bảo duy trì và kết thúc các đường mạch ảo. Cung cấp cơ chế sửa lỗi, dò lỗi tin cậy, cơ chế phục hồi thông tin bằng điều khiển luồng.

##### 1.5 Session Layer:
- Giải quyết vấn đề Làm thế nào các ứng dụng có thể truy cập vào được đường truyền này.
- Truyền thông Interhost (Giao tiếp giữa các máy chủ) bằng cách thiết lập, quản lý và kết thúc các phiên trao đổi trong ứng dụng. Đứng ra tổ chức các phiên kết nối để phân biệt giữa ứng dụng và các kết nối ứng dụng với nhau.

##### 1.6 Presentation Layer:
- Giải quyết ứng dụng này truyền chưa chắc ứng dụng kia đã hiểu --> cần người phiên dịch.
- Đảm bảo dữ liệu có thể đọc được bởi thiết bị nhận, tổ chức, format, structure lại dữ liệu. thương lượng cú pháp truyền cho application Layer. Cung cấp cơ chế mã hóa. Đảm bảo 2 tầng application ở 2 đầu có thể nói chuyện được với nhau.

###### 1.7 Application Layer:
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