# CỨU CỤM GALERA MỒ CÔI SAU KHI TẮT CẢ 3 NODE

> Tình huống đã gặp thật trong lab này. Đây là quy trình chính thống của Galera, ghi lại để
> sau gặp lại làm trong 5 phút thay vì hoảng.

---

## 1. KHI NÀO GẶP TÌNH HUỐNG NÀY

Triệu chứng đặc trưng:
- Đã từng có cụm Galera 3 node chạy ngon.
- **Tắt cả 3 controller cùng lúc** (shutdown lab, mất điện, snapshot toàn bộ...).
- Mở lại, `sudo systemctl start mariadb` ở mọi node đều fail.
- Log có cụm từ:
  ```
  WSREP: failed to open gcomm backend connection: 110
  WSREP: gcs connect failed: Connection timed out
  ```

Đây **không phải lỗi**. Đây là Galera làm đúng việc của nó: từ chối tự khởi động vì sợ
split-brain. Logic của nó: "tao không biết 2 node kia có ai data mới hơn tao không, để chắc thì
tao không dám tự nhận mình đúng".

---

## 2. HIỂU 2 KHÁI NIỆM TRƯỚC KHI ĐỘNG TAY

**File `/var/lib/mysql/grastate.dat`** là "thẻ căn cước" của node trong cụm:
```
uuid:              định danh cụm (cả 3 node phải giống nhau)
seqno:             số thứ tự transaction cuối node này thấy
safe_to_bootstrap: cờ "node này có quyền tự lập cụm không" (0 = không, 1 = có)
```

**Tại sao `seqno: -1` sau khi tắt máy không sạch:** MariaDB chỉ ghi seqno xuống file lúc tắt
**đúng quy trình**. Tắt đột ngột → file chưa kịp update → giá trị `-1` (chưa biết). Nhưng số
thật vẫn nằm trong **InnoDB redo log** trên đĩa, lôi ra được bằng `mariadbd --wsrep-recover`.

→ Quy tắc cứu cụm: **node nào có `seqno` THẬT cao nhất thì node đó bootstrap.** Các node có
seqno thấp hơn phải join và bị overwrite phần thiếu — đây là điều bạn muốn (kéo về data mới).
Nếu bootstrap nhầm node có seqno thấp → 2 node kia khi join sẽ bị overwrite về data CŨ → mất
dữ liệu.

---

## 3. QUY TRÌNH CỨU (LÀM ĐÚNG THỨ TỰ)

### Bước 1: Xác nhận cả 3 node cùng cụm

```bash
# trên cả 3 controller
sudo cat /var/lib/mysql/grastate.dat
```

Kiểm tra `uuid` phải GIỐNG NHAU ở cả 3 node. Nếu khác nhau → 3 cụm tách biệt → bài toán khác,
phức tạp hơn, **dừng lại đừng làm tiếp** (rủi ro mất data, cần xử riêng).

Nếu cùng uuid → đi tiếp.

### Bước 2: Lấy `seqno` thật trên cả 3 node

MariaDB không cho chạy bằng `root` → phải qua user `mysql`:

```bash
# chạy LẦN LƯỢT trên cả 3 controller
sudo -u mysql mariadbd --wsrep-recover --log-error=/tmp/recover.log
```

> Lệnh tự chạy vài giây rồi thoát. Đọc redo log → ghi log ra `/tmp/recover.log`.
> An toàn chạy lại nhiều lần. Không sửa data.

Xem kết quả:
```bash
sudo grep -i 'recovered position' /tmp/recover.log
```

Sẽ ra dòng kiểu:
```
... [Note] WSREP: Recovered position: <uuid>:<seqno>
```

Số sau dấu `:` là `seqno` thật. Ghi lại cho cả 3 node.

### Bước 3: Chọn node bootstrap

So `seqno` 3 node:

| Tình huống | Chọn node nào | Lý do |
|---|---|---|
| seqno khác nhau | Node có **seqno cao nhất** | Có data mới nhất |
| seqno **bằng nhau** ở cả 3 | Node nào cũng được (chọn controller01 cho thuận) | Data 3 node y hệt — bằng chứng là tắt máy lúc cụm idle, không có ghi mới |

> **Ca lab này gặp:** cả 3 node `seqno=12` → chọn controller01.

### Bước 4: Sửa cờ `safe_to_bootstrap` trên node được chọn

**Chỉ trên 1 node được chọn ở bước 3:**
```bash
sudo sed -i 's/^safe_to_bootstrap: 0/safe_to_bootstrap: 1/' /var/lib/mysql/grastate.dat
sudo cat /var/lib/mysql/grastate.dat
```

Phải thấy `safe_to_bootstrap: 1`. Đây là cách nói với Galera: "tao chịu trách nhiệm, tao có data
mới nhất, tao tự lập cụm".

> ⚠️ KHÔNG sửa cờ này trên 2 node còn lại. Chỉ 1 node bootstrap. Hai node kia sẽ join sau.

### Bước 5: Bootstrap node được chọn

```bash
sudo galera_new_cluster
```

Đợi 5-10s, kiểm tra:
```bash
sudo mariadb -e "SHOW STATUS LIKE 'wsrep_cluster_size';"        # = 1
sudo mariadb -e "SHOW STATUS LIKE 'wsrep_local_state_comment';" # = Synced
```

Có `size=1` + `Synced` → node bootstrap thành công, sẵn sàng cho node khác join.

### Bước 6: Join 2 node còn lại — LẦN LƯỢT

