# VM Ware Workstation
## Switch ảo (Virtual Switch _ VMnet0, VMnet1, VMnet8)
- Đây là thiết bị mạng ảo do VMware tạo ra trên máy Host.
- Nó giống như Switch vậy lý logic trong mạng LAN, nhiệm vụ là kết nối các card mạng ảo (của VM) với nhau và/hoặc với card mạng thật của Host.
- Một số switch ảo mặc định trong VMware:
  - VMnet0: cho chế độ Bridged (kết nối thẳng với switch/ vLan ngoài).
  - VMnet1: cho chế độ Host-only (switch riêng, không nối Internet).
  - VMnet8: cho chế độ NAT (switch riêng, có gateway NAT đi Internet).

  ![altimage](../Images/switchvirtual.png)

## Phân biệt 3 chế độ network trong VMware: NAT, Bridget, Host-only
🔑 **Tóm tắt nhanh:**
| **Tính năng** | **NAT** | **Bridged**| **Host-Only**|
|---------------|---------|------------|--------------| 
| **IP VM**     | Máy ảo lấy IP từ VMware DHCP(VMnet 8) | Máy ảo lấy IP từ router của mạng LAN | Máy ảo lấy IP từ VMware riêng biệt(VMnet 1)|
| **Kết nối Internet** | Có(qua host) | Có (trực tiếp) | Không |
| **Kết nối LAN ngoài** | Không (bị ẩn sau host) | Có ( như mọi máy tính thật trong mạng) | Không( chỉ liên lạc được với host và máy ảo VM khác) |
| **Kết nối với Host** | Có | Có | Có |
| **Bảo mật**| Cao( máy ảo ẩn khỏi mạng bên ngoài) | Thấp (máy ảo lộ trực tiếp ra ngoài mạng) | Rất cao (máy ảo hoàn toàn cách ly) |
| **Tính ứng dụng** | Truy cập internet mà không lộ IP thật | Test mạng như máy thật, cần IP tĩnh | Môi trường cô lập, thử nghiệm nội bộ |

 🖊️  **Chi tiết từng chế độ**


### 1. NAT (Network Address Translation)

 ![altimage](../Images/NAT.png)

#### 1.1 Khái niệm
- NAT (Network Address Translation): dịch địa chỉ mạng.
- Khi chọn chế độ NAT cho máy ảo (VM), VMware sẽ tạo ra một card mạng ảo (VMnet8).
- Máy ảo sẽ nhận một IP Private trong dải do VMware quản lý. Lúc này, các máy ảo sẽ kết nối với máy thật qua switch ảo VMnet8, máy thật sẽ đóng vai trò NAT server cho các máy ảo.
- Khi máy ảo truy cập Internet, Vmware sẽ dịch IP Private của VM sang IP của máy Host.

👉 Nghĩa là với mạng bên ngoài, tất cả VM chạy NAT sẽ "núp bóng" sau máy Host.
#### Cách hoạt động
- **Máy ảo (VM) gửi yêu cầu truy cập mạng:** Khi máy ảo muốn truy cập một địa chỉ trên mạng (ví dụ: một trang web), nó sẽ gửi một gói tin đi. Gói tin này sẽ có địa chỉ iP nguồn là địa chỉ IP riêng (private IP) của máy ảo.
- **Máy thật (Host) thực hiện NAT**: Máy thật đóng vai trò là NAT device cho máy ảo. Khi gói tin từ máy ảo đến, máy thật sẽ thực hiện các bước sau:
  - Thay đổi địa chỉ IP nguồn trong gói tin từ địa chỉ IP riêng của máy ảo thành địa chỉ IP riêng của chính máy thật.
  - Ghi lại thông tin về kết nối này (địa chỉ IP và port của máy ảo, địa chỉ IP và port mới của máy thật) vào bảng NAT của nó. Thông tin này sẽ được dùng để theo dõi các phản hồi sau này.
