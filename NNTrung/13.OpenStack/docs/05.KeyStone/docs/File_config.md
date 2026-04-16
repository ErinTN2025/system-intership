# File config của Keystone

File cấu hình chính của Keystone:  
`/etc/keystone/keystone.conf`

### 1. Cấu trúc file config

- OpenStack sử dụng định dạng **INI file** (text đơn giản).
- Nội dung được chia thành các section (nhóm), ví dụ: `[DEFAULT]`, `[database]`,`[token]`, `[auth]`…
- Trong mỗi section có nhiều dòng kiểu: `tùy_chọn = giá_trị`(`key=value`)

Ví dụ:
```ini
[DEFAULT]
debug = false
list_limit = 500

[database]
connection = mysql+pymysql://keystone:matkhau@10.0.0.11/keystone
```

Các options có thể có các giá trị khác nhau, dưới đây là các loại thường được sử dụng bởi OpenStack:
- **boolean**: `true` / `false` (dùng cho tính năng bật/tắt)
- **integer**: số nguyên (ví dụ: `64`)
- **float**: số thực (ví dụ: `0.25`)
- **list**: danh sách cách nhau bởi dấu phẩy (ví dụ: `password,token,application_credential`)
- **multi-valued**: có thể khai báo nhiều dòng cùng key
- **string**: chuỗi ký tự (có thể dùng dấu nháy đơn `''` hoặc kép `""` nếu chứa khoảng trắng): `password = 'My Secret Pass'`

**Variable substitution (thay thế biến):**
- Dùng `$tên_biến` để tham chiếu giá trị đã định nghĩa trước đó.  
  Ví dụ: 
```bash
rabbit_host = controller`  
# rabbit_hosts = $rabbit_host:$rabbit_port
transport_url = rabbit://$rabbit_host:5672/
# Để dùng literal `$`, viết `$$`.
ldap_dns_password = $$xkj432
```

**Khoảng trắng trong value:** Dùng dấu nháy đơn:  
`ldap_dns_password = 'password with spaces'`

**Lưu ý quan trọng:**
- Hầu hết service load file `/etc/keystone/keystone.conf` tự động.
- Để chỉ định file khác: dùng `--config-file /path/to/keystone.conf` khi chạy lệnh hoặc start service.
- Sau khi chỉnh sửa, restart Keystone (thường qua systemd: `systemctl restart httpd` hoặc `keystone-wsgi`).

### 2. Các section quan trọng và tùy chọn phổ biến - API configuration options

Dưới đây là các section hay dùng nhất và các tùy chọn quan trọng (đã cập nhật theo docs mới nhất). Tôi ưu tiên những tùy chọn thực tế cần chỉnh.

#### **[DEFAULT]**
| Option                        | Type      | Mô tả & Giá trị khuyến nghị |
|-------------------------------|-----------|-----------------------------|
| `debug`                       | boolean   | `False` (bật `True` chỉ khi debug) |
| `insecure_debug`              | boolean   | `False` (bật chỉ khi cần chi tiết lỗi – không an toàn) |
| `admin_token`                 | string    | **Không nên dùng**. Dùng `keystone-manage bootstrap` thay thế. Không nên sử dụng giá trị này. Giá trị của tùy chọn này là một đoạn mã dùng để khởi động Keystone thông qua API. Token này không được hiểu là user và nó có thể vượt qua hầu hết các phần check ủy quyền. |
| `public_endpoint`             | URI       | URL Endpoint cơ sở của Keystone cho Client. Chỉ nên set option này trong trường hợp giá trị của base URL chứa đường dẫn mà Keystone không thể tự suy luận hoặc endpoint ở server khác |
| `max_project_tree_depth`      | integer   | `5` Số lượng tối đa của cây project. Lưu ý: đặt giá trị cao có thể ảnh hưởng đến hiệu suất. |
| `list_limit`                  | integer   | `None` hoặc `500` (giới hạn số item trả về trong list) Số lượng entities lớn nhất có thể được trả lại trong một collection. Với những hệ thống lớn nên set option này để tránh những câu lệnh hiển thị danh sách users, projects cho ra quá nhiều dữ liệu không cần thiết |
| `max_db_limit`                | integer   | `1000` (giới hạn query DB) |
| `strict_password_check`       | boolean   | `False` (nếu `True` Nếu được set thành true, Keystone sẽ kiểm soát nghiêm ngặt thao tác với mật khẩu, nếu mật khẩu quá chiều dài tối đa, nó sẽ không được chấp nhận. Còn đặt False thì mật khẩu sẽ tự động bị cắt ngắn đến độ dài tối đa |
| `notification_format`         | string    | `cadf` (khuyến nghị cho audit) |
| `executor_thread_pool_size`   | integer   | `64` |
|`max_param_size = 64 ` | integer | Giới hạn kích thước của ID/names|
|`max_token_size = 255`| integer | Giới hạn kích thước Token. MẶc định là 255 dành cho Fernet token |

#### **[database]**
| Option                  | Type   | Mô tả |
|-------------------------|--------|-------|
| `connection`            | string | Chuỗi kết nối DB (ví dụ: `mysql+pymysql://keystone:pass@controller/keystone`) – **bắt buộc** |
| `max_pool_size`         | integer| Số kết nối tối đa |
| `max_overflow`          | integer| Số kết nối dự phòng |

