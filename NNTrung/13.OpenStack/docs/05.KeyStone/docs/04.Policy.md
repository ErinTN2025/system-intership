# Policy
## File `policy.yaml`
Trong kiến trúc OpenStack, Keystone là dịch vụ quản lý danh tính (Identity Service) chịu trách nhiệm xác thực (authentication) và ủy quyền (authorization).

Trong kiến trúc OpenStack, Keystone là dịch vụ quản lý danh tính (Identity Service) chịu trách nhiệm xác thực (authentication) và ủy quyền (authorization). Để kiểm soát việc người dùng có thể thực hiện hành động (API calls) nào, OpenStack sử dụng cơ chế Role-Based Access Control (RBAC) dựa trên Policy.

Mỗi dịch vụ trong OpenStack (Keystone, Nova, Neutron, Glance, Cinder…) đều có hệ thống policy riêng. Policy định nghĩa rõ ràng:
  - **Target**: Hành động cụ thể cần kiểm soát (ví dụ: `identity:list_users`, `identity:create_user`).
  - **Rule**: Điều kiện để cho phép hành động đó (thường dựa trên role, scope và các thuộc tính khác).

Từ các phiên bản gần đây, OpenStack áp dụng policy-in-code:
- Các quy tắc policy mặc định được nhúng trực tiếp trong mã nguồn của service.
- Bạn không bắt buộc phải có file `policy.yaml` đầy đủ. Service sẽ tự động sử dụng default rules trong code.
- File `policy.yaml` chỉ dùng để override (ghi đè) những rule bạn muốn thay đổi.
- Ưu điểm: Giảm nguy cơ cấu hình sai, dễ nâng cấp phiên bản, và luôn đồng bộ với code.

JSON policy đã deprecated từ Wallaby (2021) và không còn được khuyến nghị. Tất cả đều dùng định dạng YAML.

Khuyến nghị sử dụng YAML (hỗ trợ comment, dễ đọc và bảo trì hơn).
### Default Roles 
Keystone cung cấp các role mặc định (được tạo tự động qua lệnh `keystone-manage bootstrap`): 
  - **admin**: Quyền quản trị cao nhất( thường kết hợp với `system_scope:all`)
  - **member**: Quyền thao tác thông thường (tạo, sửa, xóa tài nguyên trong project/domain).
  - **reader**: Chỉ quyền đọc (read-only)
  - **service**: Dành cho các dịch vụ OpenStack giao tiếp với nhau (Service-to-service)
  - **manager**: Vai trò quản lý domain (từ 2023.2/Bobcat trở đi).

Các role này có implied roles: `admin` implies `member` implies `reader`
### Scope Enforcement

Policy hiện đại thường kiểm tra cả role và scope:
- `system_scope:all` Quản trị toàn hệ thống
- `domain_scope` Quản trị trong một domain
- `project_scope` Quản trị trong một project

Ví dụ: 
`"role:reader and system_scope:all"` — Chỉ cho phép người dùng có role reader và token có system scope toàn bộ.

### Các tùy chọn quan trọng trong oslo_policy

Để sử dụng RBAC hiện đại và an toàn, khuyến nghị bật hai tùy chọn sau trong file cấu hình của service (ví dụ Trong file cấu hình `/etc/keystone/keystone.conf`):
```init
[oslo_policy]
policy_file = policy.yaml
enforce_scope = true
enforce_new_defaults = true
```
Lưu ý: Khi bật hai tùy chọn này, policy trở nên an toàn và chính xác hơn, nhưng một số hành vi cũ có thể bị từ chối → cần test kỹ trước khi áp dụng production.

