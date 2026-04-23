# Tổng quan về Keystone
Môi trường cloud theo mô hình dịch vụ Infrastructure-as-a-Service layer (IaaS) cung cấp cho người dùng khả năng truy cập vào các tài nguyên quan trọng ví dụ như máy ảo, kho lưu trữ và kết nối mạng. Bảo mật vẫn luôn là vấn đề quan trọng đối với mọi môi trường cloud và trong OpenStack thì keystone chính là dịch vụ đảm nhiệm công việc ấy. Nó sẽ chịu trách nhiệm cung cấp các kết nối mang tính bảo mật cao tới các nguồn tài nguyên cloud.

## 1. Tổng quan
**Keystone** là thành phần quản lý xác thực và ủy quyền (Identity & Access Management) của OpenStack. Keystone có thể tự lưu user hoặc đứng giữa đóng vai trò như một cái cổng (Shim) đứng trước các hệ thống có sẵn (như LDAP).

**Keystone** làm 3 việc chính:
- Xác thực (Authentication): 
  - Khi bạn đăng nhập (authenticate):
  - Kiểm tra: Keystone dùng **Identity service** để kiểm tra username + password của bạn, có thể tự check hoặc hổi LDAP
- Cấp Token: 
  - Nếu login đúng -> **Token service** tạo ra một cái token (giấy phép) và trả về cho bạn, sau đó user không cần login lại, chỉ dùng token.
  - Sau này, mỗi lần bạn gọi API, bạn đưa token này cho Keystone kiểm tra.
- Phân quyền (Authorization):
  - Xác định user được làm gì, trên project nào.

Ví dụ:
- LDAP(Database thật sự): Chỉ biết user này đúng password hay không.
- Keystone biết user này là ai, thuộc project nào, có role gì, được gọi API nào, cấp token để dùng tiếp.

## 2. Thành phần cốt lõi của KeyStone
### 2.1 Identity 
- Dịch vụ Định danh (Identity Service) cung cấp chức năng xác thực thông tin đăng nhập và quản lý dữ liệu về người dùng cũng như các nhóm người dùng. 
- Trong các cấu hình cơ bản, dữ liệu này được quản lý trực tiếp bởi dịch vụ Định danh, cho phép hệ thống thực hiện toàn bộ các thao tác CRUD (Create,Read,Update,Delete) liên quan. 
- Trong những trường hợp phức tạp hơn, dữ liệu sẽ được quản lý bởi một dịch vụ nền tảng có thẩm quyền (authoritative backend service). Ví dụ điển hình là khi dịch vụ Định danh đóng vai trò giao diện frontend cho giao thức LDAP. Trong kịch bản đó, máy chủ LDAP được coi là nguồn dữ liệu gốc (source of truth) và vai trò của dịch vụ Định danh là chuyển tiếp thông tin một cách chính xác.

- Identity Service trong keystone cung cấp các Actors. Nó có thể tới từ nhiều dịch vụ khác nhau như SQL, LDAP, và Federated Identity Providers.
#### 2.4 LDAP
- Keystone có tùy chọn cho phép lưu trữ actors trong Lightweight Directory Access Protocol (LDAP).
- Keystone sẽ truy cập LDAP như các ứng dụng khác (System Login, Email, Web Application, etc.).
- Thiết lập kết nối sẽ được lưu trong file config của keystone. Các cài đặt bao gồm tùy chọn cho phép keystone được ghi hoặc chỉ đọc dữ liệu từ LDAP.
- Thông thường LDAP chỉ cho phép các câu lệnh đọc (ví dụ như tìm kiếm user, group và xác thực).
- Nếu sử dụng LDAP như một read-only Identity Backends thì Keystone cần có quyền sử dụng LDAP
### 2.2 Users
- Đại diện cho một người (hoặc một ứng dụng) dùng API trong OpenStack (Users represent an individual API consumer.)
- Mỗi User phải thuộc về 1 Domain
- Tên User không cần phải unique toàn hệ thống, nhưng bắt buộc unique trong domain của nó.
### 2.3 Groups
- Là một nhóm chứa nhiều Users
- Cũng phải thuộc về 1 domain
- Tên group chỉ unique trong domain của nó.
- Users và User Groups gọi là actor

