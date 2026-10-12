# Bắt đầu từ đây: dựng lại bằng file, học từng bước

Mục tiêu là dựng lại lab và biết mình đã làm gì. Không yêu cầu giữ dữ liệu DB/VM cũ. Bản private không phải đầu vào bắt buộc của việc học hoặc dựng cụm mới; folder này giữ chart/cấu hình để không phụ thuộc bản chụp bastion đã bị thu hồi.

**Dựng mới từ Kubernetes đã có:** theo [09 New Cluster](docs/09-New-Cluster.md). **Octavia tiếp theo:** theo [08 Octavia](docs/08-Octavia-Genestack.md). Không cần đọc bài cài Talos; không cần folder bastion bên ngoài để lấy chart/config đã giữ.

## 1. Chỗ nào là cấu hình chính?

| Chỗ | Vai trò | Có chạy trực tiếp không? |
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

## 2. Đưa file sang bastion mới

Copy folder sang ~/Openstack-Lab-Learning. Cài/chuẩn bị Helm3, kubectl, talosctl đúng Talos, Python3/PyYAML. Công cụ, container images và OS packages không tự có vì bạn clone Git.

Để tạo một thư mục làm việc mới từ assets/config, không đè ~/osh-lab hiện có:

```bash
bash ~/Openstack-Lab-Learning/tools/prepare-files.sh
```

Script in đường dẫn vừa tạo. Nó chỉ copy file/giải nén chart local, không cài cluster, không restore dữ liệu, không tải Internet. Đọc script để hiểu thao tác. Thư mục mới là nơi tập render; cần kubeconfig/talosconfig đúng cụm cho thao tác quản trị sau đó.

## 3. Thứ tự dựng lại về mặt kỹ thuật

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

Đây là bản đồ thứ tự, không phải một installer đã được chạy nghiệm thu trên cụm sạch. Các bài học hiện có hướng dẫn đầy đủ thực hành Helm/Horizon/image; chưa có một chuỗi lệnh tự động chạy 1–9 cho cụm mới. Nếu muốn copy-paste dựng hết, cần hoàn thiện từng bước và kiểm thử trên cụm sạch, đặc biệt credential/topology/OVN/Ceph sinh mới. Không dùng snapshot old credentials làm shortcut.

Các tài liệu gốc được lưu trong reference để học lại cách đã triển khai. File 05 là baseline đã từng dùng RabbitMQ Helm; file 06 là migration sang Operator sau đó. Chúng không phải hai bước vô hại để chạy lại trên cụm hiện tại.

## 4. Sau mỗi bước, mình cần biết năm điều

- File vừa tạo nằm ở đâu và ai đọc nó?
- Giá trị nào là defaults, giá trị nào do mình chọn?
- Lệnh chỉ đọc/render, hay thực sự thay đổi cluster/disk?
- Kết quả nào chứng minh bước đạt, kết quả nào chưa đủ?
- File nào cần giữ cho lần sửa sau, file nào chỉ là output có thể tạo lại?

Xem [giữ và xóa file](docs/07-Keep-or-Delete.md) trước khi dọn dung lượng. File chưa biết mục đích không cần giữ vĩnh viễn: phân loại và kiểm tra thay vì gom mọi thứ.

## CLI sau khi Gateway đã có

Dùng [admin.sh](docs/10-Admin-Environment.md): source một lần mỗi terminal, không gọi load_osh_admin hoặc port-forward ở luồng hằng ngày.
