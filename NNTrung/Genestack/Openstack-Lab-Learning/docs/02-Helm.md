# 02. Helm: một lệnh thực sự đọc và tạo gì?

```text
Chart.yaml + templates/ + values.yaml + -f distro.yaml + -f lab.yaml
  → helm template → YAML Kubernetes (render)
  → helm upgrade --install → release + tài nguyên trong cluster
  → Kubernetes controller / kubelet → pod / container
```

Helm giao tài nguyên cho Kubernetes, không chạy ứng dụng trên bastion. Chart có thể tạo init Job, Secret, Service, Deployment. Helm cũng có thể cài Operator; Operator tạo workload từ Custom Resource. Operator và Helm không phải hai cách loại trừ nhau.

## 1. Mổ lệnh đã dùng (đọc, không chạy lại trên cụm hiện tại)

```bash
helm upgrade --install glance openstack-helm/glance \
  --version '2026.1.39+dd5656a9c' -n openstack \
  -f ~/osh-lab/overrides/glance/2026.1-ubuntu_noble.yaml \
  -f ~/osh-lab/overrides/glance/lab-worker-pvc.yaml \
  --wait --timeout 15m
```

| Phần | Ý nghĩa |
|---|---|
| glance đầu tiên | Release name để get/history/upgrade |
| openstack-helm/glance | Chart từ repo alias; có thể cần mạng để tải |
| --version | Chọn chart, không thay thế distro/image overrides |
| -n | Namespace |
| -f distro | Đè defaults với lựa chọn OpenStack/Ubuntu |
| -f lab | Đè tiếp placement/PVC của lab |
| --wait | Chờ các tài nguyên hỗ trợ đạt ready; không test tạo VM |
| --timeout | Giới hạn chờ; timeout cần xem history/runtime |

Dùng path `~/osh-lab/charts/glance` thì version nằm trong Chart.yaml local; phải kiểm tra version đó. Chart có sẵn không đồng nghĩa node đã có image.

## 2. Merge values

Map gộp theo key: override `pod.replicas.api` giữ key worker không bị đè. List thay toàn bộ: thêm một list volumeMounts ở file sau có thể làm mất list file trước. Nova/socket cần so sánh cả template và mounts.

Sau RabbitMQ migration, upgrade lại baseline 05 có thể đưa endpoint cũ trở lại. Dùng cấu hình hiện tại và override nhỏ có mục đích.

## 3. Tra cứu

```bash
helm show chart ~/osh-lab/charts/horizon
helm show values ~/osh-lab/charts/horizon | less
helm get values horizon -n openstack -o yaml
helm history horizon -n openstack
helm status horizon -n openstack
```

show values = defaults chart. get values = user-supplied values; thêm --all = effective/computed values. Output có thể chứa password: xem riêng, không paste raw lên Git/chat. History failed không tự chứng minh tất cả runtime hỏng hoặc đã rollback.

## 4. Render để học, không thay đổi cluster

Điều kiện: Helm trên bastion, local chart và dependencies đã có.

```bash
export STUDY_ROOT="$HOME/Openstack-Lab-Learning"
export LAB_ROOT="$HOME/osh-lab"
umask 077
mkdir -p "$STUDY_ROOT/artifacts"
helm template horizon "$LAB_ROOT/charts/horizon" -n openstack \
  -f "$LAB_ROOT/overrides/horizon/2026.1-ubuntu_noble.yaml" \
  -f "$STUDY_ROOT/examples/horizon/https-final.yaml" \
  > "$STUDY_ROOT/artifacts/horizon-demo.yaml"
```

`>` ghi file, không cài. Đây là cấu hình mẫu để học, không dùng trực tiếp upgrade cụm hiện tại. Render Secret có base64, không phải mã hóa bảo mật. Tìm hostname trên YAML raw có thể không ra vì local_settings nằm trong Secret base64.

Nguồn: [Helm commands](https://helm.sh/docs/helm/), [helm upgrade](https://helm.sh/docs/helm/helm_upgrade/).