#### **[assignment]**
| Option                     | Type | Mô tả |
|----------------------------|------|-------|
| `driver= sql`                   | string |  Trình điểu khiển phụ trợ (nơi lưu trữ phân công vài trò) trong Keystone assignment |
| `prohibited_implied_role`  | list | `['admin']` (danh sách các role bị cấm trở thành implied role) |

#### **[auth]**
**[auth]**
|Option|Type|Mô tả|
|------|----|-----|
|`external = <None>`|string|Điểm vào cho auth plugin module, mặc định sẽ là Default Domain|
|`methods = external,password,token,oauth1,mapped,application_credential`|list|Các phương thức xác thực được phép sử dụng|
|`oauth1 = <None>`|string|Điểm vào cho oAuth 1.0 auth plugin module|
|`password = <None>`|string|Điểm vào cho module xác thực mật khẩu|
|`token = <None>`|string|Điểm vào cho module xác thực bằng token|

#### **[catalog]**
| Option          | Type    | Mô tả |
|-----------------|---------|-------|
| `driver`        | string  | `sql` (khuyến nghị) hoặc `template` |
| `caching`       | boolean | `True` |
| `cache_time`    | integer | Thời gian cache catalog (giây) |

#### **[token]**
| Option               | Type    | Mô tả & Khuyến nghị |
|----------------------|---------|---------------------|
| `provider`           | string  | `fernet` (mặc định và khuyến nghị) hoặc `jws` |
| `expiration`         | integer | `3600` (1 giờ – giá trị phổ biến) |
| `allow_expired`      | boolean | `False` |

#### **[fernet_tokens]** (rất quan trọng)
| Option               | Type    | Mô tả |
|----------------------|---------|-------|
| `key_repository`     | string  | `/etc/keystone/fernet-keys` (thư mục lưu khóa) |
| `max_active_keys`    | integer | `5` (số khóa active tối đa) |

**Lưu ý:** Sau khi thay đổi, chạy `keystone-manage fernet_setup` và `keystone-manage fernet_rotate` định kỳ.

#### **[application_credential]**
| Option       | Type    | Mô tả |
|--------------|---------|-------|
| `driver`     | string  | `sql` |
| `user_limit` | integer | `-1` Không giới hạn số application credential mỗi user (hoặc đặt số cụ thể). |