### 2.4 Resource Service
Quản lý 2 thứ chính là Projects và Domains
#### 2.4.1 Projects

![altimage](../images/Screenshot_1.png)

- Đây là đơn vị sở hữu cơ bản nhất trong OpenStack
- Mọi thứ người dùng tạo ra (VM, volume, network, image,...) đều thuộc về một project.
- Trong keystone, Project được dùng bởi các service của OPS để nhóm và cô lập các nguồn tài nguyên. Nó có thể hiểu là 1 nhóm các tài nguyên mà chỉ có một số các user mới có thể truy cập và hoàn toàn tách biệt với các nhóm khác.
- Mục đích cơ bản nhất của Keystone chính là nơi để đăng ký cho các projects và xác định ai được phép truy cập project đó.
- Bản thân projects không sở hữu users hay groups mà users và groups được cấp quyền truy cập tới project sử dụng cơ chế gán role.
- Project cũng phải thuộc về một Domain
- Tên project chỉ unique trong domain của nó.
- Nếu không chỉ định domain khi tạo project → nó sẽ thuộc Default domain.
#### 2.4.2 Domains 

![altimage](../images/Screenshot_2.png)

- Là container cấp cao nhất
- Domain được dùng để cô lập danh sách các Projects và Users.
- Dùng để chứa Users, Groups và Projects
- Domain được định nghĩa là một tập hợp các users, groups, và projects. Nó cho phép người dùng chia nguồn tài nguyên cho từng tổ chức sử dụng mà không phải lo xung đột hay nhầm lẫn.
- Mỗi Domain có tên toàn cục unique (không domain nào được trùng tên).
- Keystone luôn có sẵn một domain mặc định tên là "Default"
- Dùng để phân chia quản lý
- Người dùng ở domain này vẫn có thể truy cập resource ở domain khác nếu được cấp quyền (assignment).

**Tóm tắt tính Unique trong Identity v3 API**
 
| Attributes | Unique |
|-------------|------------------------------------|
| Domain Name | Globally unique across all domains|
| Role Name | Unique within the owning domain |
| User Name | Unique within the owning domain |
| Project Name | Unique within the owning domain |
| Group Name |  Unique within the owning domain |

### 2.5 Assignment Service
Quản lý Roles và Role Assignments

#### 2.5.1 Roles
- Quy định bạn được làm gì 
- Role có thể gán ở mức Domain hoặc Project
- Role có thể gán cho User hoặc Group
- Tên Role chỉ unique trong domain của nó.
- Roles được dùng để hiện thực hóa việc cấp phép trong keystone. Một actor có thể có nhiều roles đối với từng project khác nhau.
- Role được gán cho user và trên một project cụ thể ("assigned to" user, "assigned on" project)

![altimage](../images/Screenshot_3.png)

#### 2.5.2 Assignment
- Gồm bộ 3 (3-tuple) gồm: Role (vai trò gì), Resource (gán cho Project hay Domain nào), Identity (gán cho User hay Group nào)
- Role assignment được cấp phát, thu hồi, và có thể được kế thừa giữa các users, groups, project và domains.

### 2.6 Token Service
- Để user truy cập bất cứ OpenStack API nào thì user cần chúng minh họ là ai và họ được phép gọi tới API. Để làm được điều này, họ cần có token và "dán" chúng vào "API call". Token Service chính là service chịu trách nhiệm tạo ra tokens.
- Sau khi Identity kiểm tra username/password thành công, Token service sẽ tạo token. Token cũng chứa các thông tin ủy quyền của user trên cloud.
- Token có cả phần ID và payload. ID được dùng để đảm bảo rằng nó là duy nhất trên mỗi cloud và payload chứa thông tin của user.
- Token dùng để xác thực mọi request sau này (không cần gửi password nữa).
- Token service cũng chịu trách nhiệm kiểm tra token có hợp lệ không.

