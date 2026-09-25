# Sự cố VM kẹt SHUTOFF sau resize nhầm (boot-from-volume) trên OpenStack Kolla-Ansible — Ghi chép chẩn đoán & khắc phục

> Tài liệu này ghi lại toàn bộ quá trình truy vết một sự cố thực tế: một VM boot-from-volume
> bị resize nhầm rồi kẹt ở trạng thái `error`, sau đó dù đã reset về `active`/`shutoff` vẫn
> **không start lên được**, và **không log nào** ở compute lẫn control. Đọc theo thứ tự để
> hiểu cách lần ngược từ triệu chứng về gốc rễ.
>
> **Spoiler nguyên nhân gốc:** thủ phạm cuối cùng KHÔNG nằm ở Nova mà ở **RabbitMQ bị nghẹt**
> (xem tài liệu "Binding failed for port" đi kèm). VM kẹt chỉ là một biểu hiện khác của cùng
> một bệnh RPC. Phần Nova bên dưới vẫn cần dọn (migration record `error`), nhưng nếu RabbitMQ
> còn nghẹt thì sửa Nova bao nhiêu cũng vô ích.

---

## 1. Triệu chứng ban đầu

- Lỡ tay **resize một VM đang boot-from-volume** (Cinder persistent volume).
- OpenStack hiện warning quen thuộc:

  ```
  The root disk size in flavor will not be applied while booting from a persistent volume.
  ```

- Sau resize, VM kẹt ở `vm_state = error`.
- Đã `nova reset-state --active` / set về `active`, rồi `shutoff`, **nhưng start không lên**.
- **Không có log** rõ ràng ở compute lẫn control — VM như "treo ở đâu đó".

**Quan trọng:** Giống mọi sự cố OpenStack, đây là *triệu chứng*, không phải *bệnh*. "Không
start được + không log" là một mô-típ điển hình của **fail im lặng** — lệnh được nhận nhưng
chết ở một tầng nào đó trước khi kịp ghi log hữu ích.

---

## 2. Hiểu đúng bản chất: vì sao resize boot-from-volume hay gây kẹt

Khi resize một VM boot-from-volume:

1. Nova tạo một **migration record** loại `resize` (kể cả khi nguồn = đích, "resize tại chỗ").
2. Root disk size trong flavor **bị bỏ qua** vì đĩa nằm trên Cinder volume, không phải local
   disk → đây là warning ở mục 1, **bình thường**, không phải lỗi.
3. Nếu bước resize fail giữa chừng → migration record nằm lại ở `status = error` /
   `finished` / `confirming` / `post-migrating`.
4. `nova reset-state --active` chỉ sửa `vm_state` / `power_state` trong bảng `instances`.
   Nó **KHÔNG** đụng tới bảng `migrations`.

> Hệ quả: migration record treo vẫn còn → mỗi lần start, Nova thấy instance đang "giữa chừng
> một resize" → revert lệnh start một cách im lặng. Đây là lý do "start xong vẫn SHUTOFF, không
> log".

### Các nhóm nguyên nhân có thể dẫn tới "VM không start được"

| Nhóm nguyên nhân | Ví dụ cụ thể |
|---|---|
| State Nova kẹt | `task_state` không null, `vm_state = resized/error` |
| **Migration record treo** | dòng `resize`/`live-migration` ở `status = error` còn sót |
| Host/node lệch | `host` ≠ `hypervisor_hostname` sau resize dở |
| Volume kẹt (Cinder) | volume gốc ở `reserved`/`attaching`/`error` → không attach được lúc boot |
| **Mất/chậm RPC (RabbitMQ)** | lệnh start không tới được compute → fail im lặng, **không log compute** |

> Trong sự cố này: state Nova sạch, volume sạch, host khớp — nhưng vẫn fail im lặng. Hai
> thủ phạm thật là **(a) migration record `error` còn sót** và **(b) RabbitMQ nghẹt** ở tầng
> dưới cùng.

---

## 3. Đặc thù khi chạy trên Kolla-Ansible

