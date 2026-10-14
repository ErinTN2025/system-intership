# 09. Triển khai OpenStack trên cụm Kubernetes mới

## 1. Phạm vi và điểm bắt đầu

Quy trình bắt đầu từ cụm Kubernetes đã hoạt động, có kubeconfig/talosconfig hợp lệ và các node cùng disk chuyên dụng đã được chuẩn bị. Không dùng credentials của cụm cũ để sinh cụm mới. Folder này có bản đầy đủ [05 triển khai nền](../reference/05.Openstackhelm.md), [06 RabbitMQ Operator](../reference/06.OpenstackOperatorMigration.md), [19 Gateway/Horizon](../reference/19.Gateway.md) và các chart/config cần giữ từ bastion. Xóa bản gốc ở ngoài không làm mất ba tài liệu này.

Luồng tái tạo dưới đây giữ quá trình đã làm và giải thích chỗ cần chỉnh cho cụm mới; chưa được chạy từ đầu tới cuối trên một cụm sạch. Không coi trạng thái deployed/Ready ghi trong tài liệu nguồn là kết quả của cluster mới.

Điều kiện lab tham chiếu: controlplane-01 + workerplane-01, amd64, nested virtualization/KVM trên worker, CNI Kube-OVN, disk OS riêng, disk local-path riêng, worker sdc dành riêng Ceph. Đổi topology/IP/NIC/disk cần chỉnh file tương ứng trước apply. Cần đủ tài nguyên thực tế cho OpenStack và VM; cấu hình nhỏ của lab không có HA.

## 2. Chuẩn bị thư mục triển khai trên bastion

Copy folder từ Git sang ~/Openstack-Lab-Learning. Chuẩn bị Bash, Helm3, kubectl, talosctl đúng phiên bản, Python3/PyYAML và OpenStack CLI trên Ubuntu. Công cụ không nằm trong archive chart. Online là luồng mặc định; offline đọc bài 04 để chuẩn bị đầy đủ images/tools trước.

```bash
bash ~/Openstack-Lab-Learning/tools/prepare-files.sh "$HOME/osh-lab"
```

Lệnh dừng nếu ~/osh-lab đã tồn tại, không ghi đè folder đang dùng. Nó copy assets/config và giải nén chart tgz còn thiếu; chart đã patch được ưu tiên. Không apply lên cluster. Thư mục ~/osh-lab mới được dùng thống nhất trong các tài liệu nguồn để đỡ phải sửa mọi đường dẫn.

Kiểm tra chỉ đọc:

```bash
kubectl config current-context
kubectl get nodes -o wide
helm list -A
kubectl -n kube-system get pods
kubectl -n kube-system get svc ovn-nb ovn-sb
helm show chart ~/osh-lab/charts/libvirt
helm show chart ~/osh-lab/charts/nova
```

## 3. Kiểm tra mạng và storage

CNI phải hoạt động, NB/SB Service tồn tại. Bản chart Kube-OVN tgz có trong assets/chart-archives; shared-ovn override có ở config/overrides/kube-ovn. Talos writable paths /var/lib/ovn và /var/lib/openvswitch cần khớp cấu hình CNI; không dùng defaults /etc/origin trên Talos.

Các Talos patch được giữ ở config/talos để tra cứu. Địa chỉ node, NIC, mount và disk được kiểm tra bằng talosctl; không áp dụng patch IP cũ nếu lab mới khác mạng. UserVolumeConfig không tự cài local-path Kubernetes provisioner.

Volume local-path 9 GB của worker tham chiếu không đủ dung lượng để ghi đầy các PVC Glance 10Gi và 2Gi. Cho lab mới, cấp disk đủ dung lượng hoặc chọn PVC nhỏ trước khi tạo PVC lần đầu. Đọc [storage note](../SOURCE-MAP.md) và [giữ/xóa](07-Keep-or-Delete.md). Không shrink PVC đang có để tiết kiệm.

## 4. Triển khai các dịch vụ OpenStack nền tảng

Đọc [05 trong folder](../reference/05.Openstackhelm.md) từ phần đầu vào, không đọc hướng dẫn Talos bên ngoài. Bản local đã chỉnh helper osh-base.sh dùng chart LOCAL cho tất cả service để không bỏ các chart pin đã lưu. Phần setup repo/plugin còn dùng Internet, nhưng distro files/chart local đã có thì không tải đè.

Thứ tự:

