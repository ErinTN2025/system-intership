## Advanced Linux Installation Concepts
### Installation Modes
- **Minimal Install**: Core system only, reduces attack surface, một số gói phần mềm cơ bản nhất cần để hệ thống khởi động và chạy.
- **Full Install**: Cài toàn bộ các gói phần mềm đi kèm hệ điều hành: giao diện đồ hoạ(GUI), tiện ích văn phòng,... Complete desktop
environment with application
- **Server Install**: Optimized for headless server deployment. Đây là chế độ tập trung vào các dịch vụ server như web server (Apache, Nginx), database (MySQL, MariaDB, PostgreSQL), SSH, DNS, mail server… 
  - **Mục đích**: Dành cho các hệ thống cần phục vụ client qua mạng (website, dịch vụ mạng, ứng dụng…).

### Installation Roadmap
- **Pre-flight Check:**
  - **System Requirements**: Does your
hardware meet the minimum CPU,
RAM, and disk space needs.
  - **Installation Media**: Create a bootable USB drive or set up a virtual machine with the .iso file.
- **The Installer:**
  - The most modern installers (like Ubuntu's) guide you through:
  - Language, Keyboard Layout, and
Network Configuration.
  - Disk Partitioning: The most critical step. This is where you tell Linux how to organize the hard drive.
  - User Creation & Hostname.
  - Software Selection( e.g., install as a minimal server or with specific tools like Docker).
- **Post-Installation:**
  - First boot, update all packages (sudo apt update && sudo apt upgrade).

### Decoding Disk Partitioning
#### Why we need?
- Separate the OS from user data(e.g., putting/ home on its own partition).
- Improve performance and security.
- Use different file systems for different purposes.
#### Partitioning Schemes:
- **MBR (Master Boot Record)**: Là chuẩn phân vùng cũ ra đời từ năm 1983 (cùng với PC BIOS). Thông tin về phân vùng được lưu trong sector đầu tiên của ổ đĩa (sector 0). Sector này gọi là MBR.
  - **Đặc điểm**:
    - Hỗ trợ tối đa 4 primary partitions (nếu muốn nhiều hơn phải dùng 1 “extended partition” rồi chia nhỏ thành “logical partitions”).
    - Giới hạn dung lượng ổ cứng: tối đa 2TB (nếu ổ lớn hơn, phần dư sẽ không sử dụng được).
    - Chỉ dùng tốt với hệ thống khởi động bằng BIOS truyền thống.
- **GPT (GUID Partition Table)**: Là chuẩn phân vùng mới (ra đời cùng với chuẩn UEFI). Dùng GUID (Globally Unique Identifier) để định danh phân vùng.
  - **Đặc điểm**:
    - Cho phép tạo lên đến 128 phân vùng (trên Windows, Linux có thể còn nhiều hơn).
    - Hỗ trợ ổ cứng có dung lượng rất lớn (lý thuyết đến 9.4 ZB ~ không giới hạn thực tế).
    - Lưu thông tin phân vùng ở nhiều nơi (đầu và cuối ổ) → tăng độ an toàn.
    - Yêu cầu máy hỗ trợ UEFI firmware để boot trực tiếp (nhưng có thể dùng kết hợp với BIOS trong một số trường hợp).

#### So sánh nhanh

| Tiêu chí          | MBR                        | GPT                                 |
| ----------------- | -------------------------- | ----------------------------------- |
| Năm ra đời        | 1983                       | 2000s (chuẩn UEFI)                  |
| Dung lượng tối đa | 2 TB                       | ~9.4 ZB (gần như vô hạn)            |
| Số phân vùng      | 4 primary (tối đa)         | 128 (Windows), nhiều hơn trên Linux |
| Cơ chế boot       | BIOS                       | UEFI                                |
| Độ an toàn        | Thấp (1 bảng MBR duy nhất) | Cao (có backup, CRC check)          |
| Ứng dụng hiện nay | Máy cũ, ổ < 2TB            | Máy mới, ổ > 2TB, chuẩn khuyến nghị |

### Installation Troubleshooting
- **GRUB Boot Issues**: Boot from live USB, mount root partition, reinstall GRUB
bootloader using `grub-install` and `update-grub`.
- **Network Configuration**: Configure static IP with `netplan`(Ubuntu) or `nmcli`(Red Hat). verify DNS resolution.
- **Disk Recognition Errors**: Check BIOS/UEFI settings, verify SATA connections, use `fdisk -l` to detect available drives.
- **Post-Install Validation**: Run system updates, enable essential services, configure firewall, and verify hardware detection.