Mọi service chạy trong **Docker container**, không phải systemd.

### Tên container thường gặp

```bash
# Trên control
docker ps --format '{{.Names}}' | grep -iE 'nova|maria|rabbit'
# nova_api, nova_conductor, nova_scheduler, mariadb, rabbitmq ...

# Trên compute
docker ps --format '{{.Names}}' | grep -iE 'nova|libvirt'
# nova_compute, nova_libvirt, nova_ssh
```

> ⚠️ **Bẫy đã gặp:** lệnh `virsh` PHẢI chạy TRÊN node compute, không phải trên control.
> Trên control sẽ báo `No such container: nova_libvirt`. Ngoài ra nếu copy-paste lệnh từ
> web/chat bị dính ký tự ẩn / xuống dòng, bash báo `-bash: nova_libvirt: No such file or
> directory` (lỗi shell, KHÁC với lỗi docker `No such container`) — khi đó gõ tay lại lệnh.

### Lấy mật khẩu DB (không tự nghĩ ra)

```bash
# Password root MariaDB nằm ở dòng database_password (không có prefix)
grep '^database_password' /etc/kolla/passwords.yml
# Password user nova: dòng nova_database_password
grep 'nova_database_password' /etc/kolla/passwords.yml
```

### Vào nova DB

```bash
# Bằng root
docker exec -it mariadb mysql -u root -p'<database_password>' nova
# Hoặc bằng user nova
docker exec -it mariadb mysql -u nova -p'<nova_database_password>' nova
```

> ⚠️ Nhúng thẳng password sau `-p` (dính liền, có nháy đơn) để tránh trường hợp paste vào
> prompt `Enter password:` bị nuốt ký tự → "access denied" giả.

### KHÔNG sửa config trực tiếp trong container

Mọi tùy chỉnh đặt ở `/etc/kolla/config/...` rồi `kolla-ansible -i <inventory> reconfigure`,
vì redeploy sẽ ghi đè.

---

## 4. Quy trình chẩn đoán VM kẹt — theo đúng thứ tự đã làm

### Bước 1 — Xác định ĐÚNG UUID của VM

> ⚠️ **Bài học xương máu:** đừng nhầm cột. Trong output dạng bảng (ví dụ `nova migration-list`
> hay log), cột đầu có thể là `request_id`/`id` chứ KHÔNG phải instance UUID. Phải xác nhận
> bằng `server show`.

```bash
openstack server show <UUID> -f json
```

Cái nào ra thông tin VM thật (có `name`, `status`, `volumes_attached`) → đó là UUID đúng.
Ghi lại các trường:

- `status`, `OS-EXT-STS:vm_state`, `OS-EXT-STS:task_state`, `OS-EXT-STS:power_state`
- `OS-EXT-SRV-ATTR:host` và `OS-EXT-SRV-ATTR:hypervisor_hostname` (phải khớp nhau)
- `OS-EXT-SRV-ATTR:instance_name` (ví dụ `instance-00000015` — tên domain libvirt)
- `volumes_attached` (lấy volume id để kiểm tra Cinder)

**Kết quả thực tế trong sự cố này:**
```
vm_state    = stopped
task_state  = None          ← state Nova ĐÃ sạch, không cần sửa DB instances
power_state = 4 (NOSTATE/SHUTDOWN)
host        = compute02
hypervisor  = compute02      ← khớp, không lệch
status      = SHUTOFF
```

### Bước 2 — Tìm domain libvirt ở compute

SSH vào đúng node compute (theo `host` ở bước 1), tìm tên container libvirt thật rồi:

```bash
docker exec nova_libvirt virsh list --all
docker exec nova_libvirt virsh dominfo instance-00000015
```

**Kết quả thực tế:** `virsh list --all` **rỗng**, `dominfo` báo
`failed to get domain 'instance-00000015'`.

> Diễn giải: domain CHƯA được define. Với VM boot-from-volume đang SHUTOFF, điều này bình
> thường — domain chỉ được dựng khi start. Vấn đề là khi start nó fail TRƯỚC khi define được
> domain → nên không có domain, không có qemu log.

