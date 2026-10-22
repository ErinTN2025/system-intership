# 03. Quản lý thay đổi cấu hình Horizon

Các lệnh dưới đây minh họa thay đổi endpoint trên chart nền của giai đoạn trước khi bổ sung Octavia Dashboard. Đối với Horizon đã tích hợp plugin, nguồn chart phải là bản đã sửa script khởi động theo [chương 08](08-Octavia-Genestack.md); sử dụng lại chart nền có thể ghi đè phần sửa đó.

## 1. Nguồn cấu hình và công cụ cập nhật

| Thành phần thay đổi | Nguồn cấu hình | Công cụ áp dụng |
|---|---|---|
| allowed_hosts, CSRF, endpoint_type, image, replicas | Helm values override | Helm |
| Template mount/socket Talos không có key values | Chart local templates | Helm với chart đã patch |
| hostname/backend/listener của Gateway | Gateway/HTTPRoute manifest | kubectl apply |
| OS disk/node IP/registry CA | Talos machine config/patch | talosctl |
| Python code của Horizon | Source code → build image mới → image override | Build tool + Helm |

Image và cấu hình workload là nguồn tạo pod mới. Sửa trực tiếp tệp trong container không bảo đảm thay đổi được giữ sau khi pod được tạo lại. Các thay đổi Deployment được phản ánh trong chart/values để không bị lần Helm upgrade tiếp theo ghi đè.

## 2. Quy trình cập nhật endpoint nội bộ

Cụm đã có internalURL, nên ví dụ này có thể không tạo khác biệt về hành vi. Mục tiêu là hiểu quy trình. Không chạy upgrade chỉ để học nếu chỉ cần render. Ví dụ này chỉ dành cho cụm hiện tại với local chart cùng version release.

Các mục 2.1–2.5 sử dụng cùng phiên shell để duy trì CHANGE_DIR, STUDY_ROOT và LAB_ROOT. Nếu mở shell mới, đặt lại biến trỏ đúng thư mục đã chụp trước khi tiếp tục.

### 2.1. Lưu cấu hình và lịch sử release

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

### 2.2. Chuẩn bị override

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

### 2.3. Render và kiểm tra cấu hình

```bash
helm template horizon "$LAB_ROOT/charts/horizon" -n openstack --is-upgrade \
  -f "$CHANGE_DIR/current.yaml" \
  -f "$STUDY_ROOT/workspace/horizon/change.yaml" \
  > "$CHANGE_DIR/rendered.yaml"
python3 "$STUDY_ROOT/tools/show-horizon-settings.py" "$CHANGE_DIR/rendered.yaml"
```

Script chỉ hiện các dòng settings về host/HTTPS/interface đã chọn, không dump toàn Secret. Cần Python3 + PyYAML (bastion đã dùng trong các bước cũ). Không tìm bằng grep raw vì settings có thể nằm trong Secret base64. Render tốt mới chứng minh template tạo được output, chưa chứng minh ứng dụng chạy.

### 2.4. Áp dụng thay đổi

Điều kiện áp dụng gồm kết quả render đã kiểm tra, chart cùng phiên bản release và revision trước thay đổi đã được ghi nhận. Lệnh sử dụng cùng hai tệp values ở bước render:

```bash
helm upgrade horizon "$LAB_ROOT/charts/horizon" -n openstack \
  -f "$CHANGE_DIR/current.yaml" \
  -f "$STUDY_ROOT/workspace/horizon/change.yaml" \
  --wait --wait-for-jobs --timeout 15m
kubectl -n openstack rollout status deployment/horizon --timeout=180s
helm history horizon -n openstack
```

Job có thể được thực thi lại khi upgrade. Release đang pending được kiểm tra qua status và trạng thái Job trước khi thực hiện thêm thao tác. Sau rollout, đăng nhập Horizon qua HTTPS để kiểm tra các panel; pod Ready không thay thế nghiệm thu chức năng giao diện.

### 2.5. Cập nhật nguồn cấu hình

Đưa nội dung change.yaml vào bộ overrides chính sau khi đã xác nhận đúng, rồi commit phần cấu hình không có credentials. Lần sửa sau chụp current mới; không mãi dùng snapshot hôm nay. Đổi image code cần tag/digest mới và registry có image đó.

## 3. Khởi động lại workload

```bash
kubectl -n openstack rollout restart deployment/horizon
kubectl -n openstack rollout status deployment/horizon --timeout=180s
```

Restart thay pod nhưng không đổi values, không build code, không sửa endpoint sai. Chỉ dùng khi thực sự cần. Rollback sử dụng revision được xác định từ lịch sử và đánh giá tác động của hook hoặc thay đổi cơ sở dữ liệu. Revision cũ có thể chứa cấu hình không còn tương thích với trạng thái hiện tại.

Tham khảo [Horizon settings](https://docs.openstack.org/horizon/2026.1/configuration/settings.html).