#### **[resource]**
| Option                        | Type   | Mô tả |
|-------------------------------|--------|-------|
| `domain_name_url_safe`        | string | `off` / `new` / `strict` (khuyến nghị `strict` cho production: Bảo mật hơn (không cho phép tên domain có ký tự lạ).) |
| `project_name_url_safe`       | string | Tương tự |
| `admin_project_domain_name`   | string | Tên domain chứa admin project |

#### **[cache]** (Global caching)
| Option          | Type    | Mô tả |
|-----------------|---------|-------|
| `enabled`       | boolean | `True` (bật caching toàn cục để Keystone chạy nhanh hơn.) |
| `backend`       | string  | `dogpile.cache.memcached` hoặc `oslo_cache.memcache_pool` |
| `expiration_time` | integer | `600` (10 phút) |

#### **[oslo_middleware]**
| Option                    | Type    | Mô tả |
|---------------------------|---------|-------|
| `max_request_body_size`   | integer | `114688` (bytes) |


### Xem thêm (tài liệu chính thức mới nhất)
- https://docs.openstack.org/keystone/latest/configuration/config-options.html
- https://docs.openstack.org/keystone/2026.1/configuration/ (nếu có)
- Sample config: `/usr/share/keystone/keystone.conf.sample` trên server Keystone.

### 3. Domain-specific configuration
Đây là tính năng quan trọng của Keystone (từ phiên bản Kilo/Liberty trở đi).

Mục đích: Cho phép mỗi Domain có backend riêng (thường là LDAP hoặc SQL). Mặc định tính năng này bị tắt.

Có 2 cách lưu cấu hình domain-specific:

**Cách 1:**
- Trong `/etc/keystone/keystone.conf`, thêm:
```ini
[identity]
domain_specific_drivers_enabled = True
domain_config_dir = /etc/keystone/domains
```
- Keystone sẽ tìm file có tên `keystone.TÊN_DOMAIN.conf` trong thư mục đó
- Domain nào không có file riêng sẽ dùng cấu hình mặc định từ file chính (`keystone.conf`).

**Cách 2:**
- Lưu cấu hình vào SQL database (qua API)
```ini
[identity]
domain_specific_drivers_enabled = True
domain_configurations_from_database = True
```
- Ưu điểm: Không cần restart Keystone khi thay đổi cấu hình, thay đổi qua REST API (v3).
- Nhược điểm: Có cache, nên thay đổi có thể không áp dụng ngay (có thể chờ cache timeout).
- Để migrate từ file sang database: dùng lệnh `keystone-manage domain_config_upload --all.`

### 4. Identity Mapping (Bảng ánh xạ Identity)
- Keystone tự động tạo bảng ánh xạ (identity mapping) để:
  - Đảm bảo User ID và Group ID duy nhất toàn hệ thống.
  - Cho phép Keystone biết domain và backend nào từ chỉ 1 public ID.

- Public ID được sinh ra tự động (mặc định dùng sha256).
- Với LDAP, tên user/group giới hạn 255 ký tự.

Nếu LDAP là read-only (quản lý ngoài Keystone), bảng mapping có thể chứa dữ liệu cũ → dùng lệnh `keystone-manage mapping_purge` để dọn dẹp.

Sau khi cấu hình LDAP hoặc purge mapping, nên chạy:
```bash
keystone-manage mapping_populate --domain DOMAIN_NAME
```
để tránh timeout khi list users lần đầu.

### 5. Integrate Identity với LDAP (kết nối Keystone với LDAP / Active Directory)

Keystone hỗ trợ dùng LDAP làm backend cho authentication và authorization (chỉ read-only)

- Nếu dùng RHEL/CentOS (có SELinux): `setsebool -P authlogin_nsswitch_use_ldap on`
- Cấu hình cơ bản:
```bash
sudo nano /etc/keystone/keystone.conf
```
- Phần `[ldap]`:
  - `url = ldap://...`
  - `user`, `password`, `suffix` (base DN)
  - Có thể chỉ nhiều server LDAP (cách nhau dấu phẩy) + randomize_urls.