**Node 2** (đợi node 1 bootstrap xong mới chạy):
```bash
sudo systemctl start mariadb
```
Đợi 15-30s (đang SST kéo data). Kiểm tra trên node 1:
```bash
sudo mariadb -e "SHOW STATUS LIKE 'wsrep_cluster_size';"   # = 2
```

Thấy `2` mới sang **Node 3**:
```bash
sudo systemctl start mariadb
```
Đợi 15-30s. Kiểm tra trên node 1:
```bash
sudo mariadb -e "SHOW STATUS LIKE 'wsrep_cluster_size';"     # = 3
sudo mariadb -e "SHOW STATUS LIKE 'wsrep_cluster_status';"   # = Primary
```

> ⚠️ Đừng start 2 node con cùng lúc. Tranh chấp SST có thể làm 1 node fail và phải retry.

### Bước 7: Verify data còn nguyên

```bash
sudo mariadb -e "SHOW DATABASES;"
```
Phải thấy các database cũ của bạn (nếu đã tạo Keystone/Nova thì thấy chúng). Data còn = cứu
thành công.

---

## 4. ❌ NHỮNG ĐIỀU TUYỆT ĐỐI KHÔNG LÀM

- **Đừng** `galera_new_cluster` trên >1 node → split-brain, 2 cụm riêng, ghi đè loạn data.
- **Đừng** sửa `safe_to_bootstrap: 1` trên nhiều node → bằng cách tự gây split-brain.
- **Đừng** xoá `/var/lib/mysql/` để "làm lại sạch" → mất toàn bộ data.
- **Đừng** bỏ bước `--wsrep-recover` và đoán node nào bootstrap → bootstrap nhầm node cũ →
  data 2 node kia bị overwrite về data cũ khi join.
- **Đừng** start 3 node song song. Lần lượt: bootstrap → đợi → join 1 → đợi → join 2.

---

## 5. CÁCH PHÒNG (ĐỪNG ĐỂ GẶP LẠI)

### 5.1. Khi cần tắt cả lab

**TẮT LẦN LƯỢT** từng controller, không bao giờ tắt cả 3 cùng lúc:

```bash
# trên controller03
sudo systemctl stop mariadb
sudo shutdown -h now

# đợi controller03 tắt hẳn, rồi trên controller02
sudo systemctl stop mariadb
sudo shutdown -h now

# CUỐI CÙNG controller01 — node này tắt sạch sẽ ghi seqno đúng, lần boot kế tiếp
# CÓ THỂ tự bootstrap (safe_to_bootstrap sẽ tự thành 1)
sudo systemctl stop mariadb
sudo shutdown -h now
```

> Vì sao thứ tự ngược (3→2→1)? Để controller01 là **node tắt cuối cùng** → nó có data mới nhất
> + được Galera tự đánh dấu `safe_to_bootstrap: 1` khi tắt sạch. Bật lại lần sau: controller01
> start trước (`galera_new_cluster` nếu cần, hoặc thử `systemctl start mariadb` xem có lên
> không), rồi 02, rồi 03 join lần lượt.

### 5.2. Khi cần restart 1 controller

Bình thường: cứ `sudo systemctl restart mariadb`. Galera xử được. Đợi node đó về Synced và size
về 3 trước khi đụng node kế.

### 5.3. Thứ tự bật cụm sau khi đã tắt cả lab đúng cách (5.1)

1. Bật controller01 trước (node tắt cuối).
2. Thử `sudo systemctl start mariadb`. Nếu lên ngay → may mắn, sang bước 4.
3. Nếu fail (gcomm timeout) → quay lại Mục 3 quy trình cứu.
4. Bật controller02, `sudo systemctl start mariadb`. Đợi size=2.
5. Bật controller03, `sudo systemctl start mariadb`. Đợi size=3.

---

## 6. SỰ CỐ KHI ĐANG CỨU

| Triệu chứng | Nguyên nhân | Cách xử |
|---|---|---|
| `--wsrep-recover` báo "Please consult... how to run as root" | đang chạy bằng root | dùng `sudo -u mysql mariadbd --wsrep-recover --log-error=/tmp/recover.log` |
| `--wsrep-recover` không in "Recovered position" | grep sai chữ, lọc rỗng | `sudo tail -40 /tmp/recover.log` xem nguyên log |
| `galera_new_cluster` báo "It may not be safe to bootstrap" | quên sửa `safe_to_bootstrap: 1` | quay lại bước 4 |
| Node 2 join nhưng treo lâu | SST đang kéo data (vài chục MB thì 10-30s, GB thì lâu hơn) | đợi; xem `journalctl -u mariadb -f` |
| Node 2 fail với "rsync failed" | thiếu `rsync`, hoặc cổng 4444 chặn | `apt install rsync`; kiểm tra security group |
| Sau bootstrap, `cluster_size = 1` mãi | node 2/3 chưa start, hoặc cookie/cluster_address sai | start node 2 trước; kiểm tra `/etc/mysql/mariadb.conf.d/99-galera.cnf` |

---

## 7. NGUỒN THAM KHẢO

- MariaDB KB — Getting Started with MariaDB Galera Cluster (mục Recovery):
  https://mariadb.com/kb/en/getting-started-with-mariadb-galera-cluster/
- Galera — Restarting the cluster:
  https://galeracluster.com/library/documentation/crash-recovery.html
- OpenStack HA Guide — Database:
  https://docs.openstack.org/ha-guide/control-plane-stateful.html
