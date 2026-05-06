# Keystone Command
## 1. Các lệnh quản lý cốt lõi (Core Identity)
Chạy `openstack --help` để xem tất cả, hoặc `openstack identity --help` để xem nhóm Identity.
### 1.1 Domain
```bash
openstack domain create [--description <desc>] [--enable|--disable] <name>
```
```bash
openstack domain delete <domain>
```
```bash
openstack domain list [--name <name>]
```
```bash
openstack domain set [--name <new-name>] [--description <desc>] [--enable|--disable] <domain>
```
```bash
openstack domain show <domain>
```
### 1.2 Project
```bash
openstack project create [--domain <domain>] [--description <desc>] [--enable|--disable] <name>
```
```bash
openstack project delete <project>
```
```bash
openstack project set [--name <new-name>] [--description <desc>] [--enable|--disable] <project>
```
```bash
openstack project show <project>
```
### 1.3 User
```bash
openstack user create [--domain <domain>] [--project <project>] [--password <pass>] [--email <email>] [--enable|--disable] <name>
```
```bash
openstack user delete <user>
```
```bash
openstack user list [--domain <domain>] [--name <name>]
```
```bash
openstack user set [--name <new-name>] [--email <email>] [--password <pass>] [--enable|--disable] <user>
```
```bash
openstack user show <user>
```
### 1.4 Group
```bash
openstack group create [--domain <domain>] [--description <desc>] <name>
```
```bash
openstack group delete <group>
```
```bash
openstack group list [--domain <domain>]
```
```bash
openstack group set [--name <new-name>] [--description <desc>] <group>
```
```bash
openstack group show <group>
```
```bash
openstack group add user <group> <user>
```
```bash
openstack group remove user <group> <user>
```
```bash
openstack group contains user <group> <user>
```
### 1.5 Role
```bash
openstack role create <name>
```
```bash
openstack role delete <role>
```
```bash
openstack role list
```
```bash
openstack role show <role>
```
```bash
openstack role add --user <user> --project <project> <role> #(gán role cho user trên project)
```
```bash
openstack role add --user <user> --domain <domain> <role>
```
```bash
openstack role add --group <group> --project <project> <role>
```
```bash
openstack role remove --user <user> --project <project> <role>
```
```bash
openstack role assignment list [--user <user>] [--project <project>] [--names]
```
### 1.6 Implied Role (Role ngầm định)
```bash
openstack implied role create <prior-role> --implied-role <implied-role>
```
```bash
openstack implied role list
```
```bash
openstack implied role delete <prior-role> --implied-role <implied-role>
```
## 2. Service Catalog & Endpoint
```bash
openstack service create [--description <desc>] [--enable|--disable] [--type <type>] <name>
```
(Ví dụ: --type identity cho Keystone)
```bash
openstack service delete <service>
```
```bash
openstack service list
```
```bash
openstack service show <service>
```
```bash
openstack endpoint create [--region <region>] <service> public <url>
```
```bash
openstack endpoint create [--region <region>] <service> internal <url>
```
```bash
openstack endpoint create [--region <region>] <service> admin <url>
```
```bash
openstack endpoint list [--region <region>]
```
```bash
openstack endpoint set [--url <new-url>] [--enable|--disable] <endpoint>
```
```bash
openstack endpoint delete <endpoint>
```
```bash
openstack endpoint show <endpoint>
```
```bash
openstack catalog list
```
(xem service catalog của user hiện tại)
## 3. Token & Authentication
```bash
openstack token issue
``` 
Tạo scoped/unscoped token
```bash
openstack token revoke <token>
```
```bash
openstack token show <token>
```
`revoke`: thu hồi, vô hiệu hóa token
## 4. Application Credential 
```bash
openstack application credential create [--description <desc>] [--expiration <YYYY-MM-DD>] [--role <role>] [--unrestricted] <name>
```
```bash
openstack application credential delete <credential-id>
```
```bash
openstack application credential list
```
```bash
openstack application credential show <credential-id>
```
## 5. Federation (Federated Identity - OIDC, SAML, Keystone-to-Keystone)
```bash
openstack identity provider create [--description <desc>] [--remote-id <remote-id>] <name>
```
```bash
openstack identity provider list
```
```bash
openstack identity provider set <idp>
```
```bash
openstack identity provider show <idp>
```
```bash
openstack identity provider delete <idp>
```
```bash
openstack federation protocol create --identity-provider <idp> --mapping <mapping> <protocol>
```
```bash
openstack federation protocol list --identity-provider <idp>
```
```bash
openstack federation protocol show --identity-provider <idp> <protocol>
```
```bash
openstack mapping create <mapping-name> --rules <rules.json>
```
```bash
openstack mapping list
```
```bash
openstack mapping show <mapping>
```
## 6. Các lệnh quản trị Keystone (keystone-manage)
Đây là lệnh chạy trực tiếp trên server Keystone (thường với quyền root hoặc dưới user keystone):

```bash
keystone-manage bootstrap
```
Khởi tạo Keystone lần đầu (tạo admin user, service, endpoint…)
```bash
keystone-manage db_version
```
```bash
keystone-manage db_sync
```
- Thường cần chạy thủ công
```bash
keystone-manage fernet_setup
```
- Tạo kho khóa Fernet lần đầu
```bash
keystone-manage fernet_rotate
```
- Xoay khóa Fernet (nên chạy định kỳ)
```bash
keystone-manage mapping_engine
```
```bash
keystone-manage token_flush
```
- Deprecated, token giờ dùng Fernet/JWS
```bash
keystone-manage credential_setup
```
```bash
keystone-manage credential_migrate
```
```bash
keystone-manage doctor
```
- Kiểm tra vấn đề phổ biến
```bash
keystone-manage --help
```
- Xem đầy đủ
## 7. Các lệnh hữu ích khác
```bash
openstack limit list
```
```bash
openstack registered limit list
```
```bash
openstack registered limit create ...
```
```bash
openstack project quota ...
```
- Một số service dùng