### Bước 3 — Kiểm tra volume gốc (Cinder)

```bash
# Lấy volume id từ volumes_attached ở bước 1
openstack volume show <VOLUME_ID> -c status -c attachments
```

Cần xem `status`:

| status | Ý nghĩa |
|---|---|
| `in-use` | Volume OK, attach đúng → lỗi nằm chỗ khác |
| `reserved` / `attaching` / `detaching` | Volume kẹt → Nova không attach được lúc boot → fail im lặng |
| `available` | Attachment đã mất → cần gắn lại |
| `error` | Volume hỏng trạng thái → cần `cinder reset-state` |

**Kết quả thực tế:** `status = in-use`, attachment trỏ đúng `server_id`, đúng `host_name`,
đúng `/dev/vda`. → **Volume sạch, loại trừ.**

> ⚠️ Lưu ý: `openstack volume list | grep <instance_uuid>` sẽ KHÔNG ra gì, vì volume list
> hiển thị theo volume id chứ không theo instance id. Phải dùng `volume show <VOLUME_ID>`.

### Bước 4 — Start và bắt log TẠI TRẬN

Đây là bước quyết định để biết lệnh start chết ở tầng nào.

**Trên control** — ra lệnh start rồi poll status liên tục:

```bash
openstack server start <UUID>
# lặp lại nhiều lần, nhanh:
openstack server show <UUID> -c status -c "OS-EXT-STS:task_state" -c "OS-EXT-STS:vm_state"
```

**Kết quả thực tế — RẤT QUAN TRỌNG:**
```
task_state = powering-on   ← (giữ vài giây)
task_state = powering-on
task_state = powering-on
task_state = None          ← rồi tự về None, vm_state vẫn stopped, status vẫn SHUTOFF
```

→ Diễn giải: lệnh start ĐƯỢC nhận (task_state đổi sang `powering-on`), nhưng sau vài giây
**tự revert về None mà VM vẫn SHUTOFF** = **fail im lặng**.

**Trên compute** — theo dõi log nova_compute khi start (chạy TRÊN node compute):

```bash
docker logs -f --since 1s nova_compute
# hoặc lọc:
docker logs --tail 80 nova_compute 2>&1 | grep -iE 'amqp|rabbit|error|reconnect|<uuid>'
```

**Kết quả thực tế:** compute02 **KHÔNG in ra bất kỳ log nào** khi start.

> 🔑 **Manh mối vàng:** compute im lặng hoàn toàn nghĩa là lệnh start **không bao giờ đến
> được nova-compute**. Nó chết ở tầng trên (conductor/scheduler) HOẶC message kẹt ở
> **RabbitMQ**. "Không log ở compute" = compute không nhận được gì để mà log.

### Bước 5 — Soi tầng control + RabbitMQ

```bash
# Log conductor/scheduler khi start
docker logs --tail 60 nova_conductor 2>&1 | grep -iE '<uuid>|error|fault|traceback'
docker logs --tail 60 nova_scheduler 2>&1 | grep -iE '<uuid>|error|warning'

# Service compute có thực sự lắng nghe không (up ≠ chắc chắn nhận RPC)
openstack compute service list --host <compute>
```

**Kết quả thực tế:** conductor + scheduler cũng **không ra log gì** liên quan; compute
service báo `up`. → Service "trông khỏe" nhưng RPC không thông. Đây chính là dấu hiệu trùng
khớp với sự cố **RabbitMQ nghẹt** (xem mục 6).

### Bước 6 — Kiểm tra bảng `migrations` (thủ phạm phía Nova)

```bash
docker exec -it mariadb mysql -u root -p'<database_password>' nova -e \
"SELECT id, status, source_compute, dest_compute, migration_type \
 FROM migrations WHERE instance_uuid='<UUID>' ORDER BY id DESC LIMIT 5;"
```

