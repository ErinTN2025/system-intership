# Học cụm OpenStack của mình: đọc file, hiểu lệnh, tự sửa

Đây là sổ học và nơi thực hành cho cụm Talos/OpenStack đã dựng. Mục tiêu: khi gặp một lệnh, biết nó đọc file nào, đổi cái gì, kết quả ở đâu và lần sau phải sửa ở đâu.

Muốn dựng mới: đọc [09 — New Cluster](docs/09-New-Cluster.md), bắt đầu từ Kubernetes đã có, không có bài cài Talos. Đọc [START-HERE.md](START-HERE.md) để biết bộ file chính; [07 — Giữ/xóa file](docs/07-Keep-or-Delete.md) để dọn mà biết mình đang xóa gì.

Đọc lần lượt:

| Bài | Bạn sẽ trả lời được |
|---|---|
| [01. Bản đồ](docs/01-Map.md) | Bastion, Talos, Helm và Genestack làm gì? File nào là bản cuối? |
| [02. Helm từ đầu tới cuối](docs/02-Helm.md) | Chart/version/values/render/release/pod liên quan thế nào? |
| [03. Tự sửa một dịch vụ](docs/03-Change.md) | Đổi Horizon bằng file, render, upgrade và xem kết quả thế nào? |
| [04. Image và mất Internet](docs/04-Images.md) | Tải image từ đâu, lưu local, nạp registry, đổi values/Talos ra sao? |
| [05. Học cấu trúc Git](docs/05-Git.md) | Gom cấu hình chính, snapshot và secrets thế nào? |
| [06. Đọc lỗi theo luồng request](docs/06-Debug.md) | Phân biệt Gateway, Horizon, catalog, DNS, API và storage? |
| [08. Octavia theo Genestack](docs/08-Octavia-Genestack.md) | Quy trình cuối Octavia OVN, Gateway, CLI và tạo LB; lý do cấu hình |
| [09. Dựng cụm mới](docs/09-New-Cluster.md) | Thứ tự OpenStack từ Kubernetes sẵn có; chart/config/tài liệu nằm local |

## Đường dẫn dùng trong bài

Copy nguyên thư mục này sang `~/Openstack-Lab-Learning` trên bastion Linux. Trong ví dụ:

```bash
export STUDY_ROOT="$HOME/Openstack-Lab-Learning"
export LAB_ROOT="$HOME/osh-lab"
```

STUDY_ROOT là bài học/ví dụ mới; LAB_ROOT trong các bài cũ là cấu hình/chart thực tế đã có. Nếu máy đó đã mất, chạy tools/prepare-files.sh và đặt LAB_ROOT theo thư mục output mới để tập render; get values vẫn cần cụm đang chạy. Folder bastion trong workspace Windows là bản chụp home, không phải máy đang chạy. Chạy Bash trên Linux, không paste Bash vào PowerShell. Không có cluster vẫn đọc được chart/YAML; kubectl và helm get cần kết nối cụm.

## Tổ chức

- `docs/`: giải thích mới theo thứ tự học.
- `examples/`: bản sao chọn lọc từ bastion; mỗi file có nguồn ở [SOURCE-MAP](SOURCE-MAP.md). Đọc trước, không apply tất cả.
- `tools/`: script lấy tên image, xem settings, nạp CLI credentials và chuẩn bị file local. prepare-files.sh không apply cluster.
- `reference/`: bản đầy đủ 05, 06, 07, 18, 19 và các nguồn Genestack chọn lọc. Không cần bản 05/19 bên ngoài. Tham khảo đúng ngữ cảnh mới/cũ; không chạy lại migration trên cụm đã chuyển xong.
- `workspace/`: bạn tự ghi override thực hành.
- `artifacts/`: snapshot/render/archive sinh ra khi học; không commit.

Không copy credentials của Talos/Kubernetes, TLS private key, SSH key hoặc render Secret vào Git. Chart local đã patch và dependencies đã được giữ trong assets/charts; chart Envoy ở assets/gateway-api/charts. Các tgz có trong assets/chart-archives. Config được chọn ở config/. Không cần giữ bản chụp bastion chỉ để đọc các asset này.

## Đã kiểm tra nguồn ngày 08/10/2026

Có local chart Nova/Neutron/Libvirt/Cinder/Glance/Horizon, hai chart Envoy và cache tgz các chart hạ tầng. Libvirt/Nova có patch Talos cần giữ. Horizon dùng cấu hình cuối HTTPS/CSRF/internalURL. before/current/rendered là snapshots/output, không ghép các bản sửa nối tiếp vào luồng dựng mới.

Chưa có bộ archive container images đầy đủ được đóng gói. Bài 04 dạy quy trình một image từ đầu tới cuối và cách kiểm kê toàn cụm, không coi folder này là bộ cài mới offline đã nghiệm thu. Việc tạo folder không thay đổi cluster.

CLI dùng hằng ngày: [10 — một file admin.sh](docs/10-Admin-Environment.md). Sau chuẩn bị một lần, chỉ source ~/osh-lab/bin/admin.sh để dùng OpenStack và Octavia qua Gateway.