**Tùy chọn quan trọng khác**:
- Query scope, page_size, alias_dereferencing...
- Connection pooling (use_pool, pool_size...) để tăng hiệu suất.
- Connection pool riêng cho user authentication `(use_auth_pool)`.

**Cấu hình Identity backend với LDAP**:
- Cách 1: Toàn hệ thống dùng LDAP (không khuyến khích cho production lớn):
```ini
[identity]
driver = ldap
```
- Cách 2: Dùng domain-specific 
  - Bật domain-specific drivers.
  - Tạo file `/etc/keystone/domains/keystone.TÊN_DOMAIN.conf` với phần `[identity] driver = ldap` và cấu hình `[ldap]`.

**Attribute mapping**:
- `user_id_attribute`, `user_name_attribute`, `user_mail_attribute`...
- Hỗ trợ Active Directory (userAccountControl, user_enabled_mask...).
- Hỗ trợ enabled emulation nếu LDAP không có thuộc tính enabled.

**Bảo mật kết nối LDAP**:
- Bật TLS (`use_tls = True`, `tls_cacertfile = ...`, `tls_req_cert = demand/allow/never`).

### 6. Caching layer (Lớp Cache)
Keystone hỗ trợ cache để tăng tốc độ (đặc biệt token validation).

- Cấu hình trong phần `[cache]`.
- Phải bật `enabled = True` thì mới cache.
- Mỗi subsystem (token, role, resource, domain_config...) có thể bật/tắt cache riêng.
- Backend phổ biến: memcached, redis, dbm, memory (chỉ test),...

Token caching: Rất quan trọng, đặc biệt với Fernet tokens. Có tùy chọn `token_cache_time`, `revocation_cache_time`.

Lưu ý: Cache có thể gây ra dữ liệu cũ (stale data) nếu backend là read-only (như LDAP).
### 7. Security compliance and PCI-DSS
Các tính năng bảo mật bổ sung (từ phiên bản Newton) để đáp ứng chuẩn PCI-DSS:

- **Account lockout**: Khóa tài khoản sau N lần sai password (`lockout_failure_attempts`, `lockout_duration`).
- **Disable inactive users**: Tự động disable user không login trong X ngày (`disable_user_account_days_inactive`).
- **Force change password first use**: Buộc đổi password lần đầu hoặc sau khi admin reset (`change_password_upon_first_use`).
- **Password expiration**: Password hết hạn sau X ngày (`password_expires_days`).
- **Password strength**: Dùng regex để buộc password mạnh (`password_regex + mô tả`).
- **Password history**: Không cho dùng lại N password cũ (`unique_last_password_count`).
- **Minimum password age**: Không cho đổi password quá thường xuyên.
- Có thể exempt một số user (service account, admin...) khỏi các quy tắc này.

Lưu ý: Các tính năng này chủ yếu áp dụng cho SQL backend, không phải LDAP.
### 8.Performance and Scaling (Hiệu suất & Mở rộng)
Keystone là ứng dụng web 2 tầng, scale ngang dễ dàng (thêm process, memory, load balancer).

Các tùy chọn ảnh hưởng hiệu suất:

- Giảm `max_project_tree_depth`, `max_password_length`.
- Bật cache.
- Chọn token provider (Fernet khuyến nghị + cache).
- Cấu hình keystonemiddleware (auth_token) ở các service khác (Nova, Cinder...): memcached_servers, token_cache_time, include_service_catalog = False...

### 9.Các tính năng khác
- **URL safe naming**: Kiểm tra tên project/domain không chứa ký tự đặc biệt (off / new / strict).
- **Limiting list return size:** Giới hạn số lượng kết quả trả về khi list (tránh overload).
- **Endpoint Filtering:** Tạo catalog động theo project.
- **Endpoint Policy:** Liên kết policy với endpoint cụ thể.