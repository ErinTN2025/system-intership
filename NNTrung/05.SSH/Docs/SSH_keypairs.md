# Tìm hiểu SSH keypair
## Keypair là gì?
### 1. Khái niệm
SSH key pair (cặp khoá SSH) là một cơ chế xác thực an toàn cho giao thức SSH, bao gồm hai file khoá riêng biệt nhưng có liên quan mật thiết.
  - **Private key(Khoá riêng tư)**: Khoá này phải được giữ bí mật và an toàn trên máy tính của bạn. Nó tương tự như chiếc chìa khoá duy nhất có thể mở ổ khoá mà khoá công khai đã khoá.
  - **Public key(Khoá công khai)**: Khoá này được chia sẻ với các máy chủ mà bạn muốn truy cập. Bạn có thể coi nó như một ổ khoá mà bất kỳ ai cũng có thể nhìn thấy và sử dụng để khoá một hộp thư.

Khi kết nối SSH, máy host sẽ kiểm tra public key được gửi từ máy client và gửi số ngẫu nhiên được mã hoá bằng public key để máy client giải mã bằng private key.
### 2. Mục đích của SSH Keypair
Cung cấp một phương thức xác thực an toàn và tiện lợi hơn so với việc sử dụng mật khẩu truyền thống. Với key pair, có thể đăng nhập vào máy chủ SSH mà không cần nhập mật khẩu mỗi lần.
### 3. Cách thức hoạt động
`Bước 1`: Tạo keypair
- Sử dụng một công cụ (thường là `ssh-keygen`) để tạo một cặp khoá( public key và private key) trên máy tính.

`Bước 2`: Phân phối public key
- Sao chép khoá công khai lên máy chủ SSH muốn truy cập.