1. Namespace/node labels + helper + kiểm tra chart versions.
2. Local-path provisioner và nodePathMap đúng các mount đang có.
3. MariaDB/Memcached và RabbitMQ OSH tạm thời theo baseline đã làm.
4. Keystone/Placement/Glance và PVC đã chọn đủ dung lượng.
5. Shared OVN + Libvirt dùng chart Talos đã patch.
6. Neutron lấy NB/SB ClusterIP mới, tắt agents không dùng.
7. Nova socket Libvirt/OVS, cell setup; kiểm tra compute.
8. Rook/Ceph/Cinder: sdc đúng node, pool/client mới, FSID/MON/key mới.
9. Horizon và test core API/VM/volume.

RabbitMQ OSH tạm ở bước này là để tái tạo theo quy trình cũ đã có, không phải đích cuối. Bước 5 chuyển sang Operator. Nếu muốn cài thẳng Operator ngay từ đầu thì phải viết một workflow provisioning credentials/topology mới; không bỏ bước baseline rồi chạy migration vốn lấy credentials từ các service Secrets chưa có.

Nguồn 05 chứa patch Nova và phép gộp mounts. So sánh render trước install; có chart patched không tự giải quyết mọi override list. Secret Ceph nạp vào libvirt trong baseline còn thủ công; kiểm tra sau pod recreate, chưa có cơ chế tự nạp được nghiệm thu.

## 5. Chuyển RabbitMQ sang Operator

Đọc [06 trong folder](../reference/06.OpenstackOperatorMigration.md): Cluster Operator → cert-manager/Topology Operator → RabbitmqCluster → credentials adapter/user/vhost/permissions → chuyển lần lượt service/cell transport. Giữ MariaDB OSH như quyết định của lab.

Tên broker target là rabbitmq-genestack; API group rabbitmq.com khác *.osh.openstack.org. Nhận biết khác biệt này trước khi xóa CRD. Chart versions trong script phải khớp versions trên cluster mới; history/revision ghi ở phần kết quả là của cluster cũ, không phải lệnh chọn revision để rollback trên cluster mới.

Sau render/cutover, chờ Jobs, workload và kiểm tra API/transport; chỉ bỏ RabbitMQ OSH khi có bằng chứng client đã chuyển. Kết quả chưa được kiểm tra trong cụm tham chiếu không được dùng làm bằng chứng nghiệm thu cho cụm mới.

## 6. Triển khai Gateway và cấu hình Horizon HTTPS

Đọc [19 trong folder](../reference/19.Gateway.md). Envoy charts ở ~/osh-lab/gateway-api/charts đã được prepare; không cần folder bastion ngoài repo. CRD → controller → EnvoyProxy/Class/Gateway → HTTPRoute → TLS → Horizon HTTPS.

NodePort có thể khác 31429/31384 khi tạo Service mới. Lấy port thực tế:

```bash
kubectl -n envoyproxy-gateway-system get svc openstack-gateway
HTTPS_NODEPORT=$(kubectl -n envoyproxy-gateway-system get svc openstack-gateway \
  -o jsonpath='{.spec.ports[?(@.port==443)].nodePort}')
test -n "$HTTPS_NODEPORT" && printf 'HTTPS NodePort: %s\n' "$HTTPS_NODEPORT"
```

Phần Horizon ở mục 12.2 của bản 19 tự lấy HTTPS NodePort, tạo một file https-values.yaml cuối có internalURL và CSRF origin đúng, render rồi upgrade. Không cần tạo một override khác trước đó. Đổi hostname/IP theo lab mới, tạo certificate mới và trust trên client. Kiểm tra GET trang login rồi đăng nhập/dashboard; không dùng HEAD làm tiêu chí nghiệm thu.

## 7. Triển khai Octavia sau các dịch vụ nền tảng

Đọc [08 Octavia theo Genestack](08-Octavia-Genestack.md), chạy preflight rồi lấy chart pin. Script install-octavia.sh gốc yêu cầu điều chỉnh theo MariaDB OSH và tên broker RabbitMQ của môi trường này. Giữ driver-agent sidecar/post-rendering theo ý tưởng Genestack nếu dùng OVN; Amphora cần preconf/image/mgmt network/certs và reachability riêng.

Phần Octavia dùng cấu hình cuối trong bài 08: ba script chuẩn bị → render → install → Gateway → CLI → LB. Cụm tham chiếu đã có LB OVN ACTIVE/ONLINE; chưa thử backend/traffic hoặc dựng lại trên cụm sạch. Không có bước cài sai rồi sửa lại.

## 8. Lưu nguồn cấu hình sau triển khai

Cấu hình chính ở config/, chart patches ở assets/, version/chart/image provenance ghi trong manifest/README. Snapshots/render trong artifacts/ có thể tạo lại nếu source còn, không cần đưa lên GitHub. Private credentials, cert key, database/PVC không nằm trong Git public. Bộ folder này lưu tài liệu/cấu hình, không giữ dữ liệu cloud cũ.
