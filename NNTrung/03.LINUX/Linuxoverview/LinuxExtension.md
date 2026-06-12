# Một vài ghi chú khác về Linux

## 1. Khái niệm về Inode
> Imagine a scenario where a service (e.g., Apache or Nginx) fails to start. You check the log and it says 'No space left on device'. However, when you run df -h, it shows that the disk space is only 50% utilized. What could be the root cause of this issue, and how do you check it?

- Điều này liên quan tới Inode.
- Linux lưu:
  - Data của file
  - Metadata của file (owner, permission, vị trí block...)
- Metadata này được chứa trong inode
- Mỗi file hoặc directory cần 1 inode

Ví dụ:
- 1 file 1GB -> 1 inode
- 1 triệu file log 1KB -> 1 triệu inode

Filesystem có thể còn hàng trăm GB trống nhưng nếu inode đã dùng hết thì không thể tạo file mới.

**Cách kiểm tra**
- Kiểm tra dung lượng: 
```bash
df -h
```
- Kiểm tra inode
```bash
df -i
```

**Một dịch vụ khi khởi động cần**
- tạo PID file
- ghi access log
- ghi error log
- tạo socket file
- tạo temporary file

ví dụ:
```bash
/var/run/nginx.pid
```
- Nếu filesystem không còn inode: service sẽ không start được.
- Thứ tự check ưu tiên:
```bash
df -h        # hết block?
df -i        # hết inode?
lsof | grep deleted   # file đã xóa nhưng còn bị giữ?
mount        # filesystem mount đúng chưa?
dmesg        # lỗi filesystem?
```

**Nguyên nhân hay gặp**
- Log rotation bị lỗi: Tạo hàng triệu file log
- Cache sinh quá nhiều file nhỏ
- Mail queue bị kẹt
- Container/K8s lỗi pod sinh file liên tục

> You notice that a Linux server is sluggish. You run the top command and see that the CPU usage is at 99%, but the 'wa' (I/O wait) percentage is also extremely high. What does a high 'wa' mean, and how would you investigate which process or resource is causing this bottleneck?

- CPU: 99%
- `wa`: 80%
- `wa`: là I/O wait nghĩa là: CPU không thực sự bận tính toán, mà đang chờ thao tác I/O hoàn thành.

Ví dụ: Process gửi request đọc dữ liệu, CPU phải chờ dữ liệu đc trả về từ chỗ lưu trữ như DISK, SSD, Ceph, NFS, SAN, DB(ko có thì nó làm j có j để tính). Trong thời gian đó CPU không làm được gì hữu ích nên thời gian này được tính vào `wa`

Hiểu chính xác:
```bash
CPU usage: 99%
wa: 85%
```
thực chất
```bash
User CPU: 10%
System CPU: 4%
I/O wait: 85%
```
- Cpu không hề bận tính toán, hệ thống đang chờ I/O
- Điều tra bước đầu:
```bash
top
htop
```
- Xem disk có thực sự nghẽn không
```bash
sudo apt install sysstat
iostat -xz 1
```
- Tìm process nào gây I/O
```bash
sudo iotop
```
- Nếu là storage mạng (NFS/Ceph)
```bash
mount
```

## Zombie Process
### 1. Trước tiên phải hiểu Process chết như thế nào?
- Khi bạn chạy:
```bash
sleep 10
```
Kernel tạo một process
```bash
PID 1000
sleep 10
```
Trong kernel sẽ có một cấu trúc dữ liệu:
```C
task_struct
```
chứa
```bash
PID
PPID
State
Memory mapping
Open files
Signal handlers
...
```
- Mỗi process đều có 1 `task_struct`
- Vì process cha cần biết: trạng thái của process con.
### 2. Zombie Process
Khi process kết thúc: `Memory`, `File descriptors`, `Socket`, `CPU` được giải phóng.

Nhưng: `PID`, `Exit_status`, `task_struct` vẫn được giữ lại.