- **Router thực hiện NAT lần 2**: Gói tin sau khi đã được NAT bởi máy thật sẽ tiếp tục được gửi đến router. Router, là thiết bị kết nối mạng nội bộ với internet, sẽ thực hiện NAT lần thứ hai:
  - Thay đổi địa chỉ IP nguồn trong gói tin từ địa chỉ IP riêng của máy thật thành địa chỉ IP công cộng (public IP) được cấp bởi nhà cung cấp dịch vụ internet (ISP).
  - Tương tự, router cũng sẽ ghi lại thông tin về kết nối này vào bảng NAT của nó( địa chri IP và port của máy thật, địa chỉ IP và port mới sau khi NAT ra IP public).
- **Phản hồi từ internet**: Khi máy chủ web hoặc dịch vụ mà máy ảo đang cố gắng truy cập gửi phản hồi, gói tin sẽ có địa chỉ IP đích là địa chỉ của IP công cộng của router.
- **Router chuyển phản hồi về máy thật**: Router sẽ xem xét bảng NAT của nó và xác định rằng gói tin này là phản hồi cho một kết nối đã được khởi tạo từ địa chỉ IP riêng của máy thật. Do đó, router sẽ thay đổi địa chỉ IP đích trong gói tin từ địa chỉ IP công cộng trở lại địa chỉ IP riêng của máy thật và gửi gói tin này về máy thật.
- **Máy thật chuyển phản hồi về máy ảo**: Khi máy thật nhận được gói tin phản hồi, nó sẽ xem xét bảng NAT của mình và xác định rằng gói tin này là phản hồi cho một kết nối đã được khởi tảo từ địa chỉ IP riêng của máy ảo.

**Lưu ý**: Nếu cấu hình IP tĩnh cho máy ảo ví dụ 10.0.0.5 mà IP không thuộc dải VMnet8:
  - Máy ảo không thể giao tiếp với gateway(máy chủ) -> mất khả năng truy cập Internet cũng như không giao tiếp được với các máy ảo khác trong cụng mạng NAT.
  - Máy chủ có IP tĩnh ngoài dải VMnet8, nó không thuộc cùng subnet với gateway, không lk đưới tới máy chủ. Kết quả sẽ là hoàn toàn mất kết nối mạng. Điều tương tự cũng sẽ xảy ra với Host Only hay Bridged.

### Bridged Networking
![anda](../Images/Bridget.png)
#### Khái niệm
- Khi chọn chế độ này, card mạng ảo (NIC của VM) sẽ được nối trực tiếp(bridge) với card mạng thật của Host(Ethernet hoặc WiFi).
- Kết quả: Máy ảo sẽ xuất hiện trong mạng LAN như một máy tính vật lý độc lập, có IP trong cùng dải mạng với các máy khác.
- Máy ảo lúc này = 1 máy tính thật mới trong mạng LAN.
#### Cách hoạt động
- Máy ảo kết nối trực tiếp vào mạng LAN thông qua card mạng vật lý của máy host.
  - VMware tạo một Virtual Bridge giữa adapter Ethernet/WiFI của router ngoài đời thực và VMnet0 (cấu nối ảo).
  - Máy ảo hoạt động như một thiết bị độc lập trong mạng LAN, giống như một máy tính thật.
  - Máy ảo có thể lấy IP từ DHCP trong mạng LAN, giống như máy host và các thiết bị khác trong mạng.
- Khi máy ảo gửi gói tin, nó đi qua Virtual Ethernet Adapter -> VMnet0 -> card mạng vật lý của máy host -. mạng LAN.
- Khi máy ảo nhận gói tin, dữ liệu từ mạng LAN đi vào card mạng vật lý của máy host -> VMnet0 -> máy ảo.
### Host-Only
![altimage](../Images/hostonly.png)

Host-only là một loại mạng ảo nơi các VM và máy Host( thông qua một virtual network adapter trên Host - VMnet1) nằm cùng một mạng riêng không lối ra Internet hoặc LAN bên ngoài theo mặc định. Nó tạo một mạng nội bộ (private virtual network) chỉ dành cho Host và các VM được gán vào mạng đó.

Host only asd