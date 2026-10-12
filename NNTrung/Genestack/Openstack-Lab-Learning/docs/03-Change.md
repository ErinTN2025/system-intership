# 03. Tự sửa Horizon mà biết mình đang làm gì

## 1. Phân loại trước khi sửa

| Muốn đổi | Sửa ở đâu | Công cụ áp dụng |
|---|---|---|
| allowed_hosts, CSRF, endpoint_type, image, replicas | Helm values override | Helm |
| Template mount/socket Talos không có key values | Chart local templates | Helm với chart đã patch |
| hostname/backend/listener của Gateway | Gateway/HTTPRoute manifest | kubectl apply |
| OS disk/node IP/registry CA | Talos machine config/patch | talosctl |
| Python code của Horizon | Source code → build image mới → image override | Build tool + Helm |

Đừng sửa file trong container để lưu lâu dài. Pod mới dùng lại image/config được controller tạo; sửa tay có thể mất. Đừng patch Deployment rồi quên ghi về values/chart: Helm upgrade có thể đè patch.

## 2. Bài tập: chọn internalURL cho Horizon

Cụm đã có internalURL, nên ví dụ này có thể không tạo khác biệt về hành vi. Mục tiêu là hiểu quy trình. Không chạy upgrade chỉ để học nếu chỉ cần render. Ví dụ này chỉ dành cho cụm hiện tại với local chart cùng version release.

Chạy các bước A–D trong cùng shell để giữ CHANGE_DIR/STUDY_ROOT/LAB_ROOT. Nếu mở shell mới, đặt lại biến trỏ đúng thư mục đã chụp trước khi tiếp tục.

### Bước A: lưu trạng thái, chỉ đọc cluster

```bash
export STUDY_ROOT="$HOME/Openstack-Lab-Learning"
export LAB_ROOT="$HOME/osh-lab"
umask 077
CHANGE_DIR="$STUDY_ROOT/artifacts/horizon-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$CHANGE_DIR" "$STUDY_ROOT/workspace/horizon"
helm list -n openstack --filter '^horizon$'
helm show chart "$LAB_ROOT/charts/horizon"
helm get values horizon -n openstack --all -o yaml > "$CHANGE_DIR/current.yaml"
helm history horizon -n openstack > "$CHANGE_DIR/history.txt"
```

So sánh chart version trong release và Chart.yaml. current.yaml giữ các cấu hình HTTPS/DB/Keystone hiện tại; có thể chứa credentials. history giúp biết revision trước thay đổi. Snapshot này không backup database/PVC.

### Bước B: tạo thay đổi nhỏ, chưa đổi cluster

```bash
cp "$STUDY_ROOT/examples/horizon/internal-endpoint-values.yaml" \
  "$STUDY_ROOT/workspace/horizon/change.yaml"
cat "$STUDY_ROOT/workspace/horizon/change.yaml"
```

Nội dung có một đường key:

```yaml
conf:
  horizon:
    local_settings:
      config:
        endpoint_type: internalURL
```

Trong Horizon, internalURL là định dạng dùng để chọn endpoint internal. Không suy diễn mọi phần mềm OpenStack đều dùng cùng chuỗi: CLI dùng --interface internal. Lỗi từng gặp của lab: endpoint_type=internal, Horizon lại gọi URL public Neutron không có Service, /project/ trả 500. Catalog internal đã đúng nên không cần sửa URL đó.

### Bước C: render bằng đúng chart và đúng thứ tự file

```bash
helm template horizon "$LAB_ROOT/charts/horizon" -n openstack --is-upgrade \
  -f "$CHANGE_DIR/current.yaml" \
  -f "$STUDY_ROOT/workspace/horizon/change.yaml" \
  > "$CHANGE_DIR/rendered.yaml"
python3 "$STUDY_ROOT/tools/show-horizon-settings.py" "$CHANGE_DIR/rendered.yaml"
```

Script chỉ hiện các dòng settings về host/HTTPS/interface đã chọn, không dump toàn Secret. Cần Python3 + PyYAML (bastion đã dùng trong các bước cũ). Không tìm bằng grep raw vì settings có thể nằm trong Secret base64. Render tốt mới chứng minh template tạo được output, chưa chứng minh ứng dụng chạy.

### Bước D: áp dụng, có thay đổi cluster

Chỉ chạy sau khi bạn đã xem output, chart cùng version và biết revision hiện tại. Lệnh dùng đúng hai file vừa render:

```bash
helm upgrade horizon "$LAB_ROOT/charts/horizon" -n openstack \
  -f "$CHANGE_DIR/current.yaml" \
  -f "$STUDY_ROOT/workspace/horizon/change.yaml" \
  --wait --wait-for-jobs --timeout 15m
kubectl -n openstack rollout status deployment/horizon --timeout=180s
helm history horizon -n openstack
```

Job có thể chạy lại khi upgrade. Đừng lặp lệnh lúc release đang pending; xem status/jobs trước. Mở lại browser HTTPS, đăng xuất/đăng nhập nếu cần lấy session/catalog mới rồi test panel. Pod Ready không thay thế test panel.

### Bước E: giữ thay đổi làm cấu hình chính

Đưa nội dung change.yaml vào bộ overrides chính sau khi đã xác nhận đúng, rồi commit phần cấu hình không có credentials. Lần sửa sau chụp current mới; không mãi dùng snapshot hôm nay. Đổi image code cần tag/digest mới và registry có image đó.

## 3. Nếu chỉ muốn restart

```bash
kubectl -n openstack rollout restart deployment/horizon
kubectl -n openstack rollout status deployment/horizon --timeout=180s
```

Restart thay pod nhưng không đổi values, không build code, không sửa endpoint sai. Chỉ dùng khi thực sự cần. Rollback Helm phải chọn revision cụ thể trong history và kiểm tra thay đổi DB/hook; không rollback mù về revision cũ có cấu hình không còn tương thích.

Tham khảo [Horizon settings](https://docs.openstack.org/horizon/2026.1/configuration/settings.html).