### 2.7 Catalog Service
- Giống như “danh bạ” của toàn bộ OpenStack.
- Lưu trữ thông tin tất cả các URLs và endpoint (địa chỉ API) của các dịch vụ (Nova, Neutron, Glance…).
- Khi bạn có token, bạn có thể hỏi Catalog để biết “muốn tạo máy ảo thì gọi địa chỉ nào”.
- Nếu không có Catalog, users và các ứng dụng sẽ không thể biết được nơi cần chuyển yêu cầu để tạo máy ảo hoặc lưu dữ liệu.
- Service này được chia nhỏ thành danh sách các endpoints và mỗi một endpoint sẽ chứa admin URL, internal URL, and public URL.

### Tips dễ nhớ
- `Identity`: Kiểm tra CMND (user/group) và xác thực bạn là ai.
- `Resource`: Quản lý “căn hộ” (Project) và “tòa nhà” (Domain).
- `Assignment`: Phát “thẻ ra vào” (Role) cho từng người hoặc nhóm.
- `Token`: In ra thẻ từ (token) sau khi kiểm tra xong.
- `Catalog`: Cho bạn biết “cửa vào các phòng” (endpoint) ở đâu.

## 3. Application Construction
Keystone là HTTP front-end cho nhiều dịch vụ xác thực và phân quyền. Từ phiên bản Rocky, Keystone sử dụng Flask-RESTful làm framework để cung cấp REST API.

Hiểu đơn giản là client (CLI, Horizon, service khác) gọi HTTP API. Keystone sẽ xử lý request và trả response.

Luồng sẽ là Client -> API -> Resource -> Manager -> Driver
```bash
┌────────────────────────────────────────┐
│ 1. API Layer (Flask-RESTful)           │
│    - Định nghĩa route, xử lý HTTP      │
│    - Không chứa logic nghiệp vụ        │
└────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────┐
│ 2. Manager Layer (Thin Wrapper)        │
│    - Điều phối gọi driver              │
│    - Xử lý cache, validation cơ bản    │
└────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────┐
│ 3. Driver Layer (Pluggable Backend)    │
│    - Implement thực tế: SQL, LDAP...   │
│    - Có thể không hỗ trợ CRUD          │
└────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────┐
│ 4. Policy & Auth Plugins               │
│    - Kiểm soát "ai được làm gì"        │
│    - Hỗ trợ nhiều phương thức login    │
└────────────────────────────────────────┘
```

  - **API**: Là nơi nhận request, nó nhìn vào URL, Http method và quyết định gọi Resources nào xử lý. Giống kiểu router. Ví dụ:
    - `/v3/users` -> UserResource
    - `/v3/projects` -> ProjectResource
  - **Resource**: Là xử lý thực thi logic cho từng endpoint API, viết login cho GET, POST, DELETE,.. Có thể hiểu Resource bằng controller trong web.
  - **Manager**: Là người điều phối ở giữa (lớp bọc mỏng), gọi xuống backend driver. Vai trò tách logic API khỏi logic lưu trữ.
  - **Driver**: Là người trực tiếp đi lấy dữ liệu (trong DB hoặc LDAP).

- Tính module hóa: Mỗi dịch vụ (Identity, Catalog, Resource...) là một module riêng biệt. Bạn có thể thay đổi cách hoạt động của dịch vụ này mà không làm hỏng dịch vụ kia.
- Keystone tách biệt rõ ràng giữa giao diện API (Flask) và logic nghiệp vụ (Driver), giúp dễ dàng thay đổi backend mà không ảnh hưởng đến API.

VÍ DỤ: 
```bash
 API = nhân viên phục vụ (waiter)

Khách vào gọi món:

“Cho tôi phở bò”

 Nhân viên:

nghe yêu cầu
biết gọi bếp nào
 Resource = đầu bếp
Nhận yêu cầu từ nhân viên
trực tiếp nấu món

 Mapping (gắn Resource vào API) là gì?

Món phở bò → giao cho bếp A
Món cơm rang → giao cho bếp B

 Trong Keystone:

/v3/users → UserResource
/v3/projects → ProjectResource
```

