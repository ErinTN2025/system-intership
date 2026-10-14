# 04. Quản lý container image và triển khai ngoại tuyến

## 1. Chart, image, archive và registry

| Loại tài nguyên | Ví dụ | Thành phần sử dụng |
|---|---|---|
| Helm chart | charts/horizon/ | Helm trên bastion |
| Container image | quay.io/airshipit/horizon:2026.1-ubuntu_noble | containerd trên node |
| Archive image | horizon.tar | Công cụ chuyển/nạp image; kubelet không tự đọc file này trên bastion |
| Registry | quay.io hoặc registry trong LAN | Node pull image qua giao thức registry |

Tên image có registry/repository/tag. `quay.io` là server; `airshipit/horizon` là repository; `2026.1-ubuntu_noble` là tag. Tag có thể thay đổi ở server; digest định danh nội dung manifest. Image là gói chương trình/libraries; container là tiến trình tạo từ image. Tải image không tải dữ liệu PVC/database.

Ví dụ image reference trong chart Horizon đã lưu trên bastion:

```yaml
images:
  tags:
    horizon: quay.io/airshipit/horizon:2026.1-ubuntu_noble
    horizon_db_sync: quay.io/airshipit/horizon:2026.1-ubuntu_noble
    db_init: quay.io/airshipit/openstack-client:2026.1-ubuntu_noble
    dep_check: quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_noble
```

Đổi mỗi horizon không đổi image của init Job/container. Đọc images.tags trong chart và bản render để hiểu key nào được dùng. Mất Internet mà pod đã chạy thì pod không tự dừng; pod mới có thể lỗi pull nếu thiếu cache hoặc pull policy yêu cầu liên hệ registry. Cache Docker trên bastion khác cache containerd của node.

## 2. Kiểm kê image của cụm

Trên bastion có kubectl trỏ đúng cụm:

```bash
export STUDY_ROOT="$HOME/Openstack-Lab-Learning"
bash "$STUDY_ROOT/tools/list-images.sh" "$STUDY_ROOT/artifacts/image-inventory"
```

Output là images-pods.txt, images-workloads.txt và images-observed.txt. Script chỉ đọc pod và các workload phổ biến, lấy cả init containers và ephemeral containers. Nó không tự tải image hoặc xuất Secret. images-pods.txt có image của pod Operator đã tạo như RabbitMQ/Ceph/Envoy.

Đây chưa phải danh sách đầy đủ cho cài từ đầu: Job cũ có thể đã bị xóa; controller có thể tạo workload mới; image Talos installer và image core Kubernetes có thể không xuất hiện trong workload list. Muốn đủ, kết hợp image trong render (kể cả Helm hooks), defaults/effective values, Operator spec, core images trên machine config và kiểm thử cold boot. Không copy machine config chứa secrets lên Git để kiểm kê.

## 3. Tải image và tạo archive

Thực hiện trên Ubuntu/Linux amd64 có Internet, có skopeo. Nếu chưa có, lệnh sau dùng Internet và cài công cụ trên máy tải, không chạy trên Talos:

```bash
sudo apt-get update
sudo apt-get install -y skopeo
```

Tải Horizon từ đúng registry đang dùng; không tải chart từ OpenDev để thay cho image:

```bash
export STUDY_ROOT="$HOME/Openstack-Lab-Learning"
mkdir -p "$STUDY_ROOT/artifacts/image-archives"
IMAGE='quay.io/airshipit/horizon:2026.1-ubuntu_noble'
skopeo inspect --override-os linux --override-arch amd64 "docker://$IMAGE" \
  > "$STUDY_ROOT/artifacts/image-archives/horizon-source.json"
skopeo --override-os linux --override-arch amd64 copy \
  "docker://$IMAGE" \
  "docker-archive:$STUDY_ROOT/artifacts/image-archives/horizon.tar:horizon:2026.1-ubuntu_noble"
(cd "$STUDY_ROOT/artifacts/image-archives" && sha256sum horizon.tar > horizon.tar.sha256)
```

docker:// là giao thức nói chuyện registry, không yêu cầu Docker daemon. docker-archive: là định dạng file image, không phải đường mạng. --override chọn Linux amd64 của lab, không tự biến image amd64 thành ARM. inspect lưu metadata nguồn, checksum kiểm tra file chuyển có bị hỏng. Tag mutable cần lưu digest metadata nếu muốn tái lập chính xác; copy qua định dạng archive không mặc định đảm bảo digest manifest nguồn và đích giống nhau.

