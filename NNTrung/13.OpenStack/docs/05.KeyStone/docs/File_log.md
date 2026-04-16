## File log của Keystone
Để troubleshoot Keystone, hãy xem log chính tại:
### 1. File cấu hình chính
Cấu hình vị trí log qua file
```bash
/etc/keystone/logging.conf
```
- Đây là file cấu hình riêng biệt cho hệ thống logging của Keystone.
- File này sử dụng định dạng của Python logging module (config file format), không phải định dạng thông thường của keystone.conf.

Cách kích hoạt: 
- Trong file `/etc/keystone/keystone.conf`, bạn phải chỉ định dòng sau trong phần `[DEFAULT]`:
```INI
log_config_append = /etc/keystone/logging.conf
```
Khi dùng `log_config_append`, toàn bộ cấu hình logging sẽ bị lấy hoàn toàn từ file logging.conf, các tùy chọn logging khác trong keystone.conf (như log_dir, log_file, debug...) sẽ bị bỏ qua.

### 2. File Log mặc định
Đường dẫn chính
```bash
/var/log/keystone/keystone.log
```
- Đây là nơi Keystone ghi hầu hết các log (request, lỗi, thông tin hoạt động...).
- Thư mục `/var/log/keystone/` thường do user `keystone` sở hữu.
- Có một tùy chọn đặc biệt gọi là `insecure_debug`: Nếu bật lên, các thông báo lỗi sẽ chứa thông tin nhạy cảm về bảo mật (ví dụ: lý do tại sao xác thực thất bại). Chỉ nên bật khi đang debug, không dùng trong production.
- Log sẽ hiển thị các thành phần trong request WSGI và lỗi (nếu có).
- Nếu không thấy request nào trong log, hãy chạy lệnh Keystone với tham số `--debug`.

### 3. Logging (Ghi log)
Keystone cho phép cấu hình logging riêng biệt so với các service OpenStack khác.
- Tên file cấu hình logging được chỉ định qua tùy chọn `log_config_append` trong phần `[DEFAULT]` của file `/etc/keystone/keystone.conf`.
- Để gửi log qua syslog, đặt `use_syslog = true` trong phần `[DEFAULT]`.
- Keystone sử dụng module Python logging, cho phép cấu hình rất linh hoạt về mức độ log (DEBUG, INFO, WARNING...) và định dạng output.
- Có file mẫu: `etc/logging.conf.sample` trong source code Keystone.

### 4. Ba kiểu Formatter (định dạng log)
Formatter là phần quyết định mỗi dòng log sẽ hiển thị những thông tin gì.

#### 4.1 formatter_minimal
```ini
iniformat=%(message)s
```
- Ý nghĩa: Chỉ ghi nội dung thông báo (message) thuần túy.
- Không có thời gian, không có level (INFO/ERROR), không có tên module.
- Dùng khi bạn muốn log rất gọn, sạch (thường ít dùng trong production).

#### 4.2 formatter_normal
```ini
iniformat=(%(name)s): %(asctime)s %(levelname)s %(message)s
```
- Ý nghĩa: Định dạng thông thường, dễ đọc nhất.
- Giải thích các trường:
  - `%(name)s`        → Tên logger (thường là `keystone`, `keystone.api`, `keystone.middleware`...)
- `%(asctime)s`     → Thời gian xảy ra (ví dụ: 2026-04-15 15:30:45,123)
- `%(levelname)s`   → Mức độ log: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `%(message)s`     → Nội dung thông báo chính

Đây là formatter được dùng nhiều nhất khi chạy ở mức INFO hoặc WARNING.

#### 4.3 formatter_debug
```ini
iniformat=(%(name)s): %(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s
```
- Ý nghĩa: Định dạng chi tiết debug, dùng khi cần troubleshoot sâu.
- Thêm các trường so với normal:
  - `%(module)s`     → Tên file Python (ví dụ: controllers.py, core.py)
  - `%(funcName)s`   → Tên hàm đang chạy (ví dụ: authenticate, validate_token)

Khi bật debug (`level=DEBUG`), người ta thường chuyển sang dùng formatter_debug để biết chính xác lỗi xảy ra ở đâu trong code.


### 5. Cấu trúc tổng quát của file `/etc/keystone/logging.conf`

File thường có các phần chính sau:

- `[formatters]`
Khai báo tên các formatter (minimal, normal, debug...)
- `[handlers]`
Khai báo nơi ghi log (handler). Ví dụ phổ biến:
  - `handler_file` → Ghi vào file `/var/log/keystone/keystone.log` (thường dùng `WatchedFileHandler` hoặc `RotatingFileHandler`)

- Có thể có handler_console (ghi ra màn hình)

- `[loggers]`
Cấu hình mức log cho từng logger cụ thể (keystone, keystone.api, oslo_db, sqlalchemy...).
- `[logger_root]`
Logger gốc (root logger) – quyết định mức log mặc định cho toàn bộ Keystone.

Ví dụ cấu hình điển hình (phần quan trọng):
```ini
ini[formatters]
keys=minimal, normal, debug

[formatter_minimal]
format=%(message)s

[formatter_normal]
format=(%(name)s): %(asctime)s %(levelname)s %(message)s

[formatter_debug]
format=(%(name)s): %(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s

[handlers]
keys=console, file

[handler_file]
class=handlers.WatchedFileHandler
level=INFO
formatter=normal
args=('/var/log/keystone/keystone.log', 'a')

[logger_root]
level=INFO
handlers=file
```