**Kết quả thực tế:**
```
+----+-----------+----------------+--------------+----------------+
| id | status    | source_compute | dest_compute | migration_type |
+----+-----------+----------------+--------------+----------------+
|  6 | error     | compute02      | compute01    | resize         |  ← THỦ PHẠM (resize nhầm)
|  5 | error     | compute01      | compute02    | live-migration |  ← rác cũ
|  4 | error     | compute01      | compute02    | live-migration |
|  3 | error     | compute01      | compute02    | live-migration |
|  2 | confirmed | compute02      | compute01    | migration      |
+----+-----------+----------------+--------------+----------------+
```

→ Dòng `id=6`, `status=error`, type `resize` chính là cái resize nhầm để lại. Migration
record treo này góp phần làm start bị revert.

---

## 5. Nguyên nhân gốc (root cause)

Sự cố này có **hai lớp**, phải gỡ cả hai:

### Lớp 1 — Migration record treo (Nova)

Resize boot-from-volume fail → để lại migration record `status=error`. `reset-state` không
dọn bảng `migrations` → start bị chặn/revert im lặng.

### Lớp 2 — RabbitMQ nghẹt (gốc rễ thật sự)

> 🔑 **Phát hiện then chốt:** khi thử **xóa hẳn VM lỗi rồi tạo lại**, VM mới **cũng lỗi**.
> Điều đó chứng minh vấn đề KHÔNG nằm ở riêng VM cũ, mà ở tầng hạ tầng: **RabbitMQ bị nghẹt**
> (fanout/transient queue tồn đọng hàng chục nghìn message do nâng RabbitMQ 4.x mà chưa
> migrate quorum/stream queue đúng quy trình). RPC timeout → lệnh start/create không tới được
> compute → fail im lặng, không log.

Đây chính là lý do cả buổi sáng "đi vòng": mọi thao tác phía Nova (reset state, sửa migration)
đều không ăn thua bền vững vì **gốc rễ ở RabbitMQ chưa được chữa**. Chi tiết đầy đủ về
RabbitMQ xem tài liệu **"Binding failed for port"** đi kèm (chuỗi nhân quả, cách reset state
dứt điểm ở mục 10 của tài liệu đó).

### Chuỗi nhân quả tóm tắt

```
RabbitMQ 4.x chưa migrate/reset đúng → fanout/transient queue kẹt hàng chục nghìn message
        ↓
cơ chế reply RPC nghẽn → MessagingTimeout
        ↓
lệnh start/create instance không tới được nova-compute (compute im lặng, không log)
        ↓
task_state lên 'powering-on' rồi tự revert về None, VM vẫn SHUTOFF
        ↓  (cộng thêm)
migration record 'resize' status=error còn sót từ lần resize nhầm
        ↓
VM không start được — và tạo VM mới cũng lỗi   ← triệu chứng người dùng thấy
```

---

## 6. Cách khắc phục

> Làm theo thứ tự: **chữa gốc RabbitMQ trước**, rồi mới dọn state Nova. Nếu chỉ dọn Nova mà
> RabbitMQ còn nghẹt thì vài hôm lại tái diễn.

### Phần A — Chữa gốc: RabbitMQ (xem tài liệu "Binding failed for port")

Tóm tắt cách dứt điểm (chi tiết ở mục 10/11 tài liệu kia):

```bash
# Cách phẫu thuật (nhanh, chữa triệu chứng) — xóa queue kẹt rồi restart service sở hữu
docker exec rabbitmq rabbitmqctl delete_queue scheduler_fanout --if-empty=false
docker restart nova_scheduler

# Cách dứt điểm (reset state có kiểm soát) — stop toàn bộ service, reset rabbit, khởi động lại
docker exec rabbitmq rabbitmqctl stop_app
docker exec rabbitmq rabbitmqctl reset
docker exec rabbitmq rabbitmqctl start_app
kolla-ansible -i <inventory> reconfigure
```

Kiểm tra queue đã thông:

```bash
docker exec rabbitmq rabbitmqctl list_queues name messages consumers | grep -iE 'scheduler|fanout'
# messages phải dao động về 0
```

### Phần B — Dọn migration record treo (Nova)