Chuyển cả archive/checksum sang máy lab bằng USB hoặc LAN. Trên máy nhận:

```bash
cd ~/Openstack-Lab-Learning/artifacts/image-archives
sha256sum -c horizon.tar.sha256
```

Tới đây mới có file trên ổ đĩa, node Talos vẫn chưa dùng được nó.

## 4. Triển khai registry trong mạng nội bộ

Bài tập dùng bastion .138:5001 làm registry HTTPS. Chọn port 5001 để không trùng port-forward Keystone 5000. Đây là một dịch vụ mới, không phải phần cụm đang có. Cần bastion có Docker Engine hoạt động và skopeo/openssl, đủ disk, port 5001 chưa dùng và node kết nối tới .138. Không cài Docker lên Talos.

Nếu máy registry không có Internet, chuẩn bị image registry khi còn mạng:

```bash
mkdir -p ~/Openstack-Lab-Learning/artifacts/image-archives
skopeo --override-os linux --override-arch amd64 copy \
  docker://docker.io/library/registry:3 \
  docker-archive:$HOME/Openstack-Lab-Learning/artifacts/image-archives/registry.tar:registry:3
```

Chuyển registry.tar sang bastion và nạp vào Docker cache. Công cụ Docker/skopeo và gói phụ thuộc phải được chuẩn bị trước nếu máy chưa có Internet; có registry.tar không tự cài Docker Engine.

```bash
sudo docker load -i ~/Openstack-Lab-Learning/artifacts/image-archives/registry.tar
umask 077
mkdir -p ~/registry-lab/{data,tls}
openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 365 \
  -keyout ~/registry-lab/tls/registry.key -out ~/registry-lab/tls/registry.crt \
  -subj '/CN=registry-lab' -addext 'subjectAltName=IP:192.168.207.138' \
  -addext 'basicConstraints=critical,CA:TRUE'
sudo docker run -d --name study-registry --restart=unless-stopped \
  -p 5001:5000 \
  -v "$HOME/registry-lab/data:/var/lib/registry" \
  -v "$HOME/registry-lab/tls:/certs:ro" \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/registry.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/registry.key \
  -e OTEL_TRACES_EXPORTER=none \
  registry:3
curl --cacert ~/registry-lab/tls/registry.crt https://192.168.207.138:5001/v2/
```

/v2/ trả {} với HTTP 200 chứng minh registry endpoint đáp ứng, chưa chứng minh có Horizon image. Volume data lưu image qua restart. Cert/key riêng cho registry, không dùng nhầm wildcard-lab-tls của dashboard. Registry thử này chưa có user/password/access control: chỉ đặt trong LAN lab kiểm soát được, không expose public. Nếu tên container tồn tại, inspect nó trước; không tự xóa data để chạy lại.

## 5. Nhập image vào registry nội bộ

Trên bastion có archive Horizon:

```bash
skopeo copy --dest-cert-dir "$HOME/registry-lab/tls" \
  "docker-archive:$HOME/Openstack-Lab-Learning/artifacts/image-archives/horizon.tar" \
  docker://192.168.207.138:5001/quay.io/airshipit/horizon:2026.1-ubuntu_noble
skopeo inspect --cert-dir "$HOME/registry-lab/tls" \
  docker://192.168.207.138:5001/quay.io/airshipit/horizon:2026.1-ubuntu_noble
```

Ở registry local, quay.io là một phần tên repository để tránh trùng image cùng tên từ hai registry gốc. Đây là quy ước đặt tên repository; nó không tự thiết lập cơ chế mirror. Kiểm tra image đích bằng inspect xác nhận metadata và kiến trúc của image đã nhập.

## 6. Cấu hình CA của registry trên Talos

TLS certificate tự ký phải được node tin. Docker/skopeo trên bastion tin không có nghĩa Talos tin. Tạo patch riêng (có thay đổi machine config khi áp dụng):