### Cách tạo và quản lý file policy.yaml (Generator)
Sinh file policy mẫu (chứa tất cả rule hiện tại): sử dụng lệnh:
```bash
# Đối với Keystone
oslopolicy-policy-generator --namespace keystone --output-file /etc/keystone/policy.yaml

# Tương tự cho các service khác
oslopolicy-policy-generator --namespace nova --output-file /etc/nova/policy.yaml
oslopolicy-policy-generator --namespace neutron --output-file /etc/neutron/policy.yaml
# ...
```
- Lệnh này sẽ sinh ra file YAML dựa trên:
  - Default rules trong code.
  - Các override hiện có (nếu có).

- Lưu ý: Không copy toàn bộ file generator rồi chỉnh sửa (dễ gây xung đột khi upgrade).
- Sử dụng comment trong YAML để giải thích.
- Chỉ ghi đè những rule thực sự cần thay đổi. Ví dụ file `/etc/keystone/policy.yaml`:
```yaml
# Cho phép role 'admin' và 'vpc_admin' liệt kê tất cả users (system scope)
"identity:list_users": "role:admin or (role:reader and system_scope:all) or role:vpc_admin"

# Chỉ cho phép admin tạo user
"identity:create_user": "role:admin and system_scope:all"

# Rule alias (có thể tái sử dụng)
"admin_required": "role:admin and system_scope:all"
"reader_or_owner": "role:reader and system_scope:all or user_id:%(target.user.id)s"
```
Thay đổi trong `policy.yaml` có hiệu lực ngay lập tức (không cần restart service trong hầu hết trường hợp). Tuy nhiên, để an toàn nên restart service hoặc httpd:
```bash
systemctl restart httpd
# hoặc
systemctl restart openstack-keystone
```

Chuyển file `policy.json` cũ, chuyển sang YAML bằng:
```bash
oslopolicy-convert-json-to-yaml --policy-file /etc/keystone/policy.json --output-file /etc/keystone/policy.yaml
```

### Cấu trúc và cách viết rule trong: `policy.yaml`
```yaml
"target_action": "rule_definition"
```
- **target_action**: Tên API cần kiểm soát, ví dụ:
  - `identity:list_users`
  - `identity:create_user`
  - `compute:servers:create`
  - `network:routers:create`
- **rule_definition**: Có thể là:
  - `role:admin` Kiểm tra role
  - `role:reader and system_scope:all`
  - ``user_id:%(target.user.id)s` hoặc `user_id:%(user_id)s`: Người dùng chỉ được thao tác trên chính tài nguyên của mình (owner).
  - `system_scope:all`, `domain_id:%(target.domain_id)s`: Kiểm tra scope.
  - Toán tử logic: `and`, `or,` `not`.
  - `role:admin or role:member`
  - Kết hợp với alias (rule đã định nghĩa trước): `rule:<tên_alias>`
```yaml
"admin_required": "role:admin and system_scope:all"
"reader_or_owner": "role:reader or user_id:%(user_id)s"
"identity:list_users": "rule:admin_required or role:vpc_admin"
```

### Lab thêm quyền list_users cho role tùy chỉnh
- Sinh file policy mẫu
- Thêm/overide một số rule (ví dụ cho role tùy chỉnh `test` hoặc `vpc_admin`).
- Gán role cho user và kiểm tra quyền bằng lệnh `openstack user list`, `openstack role list`, v.v.
- Bật `enforce_scope` và `enforce_new_defaults` sau khi test ổn định.
- Tránh override quá rộng (ví dụ chỉ ghi `"identity:list_users": "role:test"`) vì sẽ làm mất quyền của admin.

Lưu ý khi nâng cấp:
- Luôn kiểm tra release notes của Keystone trước khi upgrade.
- Sử dụng `enforce_new_defaults = true`để chuyển hẳn sang policy hiện đại, tránh cảnh báo deprecated.

- Chỉnh sửa : `etc/keystone/policy.yaml`
```Yaml
"identity:list_users": "role:admin or role:vpc or role:test"
```
- Tạo user và gán role `test` (hoặc `vpc`).
- Test với user đó:
```bash
openstack user list
```