```bash
docker exec -it mariadb mysql -u root -p'<database_password>' nova -e \
"UPDATE migrations SET status='confirmed' \
 WHERE instance_uuid='<UUID>' AND status='error';"
```

> Đặt về `confirmed` để Nova coi như resize đã xong, không còn chặn start. (Backup row trước
> khi UPDATE nếu cẩn thận: `SELECT ... ` ra file.)

### Phần C — Đồng bộ lại state VM và khởi động

```bash
# Reset về active
openstack server set --state active <UUID>
```

> ⚠️ **Bẫy đã gặp:** `--state` chỉ nhận `active` hoặc `error`, KHÔNG có `shutoff`/`stop`.
> Đừng mất thời gian thử các giá trị khác.

Sau khi set `active`, nếu `server start` báo:

```
ConflictException: 409: Cannot 'start' instance ... while it is in vm_state active
```

→ Đây là tiến triển tốt (migration đã được dọn). VM đang `active` "ảo" trong DB nhưng chưa
có domain thật. Dùng **hard reboot** để ép Nova dựng lại domain trên compute:

```bash
openstack server reboot --hard <UUID>
```

> Vì sao `reboot --hard` chứ không `start`: khi `vm_state=active`, `start` báo conflict;
> `reboot --hard` là lệnh hợp lệ và nó ép Nova **dựng lại domain libvirt từ đầu** — đúng cái
> cần sau khi đã gỡ migration record và thông RabbitMQ.

### Phần D — Kiểm tra kết quả

```bash
# Trên control
openstack server show <UUID> -c status -c "OS-EXT-STS:power_state" -c "OS-EXT-STS:task_state"
# Mong đợi: status=ACTIVE, power_state=Running, task_state=None

# Trên compute — domain phải thật sự lên
docker exec nova_libvirt virsh list --all
# Mong đợi: instance-00000015 state = running
```

### Phần E — Nếu vẫn SHUTOFF sau hard reboot

Kiểm tra `vm_state` trong DB có còn `resized` không:

```bash
docker exec -it mariadb mysql -u root -p'<database_password>' nova -e \
"SELECT vm_state, task_state, power_state FROM instances WHERE uuid='<UUID>';"
```

Nếu `vm_state='resized'`, ép về sạch rồi reboot lại:

```bash
docker exec -it mariadb mysql -u root -p'<database_password>' nova -e \
"UPDATE instances SET vm_state='stopped', task_state=NULL, power_state=4 WHERE uuid='<UUID>';"
openstack server reboot --hard <UUID>
```

(`power_state=4` = SHUTDOWN, `=1` = RUNNING)

---

## 7. Bài học rút ra

### Bài học chẩn đoán

1. **"VM không start được + không log" gần như luôn là fail im lặng** ở tầng RPC, không phải
   lỗi logic Nova. Đào xuống: state Nova → migration → volume → RPC → RabbitMQ.
2. **`task_state` lên rồi tự revert về None** = lệnh được nhận nhưng chết giữa chừng. Bắt log
   tại trận khi đang start là cách nhanh nhất khoanh vùng.
3. **Compute im lặng hoàn toàn khi start** = lệnh không tới được compute → nghi RabbitMQ /
   conductor, KHÔNG phải nghi libvirt/qemu.
4. **`reset-state` không dọn bảng `migrations`.** Resize fail luôn để lại migration record
   treo → phải sửa tay trong DB.
5. **Phép thử quyết định: xóa VM rồi tạo lại mà VẪN lỗi** → vấn đề ở hạ tầng (RabbitMQ),
   không phải ở VM. Đây là cách phân biệt "bệnh của 1 VM" với "bệnh của cả stack".
6. **Service báo `up` không có nghĩa RPC thông.** Heartbeat report được không đảm bảo message
   bus đang chuyển lệnh.

### Bẫy thao tác đã gặp (ghi để khỏi vấp lại)

- `virsh` phải chạy trên **node compute**, không phải control.
- Lỗi `-bash: ...: No such file or directory` là lỗi **shell** (paste dính ký tự ẩn), khác
  với `Error response from daemon: No such container` là lỗi **docker**.