```bash
python3 - <<'PY'
from pathlib import Path
import yaml
cert = (Path.home() / 'registry-lab/tls/registry.crt').read_text()
patch = {'machine': {'registries': {'config': {
    '192.168.207.138:5001': {'tls': {'ca': cert}}
}}}}
p = Path.home() / 'Openstack-Lab-Learning/workspace/registry-ca.yaml'
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(yaml.safe_dump(patch, sort_keys=False))
print('Da ghi ' + str(p) + '; chua patch node')
PY
```

Đọc patch và đối chiếu config registry đang có trước khi áp dụng cho từng node. Chỉ dùng talosconfig của đúng cụm:

```bash
talosctl -n 192.168.207.137 patch machineconfig \
  --patch "@$HOME/Openstack-Lab-Learning/workspace/registry-ca.yaml"
talosctl -n 192.168.207.139 patch machineconfig \
  --patch "@$HOME/Openstack-Lab-Learning/workspace/registry-ca.yaml"
```

Không bỏ verification bằng insecureSkipVerify chỉ để tránh đọc lỗi cert. Patch CA không tải image, không đổi image của pod, và không mở đường mạng nếu node không tới được .138:5001. Đây là ví dụ patch v1alpha1 machine registries; kiểm tra schema/CLI đúng Talos 1.13.10 của lab trước khi thực hành.

## 7. Cấu hình Horizon sử dụng registry nội bộ

File mẫu `examples/horizon/local-image.yaml` đổi cả horizon và horizon_db_sync sang repository local vừa nạp. Đọc file đó rồi dùng như override cuối cùng trong bài 03. Trong bước render/upgrade, thêm:

```bash
-f "$STUDY_ROOT/examples/horizon/local-image.yaml"
```

Dòng -f là tham số bổ sung vào lệnh Helm đầy đủ, không phải lệnh độc lập. Sau render, đối chiếu image trong Deployment/Job. Sau upgrade, xem pods/events; ImagePullBackOff là triệu chứng, describe pod cho biết thiếu image, sai CA, sai repository hay network.

```bash
kubectl -n openstack get pods -l application=horizon
kubectl -n openstack describe pod -l application=horizon
```

Bài tập chỉ chuyển hai key dùng image Horizon. DB init/dep_check/other image vẫn có thể đi registry public. Muốn offline toàn chart phải tải và đổi tất cả image thực sự cần, gồm hooks/jobs/init; muốn toàn cụm còn cần hạ tầng/Operator/Kubernetes/Talos.

## 8. Registry mirror và image override

Đổi values: pod spec nhìn thấy `192.168.207.138:5001/quay.io/airshipit/horizon:...`. Chỉ ảnh hưởng những key đã đổi.

Mirror Talos: pod spec vẫn có quay.io/... nhưng containerd chuyển request tới mirror. Mirror phải có đúng repository mapping; registry ở bước 5 chưa tự thỏa mapping mirror mặc định vì có prefix quay.io. Vì thế bài này dùng đổi values trực tiếp, không chép một mirror patch không khớp dữ liệu.

Khi học cài offline toàn cụm, mirror là phương án giảm sửa mọi chart nhưng cần thiết kế namespace từng upstream và xử lý fallback Internet. Talos upstream có hướng dẫn air-gapped; không coi chỉ thêm endpoint mirror là đã đóng gói đủ image.

## 9. Phụ thuộc mạng khi vận hành và triển khai

Mất Wi-Fi kết nối LAN: laptop không vào dashboard; cluster có thể vẫn chạy. LAN còn nhưng Internet mất: ứng dụng đã chạy và API nội bộ có thể tiếp tục. Registry local cần bastion/host registry chạy nếu node phải pull lại. Helm local chỉ tránh tải chart; nó không làm image public tự xuất hiện. Tạo VM dùng Glance image đã upload khác tải VM image từ Internet. NTP/DNS/discovery ngoài LAN và công cụ bootstrap cũng cần tính trong cài mới offline.

## Nguồn

- [Skopeo copy](https://github.com/containers/skopeo/blob/main/docs/skopeo-copy.1.md).
- [CNCF Distribution registry](https://distribution.github.io/distribution/about/deploying/).
- [Talos air-gapped](https://docs.siderolabs.com/talos/v1.10/platform-specific-installations/air-gapped): nguyên lý tham khảo; đối chiếu phiên bản Talos lab trước khi dùng cấu hình.