Ví dụ: User Resources và User API:
```Java
class UserResource(ks_flask.ResourceBase):
collection_key = 'users'
member_key = 'user'
get_member_from_driver = PROVIDERS.deferred_provider_lookup(
api='identity_api', method='get_user')
def get(self, user_id=None):
"""Get a user resource or list users.
GET/HEAD /v3/users
GET/HEAD /v3/users/{user_id}
"""
...
def post(self):
"""Create a user.
POST /v3/users
"""
...
class UserChangePasswordResource(ks_flask.ResourceBase):
@ks_flask.unenforced_api
def post(self, user_id):
...
```
```Java
class UserAPI(ks_flask.APIBase):
_name = 'users'
_import_name = __name__
resources = [UserResource]
resource_mapping = [
ks_flask.construct_resource_map(
resource=UserChangePasswordResource,
url='/users/<string:user_id>/password',
resource_kwargs={},
rel='user_change_password',
path_vars={'user_id': json_home.Parameters.USER_ID}
),
...
```

**Các nhóm dịch vụ (Service Groups) trong Keystone:**

| Nhóm dịch vụ       | Chức năng chính               | Giải thích                                                                                                                                       | Ví dụ module                 |
| ------------------ | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| **Assignment**     | Quản lý phân quyền (role)     | Xác định **ai (user/group)** có **quyền gì (role)** trên **tài nguyên nào (project/domain)**. Đây là nơi quyết định quyền truy cập thực tế trong hệ thống. | keystone.api.role_assignments, keystone.api.role_inferences, keystone.api.roles, tone.api.os_inherit, keystone.api.system      |
| **Authentication** | Xác thực người dùng           | Kiểm tra thông tin đăng nhập (password, token, …). Nếu đúng → cấp token. Đây là bước đầu tiên khi user truy cập hệ thống.                                  | ystone.api.auth, keystone.api.ec2tokens, keystone.api.s3tokens    |
| **Catalog**        | Quản lý endpoint dịch vụ      | Lưu danh sách các service (Nova, Neutron, …) và URL của chúng để client biết gọi API ở đâu. Giống như “danh bạ dịch vụ”.                                   | eystone.api.endpoints, keystone.api.os_ep_filter, keystone.api.regions, keystone.api.services |
| **Credentials**    | Quản lý thông tin xác thực    | Lưu các loại thông tin xác thực bổ sung như key, certificate… dùng cho các cơ chế auth khác ngoài password.                                                | keystone.api.credentials                 |
| **Federation**     | Liên kết identity bên ngoài   | Cho phép user đăng nhập bằng hệ thống bên ngoài (LDAP, SSO, IdP). Keystone không cần lưu user mà vẫn xác thực được.                                        |  keystone.api.os_federation               |
| **Identity**       | Quản lý user và group         | Quản lý thông tin người dùng và nhóm (tạo, sửa, xóa, truy vấn). Đây là phần “danh tính” của hệ thống.                                                      |keystone.api.groups, keystone.api.user            |
| **Limits**         | Quản lý giới hạn tài nguyên   | Đặt giới hạn (quota) như số VM, network… mà project được phép sử dụng. Giúp kiểm soát tài nguyên.                                                          | keystone.api.registered_limits, keystone.api.limits    |
| **OAuth1**         | Hỗ trợ OAuth 1.0              | Cung cấp cơ chế xác thực bằng OAuth1, thường dùng cho tích hợp API bên ngoài mà không cần password trực tiếp.                                              | keystone.api.os_oauth1                   |
| **Policy**         | Quản lý chính sách phân quyền | Định nghĩa các rule kiểm tra quyền (ai được làm gì). Keystone dùng các rule này để quyết định cho phép hay từ chối hành động.                              |  keystone.api.policy                      |
| **Resource**       | Quản lý domain và project     | Quản lý cấu trúc tài nguyên: domain (cấp cao) và project (cấp dưới). Đây là nơi tổ chức tài nguyên trong OpenStack.                                        |  keystone.api.domains, keystone.api.projects          |
| **Revoke**         | Thu hồi token                 | Quản lý việc vô hiệu hóa token trước khi hết hạn (ví dụ logout hoặc revoke quyền).                                                                         | keystone.api.os_revoke                   |
| **Trust**          | Ủy quyền (delegation)         | Cho phép user A ủy quyền cho user B hành động thay mình trong một phạm vi nhất định (có kiểm soát).                                                        | keystone.api.trusts                       |

