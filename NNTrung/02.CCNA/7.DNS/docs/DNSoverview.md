# DNS
### 1. Khái niệm
DNS (Domain Name System) là hệ thống dịch tên miền (human-readable) như example.com sang địa chỉ IP (ví dụ 93.184.216.34) mà máy tính và router dùng để định tuyến.

Nó hoạt động như “sổ địa chỉ” phân tán toàn cầu: bạn hỏi tên, DNS trả về địa chỉ tương ứng (cũng trả về mail servers, bản ghi xác thực, v.v.)

### 2. Chức năng của DNS
- **Phân giải tên miền thành địa chỉ IP**: Đây là chức năng chính. Khi bạn gõ một tên miền vào trình duyệt, hệ thống DNS sẽ tìm kiếm và trả về địa chỉ IP của máy chủ đang lưu trữ trang web đó. Nhờ có IP, trình duyệt mới biết phải kết nối đến đâu.
- **Phân giải ngược(Reverse DNS Lookup)**: DNS cũng có thể chuyển đổi ngược từ địa chỉ IP sang tên miền tương ứng (sử dụng bản ghi PTR). Điều này thường được dùng cho mục đích bảo mật, xác thực máy chủ email, hoặc ghi nhật ký.
- **Quản lý Lưu lượng Truy cập (Traffic Management)**:
  - Các bản ghi DNS cho phép nhà quản trị định tuyến (routing) lưu lượng truy cập cho các dịch vụ khác nhau như website, email, hoặc các dịch vụ phụ trợ đến các máy chủ cụ thể.
  - Nó còn hỗ trợ các kỹ thuật như cân bằng tải (Load Balancing) bằng cách luân phiên trả về nhiều địa chỉ IP khác nhau cho cùng một tên miền.
- **Quản lý các bản ghi DNS**:  DNS lưu trữ thông tin trong các bản ghi DNS, bao gồm các loại bản ghi như A (địa chỉ IPv4), AAAA (địa chỉ IPv6), CNAME (tên miền chấp nhận mệnh đề), MX (máy chủ thư điện tử) và nhiều loại khác.- được sử dụng cho mục đích xác minh quyền sở hữu tên miền, chống spam email, và các tính năng bảo mật khác.
### 4. Các bản ghi (record) quan trọng trong DNS
#### 1. A Record (Address Record)
- **Chức năng**: ánh xạ tên miền -> địa chỉ IPv4
```ruby
 example.com IN A 93.184.216.34
```
- Khi gõ `example.com`, trình duyệt sẽ dùng IP `93.184.216.34` để kết nối.
#### 2. AAAA Record (IPv6 Address Record)
- **Chức năng**: giống A record, nhưng dùng cho địa chỉ IPv6
```ruby
example.com     IN  AAAA    2606:2800:220:1:248:1893:25c8:1946
```
#### 3. CNAME Record (Canonical Name Record)
- **Chức năng**: trỏ một tên tới tên khác, dùng tạo bí danh (alias) cho một tên miền khác.
- Cấu trúc:
```ruby
Tên bí danh(Alias) IN CNAME Tên chuẩn(Canonical Name)
```
```ruby
www.example.com IN CNAME blog.example.com
```
Khi một người dùng hoặc hệ thống mạng yêu cầu địa chỉ IP của `www.example.com`, máy chủ DNS sẽ trả lời bằng cách nói: "`www.example.com` không có IP riêng, nó chỉ là bí danh của `blog.example.com`."
#### 4. MX Record (Mail Exchange Record)
- **Chức năng**: ánh xạ tên miền đến tên của máy chủ thư điện tử (Mail Server) mà máy chủ đó có thể tiếp nhận email.
```ruby
example.com IN MX 10 mail1.example.com.
example.com IN MX 20 mail1.example.com.
```
- Khi có email gửi đến example.com, máy chủ gửi sẽ thử gửi đến `mailserver1.example.com` trước vì nó có ưu tiên 10 (cao hơn).
- Nếu mailserver1.example.com không phản hồi, máy chủ gửi sẽ thử gửi đến `mailserver2.example.com` với ưu tiên 20 (dự phòng).
- Bản ghi MX luôn trỏ đến một tên miền khác, KHÔNG BAO GIỜ trỏ trực tiếp đến một địa chỉ IP.
#### 5.  TXT Record (Text Record)
- **Chức năng**: chứa dữ liệu văn bản, dùng cho:
  - Xác thực email(SPF, DKIM, DMARC).
- `NS`: Name server (delegation)
- `SOA`: Start of Authority (metadata zone: primary server, serial, refresh/retry/expire, TTL).
- `TXT`: văn bản (dùng cho SPF, DKIM, verifications)
- `SRV`: dịch vụ (service discovery, nội dung: priority, weight, port, target). 
- `PTR`: reverse lookup( IP -> tên)
- `DS, DNSKEY, RRSIG`: liên quan DNSSEC( chữ ký và khóa)