Lúc này process chuyển sang: 
```bash
EXIT_ZOMBIE  
State = Z
```
Ví dụ:
```bash
Running Process -> exit() ->  Zombie -> wait() -> Removed completely
```
### 3. Tại sao cần trạng thái này
- Process con chết ngay -> process cha không có thông tin gì của nó hết.
- Sau khi kết thúc 1 process, Kernel gửi cho cha một `SIGCHLD` -> thông báo process con đã kết thúc.
- Process cha phải gọi:
```bash
wait()
waitpid()
```
để nhận: Exit code hoặc Resource usage
- Luồng:
```bash
Child -> exit() -> Zombie  -> Parent wait() -> Kernel remove
```

### 4. Zombie bị treo
- Process cha không gọi `wait()`
- Zombie là process đã chết rồi, nó không có Memory, CPU, Thread, Socket.
- Nó chỉ còn task_struct, PID, Exit code
- Tuy nhiên Linux có giới hạn PID:
```bash
cat /proc/sys/kernel/pid_max
```
- `kill -9 zombie_pid`: không có tác dụng vì process này không còn chạy.
- 2 cách:
```bash
kill -SIGCHLD 1000
or
systemctl restart apache2
```
- PID 1 có vài trò là process đầu tiên là init cũ, systemd hiện nay.
```bash
fork()
 ↓
Running
 ↓
exit()
 ↓
EXIT_ZOMBIE
 ↓
SIGCHLD gửi cho parent
 ↓
parent wait()
 ↓
EXIT_DEAD
 ↓
Kernel remove task_struct
```

### 5. Tại sao cần có process cha và process con
- Bạn ở Bash bạn gõ lệnh command, Bash không tự thực hiện ls, Nó làm:
```bash
fork();       // tạo process mới
exec();       // biến process mới thành ls
```
- Kết quả:
```bash
Bash (PID 100)
 └── ls (PID 101)
```
- `ls` chính là process con của Bash
- Sau khi `ls` chạy xong, Bash quay lại thực hiện prompt
- Nếu k có mô hình cha-con, Bash biến thành `ls` mất luôn
- Process cha là quản lý, theo dõi, thu dọn, nhận kết quả của process con.

## Cấp quyền và Phân quyền trong Linux
### 1. Cấp quyền (Grant Permission)
- Là hành động gán các quyền cụ thể lên một đối tượng (file, thư mục, device,...)
- Ví dụ:
```bash
chmod 755 script.sh
```
- Bạn vừa cấp:
```bash
User : rwx
Group : r-x
Other : r-x
```
Hay như:
```bash
chown nginx:nginx web.conf
```
- Bạn cấp quyền sở huwx cho user/group `nginx`

### 2. Phân quyền (Authorization / Access Control Design)
- Thiết kế xem ai được làm gì trong hệ thống.
- Ví dụ công ty có:
```bash
Admin
DevOps
Developer
Auditor
```
- Bạn muốn quyết định
```bash
Admin   -> toàn quyền
DevOps  -> restart service
Developer -> chỉ đọc log
Auditor  ->  chỉ xem báo cáo
```
- Đó là phân quyền:
Sau đó mới dùng:
```bash
groupadd devOps # Tạo 1 group mới tên devOps
groupadd auditor

usermod -aG devOps trung  # usermod: sửa thông tin user, -G: Danh sách supplementary groups, -a: Append- giữ nguyên các group cũ + thêm devOps
usermod -aG auditor nam
```
rồi:
```bash
chown root:devOps  /opt/scripts
chmod 750 /opt/scripts
```
Nhìn vào trên ta thấy phân quyền rõ ràng giả sử đó là 1 file quan trọng, người sở hữu file được toàn quyền read, write, những ai đc ưu tiên trong devOps thì đc read + x, còn người không thuộc chuyên môn thì k có quyền được tiếp cận.

- Để thực hiện hóa việc phân quyền. Góc nhìn của SysAdmin:

| **Khái niệm** | Câu hỏi trả lời |
|-------------|-----------------|
| Phân quyền  | "Ai được làm gì?" |
| Cấp quyền   | "Làm cách nào để người đó có quyền đó "|

