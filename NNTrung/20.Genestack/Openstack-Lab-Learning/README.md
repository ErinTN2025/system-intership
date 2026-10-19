# Triển khai và vận hành OpenStack trên Talos

## 1. Cấu trúc nội dung

| Tài liệu | Nội dung |
|---|---|
| [01. Kiến trúc cụm](docs/01-Map.md) | Kiến trúc cụm và vai trò của các nguồn cấu hình |
| [02. Helm và vòng đời release](docs/02-Helm.md) | Chart, values, manifests và vòng đời release |
| [03. Quản lý thay đổi](docs/03-Change.md) | Quy trình thay đổi cấu hình và kiểm tra Horizon |
| [04. Image và triển khai ngoại tuyến](docs/04-Images.md) | Quản lý image, registry và triển khai ngoại tuyến |
| [05. Quản lý cấu hình trong Git](docs/05-Git.md) | Tổ chức cấu hình trong Git và phân tách thông tin xác thực |
| [06. Chẩn đoán sự cố](docs/06-Debug.md) | Chẩn đoán sự cố theo luồng yêu cầu |
| [07. Chính sách lưu trữ](docs/07-Keep-or-Delete.md) | Phân loại cấu hình, dữ liệu ứng dụng và tệp tạm |
| [08. Octavia và Horizon](docs/08-Octavia-Genestack.md) | Quy trình cuối Octavia OVN, Gateway, CLI và tạo LB; lý do cấu hình |
| [09. Triển khai cụm mới](docs/09-New-Cluster.md) | Trình tự triển khai trên Kubernetes và các tham số môi trường |
| [10. Môi trường OpenStack CLI](docs/10-Admin-Environment.md) | Thông tin xác thực và endpoint API qua Gateway |
| [11. Phiên bản Horizon](docs/11.ChangeHorizonversion.md) | Quy trình đổi image, kiểm tra phiên bản và hồ sơ triển khai |

## 2. Quy ước đường dẫn và môi trường thực thi

Thư mục repository được đặt tại `~/Openstack-Lab-Learning` trên bastion Linux. Các ví dụ sử dụng hai biến đường dẫn sau:

```bash
export STUDY_ROOT="$HOME/Openstack-Lab-Learning"
export LAB_ROOT="$HOME/osh-lab"
```

STUDY_ROOT trỏ đến bộ tài liệu và ví dụ; LAB_ROOT trỏ đến chart cùng cấu hình triển khai trên bastion. Script tools/prepare-files.sh tạo thư mục làm việc từ các tài nguyên đã lưu khi cần chuẩn bị một bastion mới. Các thao tác đọc chart và render có thể thực hiện độc lập với cụm; kubectl và helm get yêu cầu kết nối đến Kubernetes.

Các khối Bash được thực hiện trên Linux. Bản chụp thư mục bastion trong workspace Windows là dữ liệu lưu trữ, không phải môi trường thực thi đang phục vụ cụm.

## 3. Cấu trúc thư mục

- `docs/`: giải thích theo thứ tự.
- `examples/`: bản sao chọn lọc từ bastion; mỗi file có nguồn ở [SOURCE-MAP](SOURCE-MAP.md). Đọc trước, không apply tất cả.
- `tools/`: script lấy tên image, xem settings, nạp CLI credentials và chuẩn bị file local. prepare-files.sh không apply cluster.
- `reference/`: bản đầy đủ 05, 06, 07, 18, 19 và các nguồn Genestack chọn lọc. Không cần bản 05/19 bên ngoài. Tham khảo đúng ngữ cảnh mới/cũ; không chạy lại migration trên cụm đã chuyển xong.
- `workspace/`: nơi lưu override đang xây dựng hoặc kiểm tra.
- `artifacts/`: snapshot/render/archive sinh ra khi học; không commit.

Không copy credentials của Talos/Kubernetes, TLS private key, SSH key hoặc render Secret vào Git. Chart local đã patch và dependencies đã được giữ trong assets/charts; chart Envoy ở assets/gateway-api/charts. Các tgz có trong assets/chart-archives. Config được chọn ở config/. Không cần giữ bản chụp bastion chỉ để đọc các asset này.

## 4. Phạm vi dữ liệu đã lưu

Các assets ban đầu được kiểm kê ngày 08/10/2026. Phần tích hợp Octavia Dashboard được nghiệm thu ngày 13/10/2026 và trình bày tại chương 08. Chart Horizon có sửa script khởi động và image một layer của lần nghiệm thu này được quản lý theo chương 08; chart nền trong assets không tự bao gồm mọi thay đổi phát sinh sau lần kiểm kê.

Có local chart Nova/Neutron/Libvirt/Cinder/Glance/Horizon, hai chart Envoy và cache tgz các chart hạ tầng. Libvirt/Nova có patch Talos cần giữ. Horizon dùng cấu hình cuối HTTPS/CSRF/internalURL. before/current/rendered là snapshots/output, không ghép các bản sửa nối tiếp vào luồng dựng mới.

Bộ tài liệu chưa bao gồm archive đầy đủ của toàn bộ container image. Chương 04 trình bày quy trình quản lý một image và phương pháp kiểm kê image toàn cụm. Vì vậy, thư mục này chưa được nghiệm thu như một bộ cài ngoại tuyến hoàn chỉnh.

Môi trường CLI được trình bày tại [10 — một file admin.sh](docs/10-Admin-Environment.md). Sau chuẩn bị một lần, chỉ source ~/osh-lab/bin/admin.sh để dùng OpenStack và Octavia qua Gateway.