- Tham khảo thêm tại: https://docs.openstack.org//keystone/2026.1/doc-keystone.pdf 

### 3.1 Service Backends - Kiến trúc Driver linh hoạt
Keystone cho phép cấu hình backend khác nhau cho từng dịch vụ, phù hợp với nhiều môi trường: SQL, LDAP, NoSQL, hay hệ thống identity bên ngoài.

Mỗi dịch vụ trong Keystone có thể được cấu hình để sử dụng một backend khác nhau, giúp Keystone linh hoạt phù hợp với nhiều môi trường và nhu cầu.

**Cơ chế cấu hình**:

Trong file `keystone.conf`, mỗi dịch vụ có một section với key `driver`:
```ini
[assignment]
driver = sql

[identity]
driver = ldap

[catalog]
driver = templated
```
- Mỗi backend có một abstract base class (lớp cơ sở trừu tượng) để định nghĩa những gì một implementation phải có. Những lớp này nằm trong thư mục backends của từng service, thường là file `base.py`.
- Ví dụ:
```bash
• keystone.assignment.backends.base.AssignmentDriverBase
• keystone.assignment.role_backends.base.RoleDriverBase
• keystone.auth.plugins.base.AuthMethodHandler
• keystone.catalog.backends.base.CatalogDriverBase
• keystone.credential.backends.base.CredentialDriverBase
```
- Khi bạn viết driver mới, người dùng bắt buộc kế thừa từ lớp base tương ứng và implement đầy đủ các method được yêu cầu.
### 3.2 Templated Backend
- Đây là một loại backend đặc biệt, chủ yếu được thiết kế cho trường hợp phổ biến liên quan đến service catalog.
- Templated backend là một catalog backend đơn giản: nó chỉ mở rộng (expand) các template đã cấu hình sẵn để sinh ra dữ liệu catalog.
### 3.3 Data Model
Keystone được thiết kế từ đầu để hỗ trợ nhiều kiểu backend khác nhau. Do đó, nhiều method và kiểu dữ liệu chấp nhận nhiều dữ liệu hơn mức nó biết cách xử lý, và sẽ chuyển tiếp chúng xuống backend.
Có một số kiểu dữ liệu chính:
- `User`: có thông tin xác thực (account credentials), được liên kết với một hoặc nhiều project hoặc domain.
- `Group`: một tập hợp các user, được liên kết với một hoặc nhiều project hoặc domain.
- `Project`: đơn vị sở hữu (unit of ownership) trong OpenStack, chứa một hoặc nhiều user.
- `Domain`: đơn vị sở hữu trong OpenStack, chứa users, groups và projects.
- `Role`: một metadata cấp cao (first-class piece of metadata) được liên kết với nhiều cặp user-project.
- `Token`: credential dùng để xác định, liên kết với một user hoặc với user và project.
- `Extras`: một bucket chứa metadata kiểu key-value, liên kết với cặp user-project.
- `Rule`: mô tả một tập hợp các yêu cầu để thực hiện một hành động.

Mặc dù mô hình dữ liệu tổng quát cho phép mối quan hệ many-to-many giữa users/groups với projects/domains, nhưng các implementation backend thực tế sẽ tận dụng mức độ khác nhau của tính năng này.

Ví dụ: LDAP backend có thể chỉ hỗ trợ User-Project, không hỗ trợ Group.

### 3.4 Approach to CRUD
Mặc dù trong các deployment thực tế lớn, người ta thường quản lý users và groups trong hệ thống người dùng hiện có (existing user systems), Keystone vẫn cung cấp nhiều thao tác CRUD (Create, Read, Update, Delete) để phục vụ cho mục đích phát triển và testing.

