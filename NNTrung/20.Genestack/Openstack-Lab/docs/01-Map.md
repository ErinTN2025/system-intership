# 01. Kiến trúc cụm và nguồn cấu hình

| Thành phần | Chức năng | Phạm vi quản trị |
|---|---|---|
| Bastion Ubuntu | Chạy talosctl/kubectl/Helm, lưu file | Sửa chart/values, render, gửi lệnh tới cluster |
| controlplane-01 .137 | Kubernetes control plane và nhiều service | Machine config, scheduling, storage |
| workerplane-01 .139 | Compute/KVM và disk Ceph | Libvirt, OVS, Nova compute, Rook |
| Talos | OS node, không SSH/apt như Ubuntu | Dùng talosctl và machine config |
| Kubernetes | Lưu tài nguyên, điều khiển pod/Service | kubectl get/apply/describe/logs |
| Helm | Chart + values thành tài nguyên | template/upgrade/get/history |
| Genestack | Repo cấu hình, workflow và công cụ | Học cách quy hoạch; không phải daemon tự chạy trên node |

## 1. Luồng truy cập dashboard

```mermaid
flowchart LR
 B[Browser horizon.lab.test:31384] --> E[Envoy NodePort HTTPS]
 E --> S[horizon-int:80]
 S --> H[Horizon Pod]
 H --> K[Keystone internal v3]
 H --> N[Neutron internal 9696]
 H --> O[Nova / Glance / Cinder internal]
```

TLS kết thúc tại Envoy. Horizon nhận HTTP phía sau proxy, dùng forwarded header để hiểu client đi HTTPS. HTTPRoute chọn backend; không tự sửa Keystone catalog. Catalog là danh sách URL Horizon/CLI dùng để tìm API.

## 2. Tệp cấu hình Horizon

| File trên bastion | Ý nghĩa |
|---|---|
| charts/horizon/Chart.yaml | Tên/version chart; khác version ứng dụng |
| charts/horizon/values.yaml | Defaults |
| charts/horizon/templates/ | Mẫu Deployment/Job/Secret/Service |
| overrides/horizon/2026.1-ubuntu_noble.yaml | Image/distro overrides |
| gateway-api/horizon/https-values.yaml | Cấu hình cuối HTTPS/CSRF theo NodePort và endpoint_type=internalURL |
| config/overrides/horizon/https-final.yaml trong folder học | Bản cuối đã gộp; chỉnh hostname/origin theo môi trường |
| gateway-api/horizon/current-before-interface.yaml | Snapshot riêng của một lần sửa, có thể chứa credentials; không là nguồn cố định |
| gateway-api/horizon/internal-endpoint-rendered.yaml | Output xem trước; không phải input chính |

Tất cả đường dẫn trên dưới `~/osh-lab`. File before/current không tự đồng bộ với cluster. Chart/template/config local là nguồn mong muốn; tài nguyên cluster là trạng thái thực tế. Patch trực tiếp Deployment có thể chưa được ghi về file.

## 3. Phân loại nguồn cấu hình và trạng thái triển khai

Quá trình triển khai tạo ra cấu hình VXLAN, OVN dùng chung, chuyển đổi RabbitMQ và HTTPS tại các thời điểm khác nhau. Cấu hình đang có hiệu lực được phân biệt với snapshot, manifests đã render và các phương án thử nghiệm đã ngừng sử dụng. Helm values, manifests Kubernetes và cấu hình Talos có công cụ thực thi khác nhau, dù cùng sử dụng định dạng YAML.

```bash
# Chỉ đọc: context, node, release, workload và storage
kubectl config current-context
kubectl get nodes -o wide
helm list -A
kubectl -n openstack get deployments,statefulsets,daemonsets
kubectl -n openstack get svc,pvc
```

helm list không liệt kê mọi tài nguyên: RabbitmqCluster/HTTPRoute tạo bằng kubectl vẫn tồn tại. Deployment/StatefulSet/DaemonSet duy trì pod; pod không phải nơi lưu cấu hình lâu dài.