- Mật khẩu DB lấy từ `/etc/kolla/passwords.yml` — dòng `database_password` (không prefix) là
  của **root**; `nova_database_password` là của user **nova**. Nhúng thẳng sau `-p'...'` để
  tránh lỗi paste vào prompt.
- `openstack volume list | grep <instance_uuid>` không ra gì là bình thường — dùng
  `volume show <VOLUME_ID>`.
- `openstack server set --state` chỉ nhận `active` / `error`.
- Khi VM `active` mà chưa có domain → dùng `reboot --hard`, không dùng `start` (sẽ conflict).

### Phòng ngừa

- **Không resize VM boot-from-volume** trừ khi thật sự cần; root disk trong flavor bị bỏ qua,
  lợi ích gần như bằng 0 mà rủi ro kẹt state cao.
- **Trước mọi nâng cấp RabbitMQ lớn (3.x → 4.x):** migrate quorum/durable queue + reset state
  đúng quy trình. Đây là gốc rễ của cả vụ này lẫn vụ "Binding failed".
- **Giám sát số message tồn đọng trong fanout queue** (Prometheus rabbitmq exporter) để bắt
  sớm trước khi RPC sập.

---

## 8. Cheat sheet (tra nhanh)

### Chẩn đoán VM kẹt

```bash
# Trạng thái VM
openstack server show <UUID> -f json
openstack server show <UUID> -c status -c "OS-EXT-STS:task_state" -c "OS-EXT-STS:vm_state"

# Domain libvirt (CHẠY TRÊN COMPUTE)
docker exec nova_libvirt virsh list --all
docker exec nova_libvirt virsh dominfo instance-XXXXXXXX

# Volume gốc
openstack volume show <VOLUME_ID> -c status -c attachments

# Service & log
openstack compute service list --host <compute>
docker logs --tail 80 nova_compute 2>&1 | grep -iE 'amqp|rabbit|error|<uuid>'   # trên compute
docker logs --tail 60 nova_conductor 2>&1 | grep -iE '<uuid>|error'             # trên control

# Migration record treo
docker exec -it mariadb mysql -u root -p'<pw>' nova -e \
"SELECT id,status,source_compute,dest_compute,migration_type FROM migrations \
 WHERE instance_uuid='<UUID>' ORDER BY id DESC LIMIT 5;"
```

### Khắc phục

```bash
# 1) Chữa gốc RabbitMQ (xem tài liệu Binding failed) — reset state hoặc delete_queue + restart

# 2) Dọn migration treo
docker exec -it mariadb mysql -u root -p'<pw>' nova -e \
"UPDATE migrations SET status='confirmed' WHERE instance_uuid='<UUID>' AND status='error';"

# 3) Đồng bộ + khởi động
openstack server set --state active <UUID>
openstack server reboot --hard <UUID>          # nếu start báo conflict vm_state active

# 4) Kiểm tra
openstack server show <UUID> -c status -c "OS-EXT-STS:power_state"
docker exec nova_libvirt virsh list --all      # trên compute, phải thấy domain running
```

---

## Phụ lục — Liên hệ với sự cố "Binding failed for port"

Hai sự cố này **cùng một gốc rễ** (RabbitMQ nghẹt do queue quorum/stream chưa migrate),
chỉ khác triệu chứng bề mặt:

| | Sự cố "Binding failed" | Sự cố "VM kẹt SHUTOFF" (tài liệu này) |
|---|---|---|
| Triệu chứng | Không bind được port khi tạo VM | VM không start được + tạo VM mới cũng lỗi |
| Tầng bộc lộ | Neutron (OVS agent report_state timeout) | Nova (start revert im lặng, compute không log) |
| Cơ chế chung | RPC timeout do RabbitMQ queue nghẹt | RPC timeout do RabbitMQ queue nghẹt |
| Sửa gốc | Reset state RabbitMQ đúng quy trình | Reset state RabbitMQ + dọn migration Nova |

> Nếu gặp một trong hai, kiểm tra luôn cái còn lại — chúng thường đi cùng nhau.