CRUD được coi là một extension (phần mở rộng) hoặc tính năng bổ sung, chứ không phải là tính năng cốt lõi. Do đó, một backend không bắt buộc phải hỗ trợ CRUD.

Nếu backend của một service không hỗ trợ các thao tác CRUD, nó sẽ raise exception: keystone.exception.NotImplemented.

Doanh nghiệp lớn thường quản lý user qua hệ thống bên ngoài (Active Directory, LDAP...)

Keystone không nên "ép" backend phải hỗ trợ viết/xóa user nếu hệ thống gốc không cho phép

Giúp Keystone linh hoạt tích hợp với mọi môi trường identity. Backend chỉ cần hỗ trợ read là có thể dùng được trong nhiều trường hợp.

### 3.5 Approach to Authorization (Cơ chế phân quyền)
Kiểm soát xem ai được làm gì, dựa trên thông tin xác thực của người dùng.

Hai cấp độ kiểm tra cơ bản trong Keystone:
- Admin check: Người dùng có phải admin không?
- Owner check: Người dùng có phải là chủ thể của tài nguyên không?

Các hệ thống khác muốn dùng policy engine của Keystone có thể cần thêm nhiều kiểu kiểm tra và có thể viết hoàn toàn backend policy tùy chỉnh.

Mặc định, Keystone sử dụng cơ chế policy enforcement từ thư viện oslo.policy.

Quy tắc: 
- Với một danh sách các điều kiện cần kiểm tra, chỉ cần verify rằng credentials chứa các matches đó.
```bash
credentials = {'user_id': 'foo', 'is_admin': 1, 'roles': ['nova:netadmin']}

# Admin only call:
policy_api.enforce(('is_admin:1',), credentials)

# Admin or owner call:
policy_api.enforce(('is_admin:1', 'user_id:foo'), credentials)

# Netadmin call:
policy_api.enforce(('roles:nova:netadmin',), credentials)
```
- Credentials thường được xây dựng từ metadata của user trong phần extras của Identity API. 
- Việc thêm role cho user chỉ đơn giản là thêm role vào metadata của user.
- Capability RBAC: Thay vì kiểm tra "ai là admin", hệ thống có thể kiểm tra "ai có capability thực hiện hành động X" (Hiện tại chưa có)

### 3.6 Approach to Authentication (Cơ chế xác thực)
Keystone cung cấp nhiều authentication plugins kế thừa từ
`keystone.auth.plugins.base`
- Danh sách các plugin có sẵn:
  - keystone.auth.plugins.external.Base
  - keystone.auth.plugins.mapped.Mapped
  - keystone.auth.plugins.oauth1.OAuth
  - keystone.auth.plugins.password.Password
  - keystone.auth.plugins.token.Token
keystone.auth.plugins.totp.TOTP

| Plugin | Phương thức| Use case |
|----------|--------------------|-----------------|
| password | Username + password | Đăng nhập cơ bản |
| token | Dùng token có sẵn | Service-to-service auth |
| oauth1 | OAuth 1.0| Ứng dụng bên thứ 3 |
| totp | Time-based OTP | 2FA |
| mapped | Ánh xạ từ external IDP | Federation (SAML, OIDC) |
| external| Auth qua web server (REMOTE_USER)| Reverse proxy auth|

**Scope(Phạm vi)**:
- Trong authentication request: Phần POST data chỉ định tài nguyên người dùng muốn truy cập.
- Khi nói về token: Scope chỉ phạm vi hiệu lực của token.
  - Project-scoped token: chỉ dùng được trên project đã được grant.
  - Domain-scoped token: dùng để thực hiện các chức năng liên quan đến domain.
  - System-scoped token: chỉ dùng để tương tác với các API ảnh hưởng đến toàn bộ deployment.
- Trong user/group/project: Scope thường chỉ domain mà entity đó thuộc về (ví dụ: một user trong domain X thì scoped to domain X).