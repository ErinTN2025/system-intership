# Hướng dẫn sử dụng bộ tài liệu triển khai

Bộ tài liệu lưu kiến trúc, chart, cấu hình và quy trình triển khai của cụm thử nghiệm. Mục tiêu là tái tạo cấu hình trên một cụm mới và xác định chức năng của từng thành phần. Phục hồi dữ liệu cơ sở dữ liệu hoặc máy ảo từ cụm cũ là một quy trình riêng, không phải điều kiện bắt buộc của luồng dựng mới.

**Dựng mới từ Kubernetes đã có:** theo [09 New Cluster](docs/09-New-Cluster.md). **Octavia tiếp theo:** theo [08 Octavia](docs/08-Octavia-Genestack.md). Không cần đọc bài cài Talos; không cần folder bastion bên ngoài để lấy chart/config đã giữ.

## 1. Nguồn cấu hình triển khai

| Vị trí | Chức năng | Công cụ sử dụng |
|---|---|---|
| assets/charts/ | Chart OpenStack local, giữ patch Talos và dependencies | Helm đọc |
| assets/gateway-api/charts/ | Chart Envoy controller và CRD | Helm đọc |
| assets/chart-archives/ | Các tgz pin version, dùng khi chưa có chart unpacked | Helm đọc hoặc tar giải nén |
| config/overrides/ | Distro và cấu hình riêng đã chọn từ bastion | Tham số -f của Helm |
| config/operators/ | Controller manifests, RabbitmqCluster và endpoint override | Controller/CR dùng kubectl; endpoint override dùng Helm |
| config/gateway/ | Cấu hình cuối HTTPS và route API/Horizon | kubectl; controller-values là Helm values |
| config/talos/ | Patch node/network/storage | talosctl, không kubectl |
| docs/ | Giải thích và bài thực hành | Đọc theo README |
| examples/ | Bản nhỏ để học khái niệm | Không apply cả thư mục |
| reference/ | Hướng dẫn triển khai cuối và nguồn tham khảo | Đọc đúng ngữ cảnh, không chạy tất cả |

Trong config có IP/node/disk lab cũ. Khi dựng mới phải đối chiếu chúng, không áp dụng nguyên xi trên một cụm khác. Nova có cả talos-lab và shared-ovn: list mounts thay toàn bộ, cần so sánh render, không coi hai file này đã được hợp nhất đúng chỉ vì cùng tồn tại.

## 2. Chuẩn bị thư mục trên bastion

Mã nguồn được đặt tại ~/Openstack-Lab-Learning trên bastion. Môi trường thực thi gồm Helm 3, kubectl, talosctl tương thích với node, Python3 và PyYAML. Việc sao chép repository chỉ cung cấp các tệp đã lưu; công cụ, container image và gói hệ điều hành được chuẩn bị riêng.

Để tạo một thư mục làm việc mới từ assets/config, không đè ~/osh-lab hiện có:

```bash
bash ~/Openstack-Lab-Learning/tools/prepare-files.sh
```

Script in đường dẫn thư mục vừa tạo, sao chép cấu hình và giải nén chart local. Nó không triển khai workload, phục hồi dữ liệu hoặc tải tài nguyên từ Internet. Thư mục kết quả phục vụ render và chuẩn bị triển khai; thao tác quản trị tiếp theo yêu cầu kubeconfig/talosconfig của cụm đích.

## 3. Trình tự triển khai hạ tầng và dịch vụ

| Bước | Làm gì và vì sao | Phần phụ thuộc môi trường |
|---|---|---|
| 1 | Tạo VM/nested virtualization, Talos/Kubernetes | IP, NIC, disk, image nền, thời gian/NTP |
| 2 | CNI Kube-OVN để pod có mạng | Path writable trên Talos, node IP/NIC |
| 3 | User volumes + local-path provisioner | Disk sdb đúng node, đường mount, dung lượng thật |
| 4 | MariaDB/Memcached và RabbitMQ Operator/cluster/topology | Credentials mới, PVC, scheduling |
| 5 | Keystone/Placement/Glance | DB init, users, catalog, Glance storage |
| 6 | Shared OVN + Libvirt + Neutron + Nova | KVM/socket, NB/SB IP mới, metadata/provider network |
| 7 | Rook/Ceph/Cinder và libvirt Ceph key | Worker sdc dành riêng, FSID/key/MON mới |
| 8 | Horizon + Envoy Gateway/HTTPS | Host/NodePort/CSRF/interface, certificate mới |
| 9 | Test API, VM, volume, console | Không suy ra runtime OK từ render/Helm deployed |
| 10 | Octavia OVN → Gateway → LB | Bài 08 dùng cấu hình cuối; backend/traffic cần nghiệm thu riêng |

Bảng trên xác định thứ tự phụ thuộc giữa các thành phần, chưa phải bộ cài tự động đã được nghiệm thu trên cụm sạch. Các chương cung cấp quy trình Helm, Horizon và image; việc dựng mới toàn bộ cần nghiệm thu các bước tạo thông tin xác thực, topology RabbitMQ, OVN và Ceph trong môi trường đích. Snapshot thông tin xác thực của cụm cũ không thay thế quá trình chuẩn bị này.

Các tài liệu gốc được lưu trong reference để học lại cách đã triển khai. File 05 là baseline đã từng dùng RabbitMQ Helm; file 06 là migration sang Operator sau đó. Chúng không phải hai bước vô hại để chạy lại trên cụm hiện tại.

## 4. Hồ sơ cấu hình và tiêu chí kiểm tra

- Vị trí tệp đầu vào và thành phần sử dụng tệp.
- Giá trị mặc định và các tham số được điều chỉnh cho môi trường.
- Tác động của lệnh: đọc, render, thay đổi tài nguyên hoặc ghi dữ liệu lên disk.
- Kết quả kiểm tra và giới hạn của bằng chứng nghiệm thu.
- Tệp nguồn cần lưu và dữ liệu đầu ra có thể tạo lại.

Xem [giữ và xóa file](docs/07-Keep-or-Delete.md) trước khi dọn dung lượng. Việc lưu trữ dựa trên chức năng và khả năng tái tạo của từng loại tệp.

## 5. Môi trường CLI sau khi triển khai Gateway

Dùng [admin.sh](docs/10-Admin-Environment.md): source một lần mỗi terminal, không gọi load_osh_admin hoặc port-forward ở luồng hằng ngày.
