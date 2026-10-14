# 08. Triển khai Octavia OVN và tích hợp Horizon trên Talos

Tài liệu trình bày quy trình triển khai Octavia với provider OVN trên Kubernetes chạy Talos, công bố API qua Envoy Gateway và tích hợp giao diện quản lý Load Balancer vào Horizon. Cấu hình được xây dựng từ các thành phần của Genestack, sau đó điều chỉnh cho MariaDB, RabbitMQ và mạng OVN của cụm thử nghiệm.

Điều kiện đầu vào gồm các dịch vụ OpenStack nền tảng đang hoạt động, RabbitMQ Cluster Operator và Messaging Topology Operator đã triển khai, cùng Gateway HTTPS đã được cấu hình. Quy trình cài đặt Talos và các dịch vụ nền tảng nằm ngoài phạm vi tài liệu này. Mục 1–9 trình bày cài đặt Octavia; mục 10–12 trình bày vận hành và provider Amphora; mục 13 trình bày tích hợp Horizon.

Octavia cung cấp API điều khiển load balancer. Provider OVN chuyển cấu hình đó thành các đối tượng mạng trong OVN. Horizon là giao diện sử dụng API Octavia; việc cài plugin Horizon không thay thế việc triển khai Octavia hoặc cấu hình mạng cho các máy chủ ứng dụng.

**Kết quả triển khai:** Octavia, Gateway/API/provider và giao diện Load Balancers trên Horizon đã hoạt động. Ngày 13/10/2026, Horizon revision 10 tự khởi động thành công trên controlplane với image một layer và chart tùy chỉnh (mục 13). study-lb đã ACTIVE/ONLINE; chưa nghiệm thu traffic qua listener/pool/member/backend. Quy trình chưa được nghiệm thu toàn bộ trên một cụm mới.

Đối với cụm đã triển khai Octavia, quy trình cập nhật tại mục 10 thay thế các bước tạo release và load balancer mới. UUID và địa chỉ IP trong bảng nghiệm thu là dữ liệu của cụm tham chiếu, không phải tham số mặc định cho các cụm khác.

| Tệp cấu hình | Chức năng | Chính sách lưu trữ |
|---|---|---|
| tools/prepare-octavia-rabbitmq.py | Tạo thông tin xác thực và các đối tượng RabbitMQ | Lưu mã nguồn |
| tools/prepare-octavia-credentials.py | Đọc thông tin quản trị từ Secret; tạo thông tin xác thực DB, Keystone và cache | Lưu mã nguồn |
| tools/prepare-octavia-ovn.py | Sinh values, post-renderer và kiểm tra manifests | Lưu mã nguồn |
| ~/osh-lab/charts/octavia/ | Chart được cố định phiên bản, kèm helm-toolkit | Lưu chart và archive |
| ~/osh-lab/octavia/lab-values.yaml | Cấu hình provider, endpoint, images/resources | Giữ cấu hình cuối |
| ~/osh-lab/octavia/credentials-private.yaml | DB/Keystone/admin/cache credentials | Lưu riêng tư sau triển khai; loại khỏi Git |
| ~/osh-lab/octavia/rabbitmq-private.yaml | Broker endpoint/password Octavia | Lưu riêng tư sau triển khai; loại khỏi Git |
| ~/osh-lab/octavia/post-render.py | Ghép agent/socket/tolerations | Luôn dùng khi render/install/upgrade |
| ~/osh-lab/octavia/rendered.yaml | Manifests chứa Secret sau khi render | Có thể tạo lại; loại khỏi Git và các bản công bố |
| ~/osh-lab/gateway-api/manifests/octavia-route.yaml | Route HTTPS về octavia-api:9876 | Giữ manifest |

Các script yêu cầu Python3, PyYAML, kubectl và Helm; context Kubernetes phải trỏ đến cụm đích. Script sinh cấu hình ghi đè lab-values.yaml và post-render.py mỗi lần chạy. Các thay đổi lâu dài được thực hiện trong mã nguồn script để kết quả không bị mất ở lần sinh tiếp theo. Các tệp values chứa thông tin xác thực phải được duy trì nhất quán với release đang hoạt động.

## 1. Kiến trúc triển khai và đối chiếu với Genestack

Các thành phần Genestack liên quan được lưu tại [reference/genestack](../reference/genestack/docs/openstack-octavia.md), phục vụ đối chiếu kiến trúc và cấu hình. Bản sao này chứa tài liệu, script và values gốc; các điều chỉnh dành cho cụm Talos được triển khai bằng script và cấu hình của Openstack-Lab-Learning.

| Thành phần tham chiếu | Chức năng |
|---|---|
| [openstack-octavia.md](../reference/genestack/docs/openstack-octavia.md) | Chuẩn bị secrets, preconf Amphora, đưa values sinh ra vào thư mục overrides, chạy installer |
| [install-octavia.sh](../reference/genestack/bin/install-octavia.sh) | Pin chart, đọc base/global/custom, lấy secrets, lấy NB/SB Service, xử lý Kube-OVN TLS, Helm với post-renderer |
| [base values](../reference/genestack/base-helm-configs/octavia/octavia-helm-overrides.yaml) | Bật providers ovn+amphora, mặc định amphora, ACTIVE_STANDBY; DB/MQ mặc định theo Genestack |
| [Kustomize](../reference/genestack/base-kustomize/octavia/base/kustomization.yaml) | Thêm driver-agent sidecar trong API pod, shared /var/run/octavia, MariaDB/RabbitMQ CR, HPA và policy |
| [post-renderer](../reference/genestack/base-kustomize/octavia/post-renderer.sh) | Gọi framework Kustomize; thêm/xóa TLS mounts theo trạng thái Kube-OVN |
| [preconf role](../reference/genestack/ansible/roles/octavia_preconf/README.md) | Network/subnet/SG, ports, quota, keypair/flavor/image, certificate, Helm values |
| [LB workflow](../reference/genestack/docs/octavia-loadbalancer-setup-guide.md) | LB → listener → pool → members → monitor; chọn provider explicit |

Phiên bản chart trong bản Genestack tham chiếu là **2026.1.8+d03dd061a** cho Octavia và **2026.1.8+a659ab8a2** cho Barbican. Danh sách được lưu tại [helm-chart-versions.yaml](../reference/genestack/helm-chart-versions.yaml). Mục 3 tải chart Octavia theo phiên bản cố định. Phiên bản chart và phiên bản container image là hai thông số độc lập; cố định chart không làm các image có tag latest trở nên bất biến.


### 1.1. Vai trò của Octavia và Envoy Gateway

Envoy Gateway tiếp nhận kết nối HTTPS từ bên ngoài và chuyển tiếp đến API hoặc dashboard trong Kubernetes. Octavia quản lý load balancer của project OpenStack và địa chỉ VIP trên mạng tenant. HTTPRoute octavia.lab.test công bố API quản trị; đường truyền từ máy khách đến VIP của load balancer được thiết lập riêng trong mạng OpenStack.

Provider Amphora sử dụng máy ảo chạy HAProxy. Image Amphora dạng qcow2 được đưa vào Glance để Nova tạo máy ảo, trong khi container image Octavia được Kubernetes sử dụng để chạy API và các tiến trình điều khiển.

### 1.2. Provider OVN và Amphora

| Provider | Luồng xử lý | Điều kiện triển khai |
|---|---|---|
| OVN | Octavia API + driver-agent → OVN NB/SB → OVS dataplane | Neutron OVN, DB connectivity, driver-agent/socket đúng, tenant network |
| Amphora | Octavia worker → Nova tạo VM Amphora → cấu hình HAProxy | VM boot được, mgmt network/ports/SG, certificate, Glance image, flavor, worker/health manager reachability |

Genestack đặt Amphora làm provider mặc định và đồng thời hỗ trợ OVN. Cụm thử nghiệm trong tài liệu sử dụng OVN hiện có và chọn provider OVN để không bổ sung máy ảo Amphora. Đây là khác biệt cấu hình so với mặc định Genestack.

Các yêu cầu như xử lý lớp 7 hoặc kết thúc TLS tại load balancer phải được đối chiếu với khả năng của provider và phiên bản đang triển khai. Một load balancer TCP dùng OVN không đủ để nghiệm thu các chức năng đó. Khi triển khai Amphora với chứng thư do Barbican quản lý, cần bổ sung các thành phần và cấu hình tương ứng.

Amphora ACTIVE_STANDBY yêu cầu thiết kế vị trí máy ảo và miền lỗi phù hợp. Một compute node không cung cấp khả năng chịu lỗi mất node cho cả cặp máy ảo. Chế độ SINGLE có thể phù hợp với cụm thử nghiệm nhưng khác cấu hình HA mặc định của Genestack.

### 1.3. Điều chỉnh cho hạ tầng của cụm thử nghiệm

| Thành phần | Cấu hình Genestack | Hạ tầng của lab | Điều chỉnh |
|---|---|---|---|
| MariaDB | mariadb-cluster-primary + k8s.mariadb.com CR | OSH mariadb + controller/Jobs | Giữ MariaDB, dùng DB provisioning tương ứng; không apply CR Operator không có |
| RabbitMQ | rabbitmq + secret rabbitmq-default-user | rabbitmq-genestack | Đổi host/reference, tạo user/vhost/permission Octavia với Topology Operator |
| Keystone admin secret | keystone-admin.data.password | nova-keystone-admin có OS_* | Đọc key đúng, giữ service credentials mới; không giả định secret gốc tồn tại |
| Memcache key | os-memcached.data.memcache_secret_key | Chưa xác nhận key/config thực tế | Kiểm tra chiến lược cache/key, không dùng random key lệch giữa app/cấu hình |
| Kube-OVN SSL | networking.ENABLE_SSL, TLS Secret nếu true | Cần đọc effective values mới | TCP/SSL và CA/key phải khớp NB/SB, không dùng localhost mặc định |
| HPA | hpa-octavia-api | Lab chưa có Metrics API | Chưa đưa HPA vào lab; replicas/resources chọn theo dung lượng |
| Redis jobboard | Source có endpoint Sentinel, jobboard_enabled=false | Chưa cài Redis | Đọc flags/workload/dependencies thực tế; không cài Redis chỉ vì thấy chuỗi host |
| Kustomize | Thêm driver-agent vào API | Helm thuần sẽ bỏ phần này | Giữ cùng ý tưởng shared socket/sidecar, kiểm tra render sau post-render |

Một số script gốc đưa giá trị mật khẩu vào câu lệnh được in sau khi đọc Secret. Quy trình trong tài liệu sử dụng các tệp values riêng tư và tránh công bố thông tin xác thực trong đầu ra lệnh hoặc lịch sử shell.

### 1.4. Vai trò của chart, values và post-renderer

Helm chart chứa các template mô tả tài nguyên Kubernetes như Deployment, Service và Job. Tệp values cung cấp tham số cho các template, bao gồm image, endpoint, số replica và cấu hình ứng dụng. Helm hợp nhất các tệp values theo thứ tự xuất hiện trong lệnh; giá trị trong tệp sau có thể ghi đè giá trị cùng khóa trong tệp trước.

Render là quá trình kết hợp chart với values để sinh manifests Kubernetes. Kiểm tra manifests trước triển khai giúp xác định tài nguyên nào sẽ được tạo và cấu hình nào sẽ được áp dụng. Render thành công chỉ xác nhận quá trình sinh cấu hình; hoạt động của ứng dụng còn phụ thuộc vào image, thông tin xác thực, kết nối mạng và trạng thái các dịch vụ liên quan.

Post-renderer nhận manifests sau khi Helm render và điều chỉnh chúng trước khi triển khai. Trong quy trình Octavia này, post-renderer bố trí API và driver-agent trong cùng pod, bổ sung volume dùng chung cho socket và các tham số thực thi. Vì vậy, cùng một post-renderer phải được sử dụng ở cả lần cài đầu tiên và các lần cập nhật release.

## 2. Điều kiện triển khai và bố trí tệp cấu hình

Các lệnh Bash được thực hiện trên bastion Ubuntu. Bước kiểm tra đầu vào xác định context Kubernetes, trạng thái node và các dịch vụ mà Octavia sử dụng:

```bash
mkdir -p ~/osh-lab/octavia ~/osh-lab/charts ~/osh-lab/chart-archives
source ~/openstack-client/bin/activate
kubectl config current-context
kubectl get nodes -o wide
kubectl -n openstack get svc mariadb memcached keystone-api neutron-server
kubectl -n kube-system get svc ovn-nb ovn-sb
kubectl -n openstack get rabbitmqcluster rabbitmq-genestack
kubectl get crd users.rabbitmq.com vhosts.rabbitmq.com permissions.rabbitmq.com
helm get values kube-ovn -n kube-system --all -o json |
  python3 -c 'import json,sys; print("ENABLE_SSL=",json.load(sys.stdin).get("networking",{}).get("ENABLE_SSL","NOT_FOUND"))'
```

Quy trình sử dụng OVN qua TCP với ENABLE_SSL=False, broker rabbitmq-genestack ở trạng thái Ready, node controlplane-01 hoạt động và Gateway HTTPS đã tồn tại. Với OVN bật SSL, script sinh cấu hình phải được điều chỉnh để sử dụng giao thức và chứng thư phù hợp trước khi triển khai. Project, domain và thông tin quản trị được đọc từ nova-keystone-admin, nova-keystone-user và nova-db-admin thay cho các giá trị mẫu trong chart.

Mã nguồn có thể được chuyển toàn bộ vào ~/Openstack-Lab-Learning hoặc chỉ chuyển ba script chuẩn bị Octavia vào ~/osh-lab/octavia. Lệnh scp dưới đây thực hiện trên PowerShell của máy Windows chứa mã nguồn, sau khi thư mục nhận đã được tạo trên bastion. Địa chỉ bastion và đường dẫn nguồn được thay theo môi trường triển khai:

```powershell
scp "D:\system-intership\NNTrung\Genestack\Openstack-Lab-Learning\tools\prepare-octavia-*.py" bastion@192.168.207.138:~/osh-lab/octavia/
```

Các bước tiếp theo sử dụng script tại ~/osh-lab/octavia. Khi mã nguồn đã được chuyển toàn bộ sang bastion, sao chép script vào vị trí này:

```bash
cp ~/Openstack-Lab-Learning/tools/prepare-octavia-*.py ~/osh-lab/octavia/
```

Đường dẫn ổ D: thuộc máy Windows. Chạy scp với đường dẫn đó từ Bash trên bastion khiến chương trình diễn giải D: thành tên máy từ xa. Việc tải chart bằng Helm và việc chuyển script nguồn là hai bước độc lập.

## 3. Tải chart Octavia và kiểm tra thành phần phụ thuộc

Bước này tải và giải nén chart Octavia theo phiên bản cố định. Archive đã có trong thư mục cache được sử dụng lại; release Kubernetes chỉ được tạo ở mục 7.

```bash
(
set -eu
VERSION='2026.1.8+d03dd061a'
ARCHIVE="$HOME/osh-lab/chart-archives/octavia-${VERSION}.tgz"
if [ ! -f "$HOME/osh-lab/charts/octavia/Chart.yaml" ]; then
  if [ ! -f "$ARCHIVE" ]; then
    helm repo add openstack-helm https://tarballs.opendev.org/openstack/openstack-helm
    helm repo update openstack-helm
    helm pull openstack-helm/octavia --version "$VERSION" --destination ~/osh-lab/chart-archives
  fi
  tar -xzf "$ARCHIVE" -C ~/osh-lab/charts
fi
python3 - <<'PY'
from pathlib import Path
import yaml
meta=yaml.safe_load((Path.home()/'osh-lab/charts/octavia/Chart.yaml').read_text())
assert meta['name']=='octavia' and str(meta['version'])=='2026.1.8+d03dd061a'
print('PASS chart pin')
PY
helm dependency list ~/osh-lab/charts/octavia
)
```

Thành phần helm-toolkit phải có trạng thái unpacked. Khi dependency đã được đóng gói trong chart, việc chạy dependency update không cần thiết và có thể thay đổi nguồn phụ thuộc.

Chart local cho phép render mà không tải lại chart từ Internet. Các node vẫn cần container image để chạy workload. Triển khai ngoại tuyến yêu cầu lưu cả chart archive và image theo digest; quy trình quản lý image được trình bày tại [mục 04](04-Images.md).

## 4. Thiết lập tài khoản và vhost RabbitMQ

Script tạo mật khẩu riêng cho Octavia, lưu tại rabbitmq-private.yaml và tạo các đối tượng Secret, User, Vhost, Permission trên broker do Operator quản lý. Vhost sử dụng cấu hình quorum theo Genestack; broker một replica không áp dụng policy group size 3. Khi thực hiện lại, script giữ mật khẩu đã có và kiểm tra tính nhất quán giữa tệp cấu hình với Secret.

```bash
python3 ~/osh-lab/octavia/prepare-octavia-rabbitmq.py
kubectl -n openstack wait users.rabbitmq.com/gs-octavia-user --for=condition=Ready --timeout=180s
kubectl -n openstack wait vhosts.rabbitmq.com/gs-octavia-vhost --for=condition=Ready --timeout=180s
kubectl -n openstack wait permissions.rabbitmq.com/gs-octavia-permission --for=condition=Ready --timeout=180s
```

Các đối tượng RabbitMQ được Messaging Topology Operator quản lý, vì vậy Rabbit init Job của chart được tắt. Thông tin xác thực riêng của Octavia không thay thế thông tin đang dùng bởi các dịch vụ khác.

## 5. Thiết lập thông tin xác thực MariaDB và Keystone

```bash
python3 ~/osh-lab/octavia/prepare-octavia-credentials.py
```

Script đọc thông tin quản trị qua kubectl, sử dụng project/domain hiện có và tạo mật khẩu DB, mật khẩu dịch vụ Keystone cùng khóa mã hóa cache riêng cho Octavia. Tệp kết quả được đặt quyền 600. Khóa cache được sử dụng nhất quán trong cấu hình Octavia; bước này không thay cấu hình máy chủ Memcached.

Cơ sở dữ liệu và tài khoản dịch vụ được các Job của chart tạo khi cài release. Khi chạy lại script, mật khẩu Octavia được giữ nguyên, còn thông tin quản trị được cập nhật từ Secret hiện tại.

## 6. Sinh cấu hình OVN và kiểm tra manifests

```bash
python3 ~/osh-lab/octavia/prepare-octavia-ovn.py
```

Script đọc Service của OVN Northbound/Southbound và HTTPS NodePort đang sử dụng, sau đó tạo lab-values.yaml và post-render.py. Helm hợp nhất values theo thứ tự lab-values → credentials-private → rabbitmq-private. Bước kiểm tra manifests xác nhận socket giữa API và agent, thông tin xác thực, Neutron adapter, các Job DB/Keystone và việc loại bỏ workload không thuộc provider OVN.

Các đặc điểm của cấu hình OVN:

- Provider ovn, agent ovn; API một process/hai threads; không thêm VM Amphora.
- Job DB init/sync và Keystone Jobs bật; worker/health-manager/housekeeping/boot/image-sync/Rabbit-init tắt.
- Jobboard tắt vì không có Valkey. Quorum flags khớp vhost broker.
- API/agent cùng Pod, chung emptyDir /var/run/octavia và config/snippets. Hai Deployment độc lập với emptyDir riêng không chia sẻ socket.
- Service auth explicit dùng tài khoản Octavia; mặc định chart có thể dùng admin.
- **Neutron adapter có valid_interfaces=internal, endpoint_type=internalURL và endpoint_override=http://neutron-server.openstack.svc.cluster.local:9696.** service_auth.interface hoặc biến CLI trên bastion không thay adapter này; thiếu nó có thể khiến create LB gọi public neutron:80 không tồn tại dù provider list đã PASS.
- Agent dùng --config-file /etc/octavia/octavia.conf và --config-dir cho thư mục snippets. Không truyền tên file vào --config-dir.
- API/agent UID 0 theo patch Genestack; có control-plane toleration. Đây là cấu hình lab, chưa tương thích PodSecurity restricted. API request 512Mi/limit1536Mi, agent request128Mi/limit512Mi; không HPA khi chưa có Metrics API.

Kết quả kiểm tra render xác nhận cấu trúc cấu hình trước triển khai; trạng thái hoạt động được nghiệm thu riêng sau khi cài. Nội dung Secret có thể được mã hóa base64, nên tìm kiếm trực tiếp trong YAML không đủ để kiểm tra giá trị thực tế. rendered.yaml và các tệp values riêng tư được loại khỏi Git và các bản công bố.

## 7. Triển khai release Octavia OVN

Điều kiện chuyển sang bước cài đặt là manifests đã xác nhận cấu hình OVN, socket dùng chung giữa API và agent, thông tin xác thực nhất quán và đầy đủ năm Job: octavia-db-init, octavia-db-sync, octavia-ks-service, octavia-ks-user, octavia-ks-endpoints. Public API sử dụng HTTPS NodePort thực tế. Kết quả nghiệm thu của cụm tham chiếu được trình bày tại mục 11.

Release được tạo bằng chart local và ba tệp values đã kiểm tra. Post-renderer bổ sung cấu trúc API/agent nên được sử dụng trong cả cài đặt và cập nhật. Helm quản lý release cùng các hook; áp dụng trực tiếp rendered.yaml bằng kubectl không thay thế quy trình này.

```bash
(
set -eu
source ~/openstack-client/bin/activate
ROOT="$HOME/osh-lab/octavia"
for FILE in lab-values.yaml credentials-private.yaml rabbitmq-private.yaml post-render.py; do
  test -f "$ROOT/$FILE" || { echo "Thieu $FILE"; exit 1; }
done
helm install octavia ~/osh-lab/charts/octavia \
  --namespace openstack \
  --values "$ROOT/lab-values.yaml" \
  --values "$ROOT/credentials-private.yaml" \
  --values "$ROOT/rabbitmq-private.yaml" \
  --post-renderer "$ROOT/post-render.py" \
  --timeout 15m
)
```

helm install được sử dụng cho lần triển khai đầu tiên. Release đã tồn tại được kiểm tra bằng status/history và cập nhật theo mục 10; việc cài lại không đi kèm tạo mật khẩu mới.

Lệnh cài trong quy trình này không dùng --wait. Job DB init là post-install hook, trong khi init container của API chờ các Job DB/Keystone hoàn tất. Nếu Helm chờ API Ready trước khi thực thi hook, hai bước có thể tạo vòng chờ. Helm vẫn chờ hook Job theo timeout, còn rollout API được kiểm tra sau khi lệnh cài kết thúc. Khi hook thất bại hoặc hết thời gian, trạng thái và log của Job là nguồn chẩn đoán trước khi thực hiện lại.

```bash
helm -n openstack status octavia
kubectl -n openstack get jobs,pods -l application=octavia -o wide
kubectl -n openstack rollout status deployment/octavia-api --timeout=300s
kubectl -n openstack get deployment octavia-api \
  -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\n"}{end}'
kubectl -n openstack get svc octavia-api
```

Tiêu chí kiểm tra gồm pod API đạt 2/2 Running với octavia-api và octavia-agent, rollout hoàn tất và Service mở cổng 9876. Hook Job có thể được Helm xóa sau khi thành công theo hook-delete-policy. HTTPRoute và kiểm tra provider được thực hiện sau khi API sẵn sàng. Trạng thái deployed của Helm và Ready của pod chưa xác nhận đường truyền đến backend của load balancer.

Khi cài đặt thất bại, thông tin chẩn đoán gồm đầu ra Helm, trạng thái Job và pod. Các tệp riêng tư và rendered.yaml có thể chứa mật khẩu nên không được công bố nguyên bản. Keystone Jobs đăng ký service, user và endpoints riêng cho Octavia; các route và public endpoint của dịch vụ khác nằm ngoài thay đổi này.

## 8. Công bố Octavia API qua Gateway HTTPS

Kết quả triển khai tham chiếu ghi nhận release deployed, năm Job hoàn tất, rollout octavia-api thành công và Service sử dụng ClusterIP 10.96.128.238, cổng 9876. UID 0 của API/agent là cấu hình thử nghiệm theo phần điều chỉnh Genestack. Cụm hiện tại cho phép tạo workload và phát cảnh báo PodSecurity; cụm thực thi chính sách restricted cần thiết kế securityContext phù hợp.

Manifest HTTPRoute được lưu trên bastion và áp dụng vào namespace openstack. Route công bố Octavia API qua HTTPS; việc tạo load balancer trên mạng tenant được thực hiện riêng ở mục 9.

```bash
mkdir -p ~/osh-lab/gateway-api/manifests
cat > ~/osh-lab/gateway-api/manifests/octavia-route.yaml <<'EOF'
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: octavia-gateway-route
  namespace: openstack
  labels:
    lab-component: openstack-gateway
spec:
  parentRefs:
    - name: flex-gateway
      namespace: envoy-gateway
      sectionName: openstack-https
  hostnames:
    - octavia.lab.test
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: octavia-api
          port: 9876
EOF
kubectl apply -f ~/osh-lab/gateway-api/manifests/octavia-route.yaml
kubectl -n openstack get httproute octavia-gateway-route \
  -o jsonpath='{range .status.parents[*].conditions[*]}{.type}{"="}{.status}{" reason="}{.reason}{"\n"}{end}'
GATEWAY_HTTPS_PORT=$(kubectl -n envoyproxy-gateway-system get svc openstack-gateway \
  -o jsonpath='{.spec.ports[?(@.port==443)].nodePort}')
: "${GATEWAY_HTTPS_PORT:?Gateway chua co HTTPS NodePort}"
curl --insecure --max-time 15 --resolve "octavia.lab.test:${GATEWAY_HTTPS_PORT}:192.168.207.139" \
  -i "https://octavia.lab.test:${GATEWAY_HTTPS_PORT}/"
```

HTTPRoute được chấp nhận khi Accepted=True và ResolvedRefs=True. API root cung cấp thông tin phiên bản dạng JSON. curl sử dụng --resolve để ánh xạ hostname đến node trong riêng yêu cầu kiểm tra, không phụ thuộc /etc/hosts. Địa chỉ node được thay theo cụm đích.

### 8.1. Cấu hình OpenStack CLI qua Gateway

Môi trường CLI được cấu hình theo [10-Admin-Environment.md](10-Admin-Environment.md). Script admin.sh nạp thông tin xác thực và các endpoint Gateway cho OpenStack, bao gồm Octavia:

```bash
source ~/osh-lab/bin/admin.sh
timeout 30s openstack loadbalancer provider list
timeout 30s openstack subnet list
```

Certificate tự ký trong lab được xử lý bằng chế độ insecure của môi trường CLI; khi có CA tin cậy, cấu hình CA thay thế chế độ này. Danh sách provider phải chứa ovn. Kết quả đó xác nhận API đã đăng ký provider, còn quá trình xử lý của agent và dataplane được kiểm tra bằng các tài nguyên LB và traffic ở mục 9.

## 9. Tạo load balancer và xác định máy chủ backend

Bước tạo load balancer được thực hiện sau khi danh sách provider có ovn. Subnet VIP được chọn từ subnet list của cụm đích; UUID trong bảng nghiệm thu thuộc cụm tham chiếu.

```bash
read -r -p 'VIP subnet UUID: ' VIP_SUBNET_ID
: "${VIP_SUBNET_ID:?Chua chon subnet}"
timeout 30s openstack --insecure loadbalancer list
```

Lệnh tạo áp dụng khi danh sách load balancer chưa có study-lb:

```bash
timeout 30s openstack --insecure loadbalancer create \
  --name study-lb --provider ovn --vip-subnet-id "$VIP_SUBNET_ID"
timeout 30s openstack --insecure loadbalancer show study-lb \
  -c id -c provider -c vip_address -c provisioning_status -c operating_status
```

PENDING_CREATE thể hiện yêu cầu đang được xử lý; trạng thái được kiểm tra lại bằng show thay vì gửi thêm yêu cầu tạo. Exit code 124 của timeout cho biết tiến trình CLI đã hết thời gian chờ, nhưng yêu cầu có thể đã đến API. Danh sách và chi tiết tài nguyên được kiểm tra trước khi thực hiện lại thao tác tạo. ACTIVE/ONLINE xác nhận trạng thái cấp phát, chưa xác nhận dịch vụ backend hay lưu lượng thực tế.

```bash
read -r -p 'Tenant network UUID: ' TENANT_NETWORK_ID
: "${TENANT_NETWORK_ID:?Chua chon network}"
timeout 30s openstack --insecure port list --network "$TENANT_NETWORK_ID"
read -r -p 'Port UUID muon kiem tra backend: ' BACKEND_PORT_ID
: "${BACKEND_PORT_ID:?Chua chon port}"
timeout 30s openstack --insecure port show "$BACKEND_PORT_ID" \
  -c id -c fixed_ips -c device_owner -c device_id -c status
```

Danh sách máy ảo được truy vấn qua Nova Gateway trong môi trường CLI đã nạp thông tin xác thực:

```bash
timeout 30s openstack server list
```

Địa chỉ IP hoặc trạng thái port không đủ để xác nhận một máy ảo đang chạy dịch vụ HTTP. VIP của OVN load balancer không gắn vNIC như port máy ảo, vì vậy port status không phải tiêu chí duy nhất đánh giá LB.

Máy chủ backend phải lắng nghe cổng phục vụ đã chọn, ví dụ TCP 80, và có security group cho phép lưu lượng tương ứng. Máy kiểm tra phải có đường định tuyến đến VIP trên mạng tenant. NodePort của Octavia API cung cấp đường quản trị, không cung cấp đường truyền đến VIP.

Phần nghiệm thu traffic chưa được thực hiện trong cụm tham chiếu. Các bước tiếp theo gồm listener TCP, pool SOURCE_IP_PORT, members và health monitor phù hợp với provider, sau đó kiểm tra lưu lượng đến ứng dụng backend. Cấu trúc các tài nguyên được trình bày trong [hướng dẫn load balancer của Genestack](../reference/genestack/docs/octavia-loadbalancer-setup-guide.md).

## 10. Quản lý cấu hình và cập nhật Octavia

Thay đổi lâu dài được thực hiện trong script sinh cấu hình hoặc các nguồn cấu hình tương ứng, sau đó render và kiểm tra trước khi cập nhật release. Thông tin xác thực riêng tư đang sử dụng được giữ nhất quán. Script có thể đọc endpoint từ Service hiện tại; những khác biệt khác của hạ tầng cần được phản ánh trong cấu hình.

```bash
(
set -eu
ROOT="$HOME/osh-lab/octavia"
helm upgrade octavia ~/osh-lab/charts/octavia -n openstack \
  -f "$ROOT/lab-values.yaml" -f "$ROOT/credentials-private.yaml" \
  -f "$ROOT/rabbitmq-private.yaml" --post-renderer "$ROOT/post-render.py" --timeout 15m
kubectl -n openstack rollout status deployment/octavia-api --timeout=300s
)
```

Các hook Job có thể được thực thi lại khi cập nhật. Helm tiếp tục quản lý release và post-renderer; các sửa đổi trực tiếp trong container không phải nguồn cấu hình lâu dài. Khi render hoặc hook thất bại, việc chẩn đoán tập trung vào bước tương ứng trước khi thay đổi thông tin xác thực hoặc vòng đời release. Các lệnh sau cung cấp lịch sử release, trạng thái workload và log API/agent:

```bash
helm -n openstack history octavia
kubectl -n openstack get pods,jobs -l application=octavia -o wide
kubectl -n openstack logs deployment/octavia-api -c octavia-agent --since=5m --tail=80
kubectl -n openstack logs deployment/octavia-api -c octavia-api --since=5m --tail=80
```

Log có thể chứa thông tin nhạy cảm và cần được rà soát trước khi công bố. provider list kiểm tra API và đăng ký provider; tạo load balancer kiểm tra thêm tương tác với Neutron, driver-agent và OVN.

## 11. Kết quả nghiệm thu của cụm tham chiếu

| Phần | Kết quả đã xác nhận |
|---|---|
| Chart | 2026.1.8+d03dd061a, appVersion18.0.0, helm-toolkit unpacked |
| OVN | TCP NB10.97.84.74:6641, SB10.96.214.248:6642; SSLFalse |
| RabbitMQ | gs-octavia User/Vhost/Permission Ready |
| Credentials/render | Project/domain service; render PASS |
| Install | Release deployed, năm DB/Keystone Jobs Complete, rollout API thành công |
| Gateway/CLI | Accepted=True/ResolvedRefs=True, provider ovn, subnet list exit0 |
| LB | study-lb 63c9d0f9-d970-4a8e-b227-d89d51216343, VIP10.20.0.50, ACTIVE/ONLINE |
| Subnet | vm-subnet 8a529d0d-cf08-4740-81a0-dd2418ab9a77, network7a76df36-8da9-4828-b07f-ac3398ebfbe9, 10.20.0.0/24 |
| Backend | Port1d4c4522-f2e9-4727-984f-42f8ed9f05cd, IP10.20.0.80, DOWN; chưa xác định VM/ứng dụng |
| Còn thiếu | Listener/pool/member, backend và nghiệm thu traffic |

Các UUID và địa chỉ IP trong bảng phục vụ đối chiếu kết quả của cụm tham chiếu. Cụm mới sử dụng tài nguyên và địa chỉ được truy vấn từ môi trường của nó. Cấu hình triển khai đã bao gồm Neutron internal endpoint ngay từ bước sinh values.

## 12. Chuẩn bị hạ tầng cho provider Amphora

[Playbook](../reference/genestack/ansible/playbooks/octavia-preconf-main.yaml) và role Amphora được lưu cùng tài liệu tham chiếu. Các task openstack.cloud.* sử dụng interface public, còn một số shell script sử dụng OS_CLOUD=default và endpoint từ cloud configuration. Vì vậy, chỉ đặt OS_AUTH_URL trỏ đến localhost không chuyển toàn bộ task sang port-forward.

Máy thực thi role phải truy cập được Keystone và các endpoint trong service catalog. Các task được điều chỉnh theo interface và cloud configuration của môi trường trước khi chạy. Thành phần phụ thuộc gồm Ansible, openstacksdk, python-openstackclient, kubernetes và các collection được task sử dụng, như openstack.cloud, community.crypto, kubernetes.core. Phiên bản đã nghiệm thu được lưu trong requirements để tái tạo môi trường thực thi.

Theo defaults, role tạo mạng quản trị lb-mgmt-net dạng Geneve và subnet 172.16.29.0/24. CIDR được điều chỉnh nếu trùng mạng pod, Service, tenant hoặc LAN. Flavor mặc định gồm 2 vCPU, 1 GiB RAM và 5 GB disk. Image Amphora Ubuntu Noble dạng qcow2 trong nguồn tham chiếu phục vụ thử nghiệm; triển khai production cần image được xây dựng và nghiệm thu theo yêu cầu vận hành.

Role chuẩn bị management ports và security rules cho worker/health manager. Trên Talos, khả năng kết nối từ pod đến mạng quản trị Amphora phải được thiết kế phù hợp với Kube-OVN. Chứng thư dùng giữa controller và Amphora độc lập với chứng thư wildcard của Gateway HTTPS.

Values được sinh cho Amphora có các danh sách volume và mount. Việc hợp nhất values có thể thay toàn bộ danh sách, vì vậy manifests sau cùng cần được kiểm tra để xác nhận các mount khác vẫn tồn tại.

Bản cấu hình tham chiếu có endpoint Redis Sentinel nhưng đặt jobboard_enabled=false. Sự hiện diện của endpoint không đủ để xác định Redis là thành phần bắt buộc của luồng hiện tại. Khi bật jobboard hoặc bổ sung HA, cấu hình Redis và luồng xử lý liên quan được triển khai, nghiệm thu riêng.

## 13. Octavia Dashboard trên Horizon 2025.2

### 13.1. Phạm vi tích hợp và cấu hình tham chiếu

Phần này bổ sung giao diện quản lý Load Balancer vào release Horizon đã tồn tại. Các bước tạo DB, broker topology, Octavia API, OVN provider và Gateway HTTPS nằm ở mục 1–10. Cài plugin giao diện không tự cài Octavia backend, tạo listener hay cung cấp dataplane cho LB.

Kết quả nghiệm thu ngày 13/10/2026:

- Horizon Helm release revision 10, pod mới trên controlplane-01 đạt 1/1 Running và không restart.
- Horizon package 25.5.3.dev10, Django 4.2.23, Octavia Dashboard 16.0.0.
- Giao diện Horizon truy cập qua HTTPS hiển thị mục Load Balancers.
- Pod mới tự tạo static assets/manifest sau khi sửa script khởi động; không chạy compress thủ công ở lần rollout cuối.
- API/provider OVN và study-lb đã được xác nhận trước đó; kiểm tra traffic qua listener/pool/member vẫn là công việc riêng.

Horizon dùng chart 2026.1.31+0ee5adeff nhưng image chứa Horizon 2025.2. Cột APP VERSION của helm list là metadata của chart, không phải phiên bản package đang chạy. Khi quản trị phải giữ cả chart, image digest và values. Bản 2025.2 của Octavia Dashboard là 16.0.0. [OpenStack 2025.2](https://releases.openstack.org/flamingo/index.html), [cài Octavia Dashboard](https://docs.openstack.org/octavia-dashboard/latest/installation.html).

Luồng cuối: image nền → thêm plugin → đóng filesystem thành image một layer → push GHCR → kiểm tra trên controlplane → chuẩn bị chart tùy chỉnh → Helm upgrade → xác nhận dashboard.

Image một layer được sử dụng để tránh lỗi filesystem quan sát trong lab; đây là điều chỉnh riêng của môi trường, không phải yêu cầu triển khai Genestack hoặc Octavia. Cùng digest image nhiều layer đã cho các file 0 byte trên controlplane nhưng đầy đủ trên worker. Nguyên nhân sâu của runtime/lưu trữ và DNS chập chờn chưa được xác định. Quy trình cuối đã hoạt động trên cụm hiện tại; chưa dựng lại toàn bộ cụm sạch từ đầu để nghiệm thu.

### 13.2. Điều kiện triển khai và cấu trúc lưu trữ

Tất cả lệnh trong phần này chạy ở Bash trên bastion. Cần kubectl đúng context, Helm, Python3/PyYAML, Docker Engine/builder và truy cập registry/PyPI. Docker CLI không tự cung cấp builder; không cài Docker lên Talos.

| Vị trí trên bastion | Nội dung | Cách quản lý |
|---|---|---|
| ~/osh-lab/charts/horizon/ | Chart gốc đúng version release | Giữ hoặc giữ archive để tải lại |
| ~/osh-lab/horizon-octavia/Dockerfile | Thêm pip và plugin vào image nền | Giữ trong Git |
| ~/osh-lab/horizon-octavia/flatten-horizon-image.py | Đóng filesystem thành image mới | Giữ trong Git |
| ~/osh-lab/horizon-octavia/patch-horizon-static.py | Sửa script startup của chart | Giữ trong Git |
| ~/osh-lab/horizon-octavia/flat/rootfs.tar | Filesystem xuất tạm khi đóng image | Có thể xóa sau khi image hoạt động; không cần đưa lên Git |
| ~/osh-lab/charts/horizon-octavia/ | Chart tùy chỉnh dùng cho lần cài theo tài liệu này | Giữ chart hoặc giữ chart gốc + script patch |
| ~/osh-lab/horizon-octavia/octavia-values.yaml | Image digest, vị trí node, danh sách panel | Giữ trong Git; file này không chứa password |
| ~/osh-lab/horizon-version/octavia-final-…/ | Baseline values, lịch sử, rollback revision và rendered manifests | Giữ private; có thể chứa credentials |
| GHCR horizon-octavia | Image được Kubernetes tải | Giữ tag/digest đang dùng |

Nguồn tương ứng trong repo: [Dockerfile](../images/horizon-octavia/Dockerfile), [script đóng image](../tools/flatten-horizon-image.py), [script sửa chart](../tools/patch-horizon-static.py), [values cuối của lab](../examples/horizon/octavia-dashboard-values.yaml). Các tệp được tạo trực tiếp trên bastion bằng các đoạn lệnh trong phần này. Đường dẫn mã nguồn Windows không được sử dụng làm đường dẫn thực thi trên Linux.


```bash
kubectl config current-context
kubectl -n openstack get deployment horizon
helm list -n openstack --filter '^horizon$'
docker info --format '{{.ServerVersion}}'
python3 -c 'import yaml; print("PyYAML OK")'
test -f ~/osh-lab/charts/horizon/Chart.yaml
```

Các biến sau xác định namespace registry, node đích và tên image cho toàn bộ quy trình. GHCR_OWNER sử dụng chữ thường và được thay theo tài khoản xuất bản image. Tag có dấu thời gian để phân biệt từng lần build với image đã cache trên node. Các bước tiếp theo sử dụng cùng phiên shell; phiên mới cần nạp lại đúng giá trị đã lưu.

```bash
export GHCR_OWNER='erintn2025'
export HORIZON_NODE='controlplane-01'
export HORIZON_NODE_IP='192.168.207.137'
export HORIZON_BUILD_TAG="2025.2-octavia16-$(date +%Y%m%d-%H%M%S)"
export HORIZON_RAW_IMAGE="ghcr.io/$GHCR_OWNER/horizon-octavia:${HORIZON_BUILD_TAG}-raw"
export HORIZON_PUBLISH_IMAGE="ghcr.io/$GHCR_OWNER/horizon-octavia:${HORIZON_BUILD_TAG}-flat"
mkdir -p ~/osh-lab/horizon-octavia
```

Image cuối đang chạy trong lab là ghcr.io/erintn2025/horizon-octavia@sha256:5a0e344e9ef4193ca2da2c7f98a7f3a131603c715c94770a1a2ce8b0b6952587. Có thể dùng image đã xuất bản này để bỏ qua mục 13.3–13.5 nếu nó còn tải được; đặt HORIZON_IMAGE bằng digest đó rồi thực hiện mục 13.6. Không cần build lại chỉ để cài lại cùng image.

### 13.3. Xây dựng image Horizon có plugin Octavia

Image nền đã kiểm tra:

- Registry/tag nguồn: quay.io/airshipit/horizon:2025.2-ubuntu_noble.
- Digest dùng ở luồng cuối: sha256:61919ada1502dc698047489c496bb1873e02c239fdb9d6e278e35d6243bb812a.
- Horizon 25.5.3.dev10, Django 4.2.23, Linux amd64.


```bash
(
set -eu
BASE_IMAGE='quay.io/airshipit/horizon@sha256:61919ada1502dc698047489c496bb1873e02c239fdb9d6e278e35d6243bb812a'
docker pull --platform linux/amd64 "$BASE_IMAGE"
docker run --rm --platform linux/amd64 \
  --entrypoint /var/lib/openstack/bin/python3 "$BASE_IMAGE" \
  -c 'from importlib.metadata import version; print("Horizon:", version("horizon")); print("Django:", version("Django"))'
)
```

Nếu registry không còn cung cấp digest, dùng tag để xác định image thay thế, kiểm tra package rồi cập nhật ARG BASE_IMAGE của Dockerfile. Tag có thể đổi nội dung theo thời gian; phiên bản package phải được kiểm tra lại trước khi dùng. Không sửa metadata chart để làm helm list hiển thị theo image.

Tạo Dockerfile:

```bash
cat > ~/osh-lab/horizon-octavia/Dockerfile <<'EOF'
ARG BASE_IMAGE=quay.io/airshipit/horizon@sha256:61919ada1502dc698047489c496bb1873e02c239fdb9d6e278e35d6243bb812a
FROM ${BASE_IMAGE}
USER 0:0

# Chuẩn bị pip trong đúng virtualenv của Horizon.
RUN /var/lib/openstack/bin/python3 -c \
      "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', '/tmp/get-pip.py')" \
 && /var/lib/openstack/bin/python3 /tmp/get-pip.py \
 && rm /tmp/get-pip.py

# Lưu versions, tránh giữ các đường dẫn nguồn đã bị dọn trong image nền.
RUN /var/lib/openstack/bin/python3 -m pip list --format=freeze > /tmp/horizon-constraints.txt \
 && /var/lib/openstack/bin/python3 -m pip install --no-cache-dir \
      -c /tmp/horizon-constraints.txt octavia-dashboard==16.0.0 \
 && /var/lib/openstack/bin/python3 -m pip check \
 && /var/lib/openstack/bin/python3 -c "from importlib.metadata import version; from importlib.util import find_spec; print('Horizon:', version('horizon')); print('Octavia Dashboard:', version('octavia-dashboard')); assert find_spec('octavia_dashboard')" \
 && rm /tmp/horizon-constraints.txt

# Script của chart chown theo tên tài khoản horizon.
RUN getent passwd horizon >/dev/null || useradd --system --user-group \
      --home-dir /var/lib/horizon --no-create-home --shell /usr/sbin/nologin horizon
EOF
```

pip được cài vào /var/lib/openstack, đúng virtualenv của Horizon. Constraints giữ phiên bản các package hiện có trong khi thêm plugin; dùng pip list --format=freeze để tránh lưu lại đường dẫn nguồn /tmp/horizon đã bị dọn khỏi image nền. pip check phát hiện dependencies thiếu hoặc xung đột. USER 0:0 tránh phụ thuộc việc runtime tra cứu tên root khi tạo container; user horizon vẫn cần cho chown và WSGI của chart. [Cài pip](https://pip.pypa.io/en/stable/installation/), [pip list](https://pip.pypa.io/en/stable/cli/pip_list/).


```bash
(
set -eu
: "${HORIZON_RAW_IMAGE:?Nạp thông số ở mục 13.2}"
docker build --network=host --platform linux/amd64 --progress=plain \
  -t "$HORIZON_RAW_IMAGE" \
  -f ~/osh-lab/horizon-octavia/Dockerfile \
  ~/osh-lab/horizon-octavia
docker run --rm --entrypoint /var/lib/openstack/bin/python3 "$HORIZON_RAW_IMAGE" \
  -c 'import pwd, pymysql; from importlib.metadata import version; assert pwd.getpwnam("horizon"); assert hasattr(pymysql, "install_as_MySQLdb"); print("Horizon:", version("horizon")); print("Octavia Dashboard:", version("octavia-dashboard"))'
)
```

--network=host dùng mạng bastion cho các lệnh RUN tải pip/package. Build mặc định từng gặp lỗi DNS trong môi trường lab. Cờ này không thay đổi mạng pod Horizon. Nếu DNS của bastion cũng lỗi, cờ này không thay thế việc sửa DNS. [Docker build network](https://docs.docker.com/reference/cli/docker/buildx/build/#network).

### 13.4. Đóng gói filesystem thành image một layer

Image build ở mục 13.3 là nguồn để đóng gói; chưa cần push image nguồn. Script tạo container không khởi động ứng dụng, export filesystem, xác nhận một số file quan trọng không rỗng rồi import thành image mới. ENV, WORKDIR, ENTRYPOINT, CMD và StopSignal được khôi phục; user chạy mặc định là UID/GID 0. Script không sao chép toàn bộ metadata image như history, healthcheck hoặc VOLUME declarations. Trong luồng này Helm chart cung cấp command, volumes và probes riêng.

Giữ các biến môi trường là cần thiết vì Horizon dùng virtualenv /var/lib/openstack. Chỉ export/import filesystem mà bỏ metadata có thể làm chương trình dùng nhầm Python hệ thống. [Docker import](https://docs.docker.com/reference/cli/docker/image/import/).

Tạo script:

```bash
cat > ~/osh-lab/horizon-octavia/flatten-horizon-image.py <<'PY'
#!/usr/bin/env python3
"""Export/import Horizon filesystem; preserve runtime metadata needed by the chart."""
import json
from pathlib import Path
import subprocess
import sys
import tarfile

if len(sys.argv) != 4:
    raise SystemExit("Usage: flatten-horizon-image.py SOURCE_IMAGE TARGET_IMAGE WORK_DIR")
base, target, directory = sys.argv[1:]
if base == target:
    raise SystemExit("Source and target must be different")
root = Path(directory).expanduser()
root.mkdir(parents=True, exist_ok=True)
archive = root / "rootfs.tar"

def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()

config = json.loads(run(["docker", "image", "inspect", base]))[0]["Config"]
container = run(["docker", "create", "--entrypoint", "/bin/true", base])
try:
    subprocess.run(["docker", "export", "--output", str(archive), container], check=True)
finally:
    subprocess.run(["docker", "rm", container], check=True)

with tarfile.open(archive) as package:
    for name in [
        "etc/passwd", "etc/group", "etc/apache2/envvars", "usr/sbin/a2enmod",
        "var/lib/openstack/lib/python3.12/site-packages/pymysql/__init__.py",
    ]:
        entry = package.getmember(name)
        if entry.size <= 0:
            raise SystemExit("Empty source file: " + name)
        print(name, "bytes=", entry.size)

args = ["docker", "import", "--platform", "linux/amd64", "--change", "USER 0:0"]
for item in config.get("Env") or []:
    key, value = item.split("=", 1)
    args += ["--change", "ENV " + key + "=" + json.dumps(value)]
if config.get("WorkingDir"):
    args += ["--change", "WORKDIR " + config["WorkingDir"]]
for key in ["Entrypoint", "Cmd"]:
    if config.get(key):
        args += ["--change", key.upper() + " " + json.dumps(config[key])]
if config.get("StopSignal"):
    args += ["--change", "STOPSIGNAL " + config["StopSignal"]]
args += [str(archive), target]
subprocess.run(args, check=True)
subprocess.run([
    "docker", "run", "--rm", "--entrypoint", "/var/lib/openstack/bin/python3", target,
    "-c", 'import pwd, pymysql; from importlib.metadata import version; '
          'assert pwd.getpwnam("horizon"); '
          'assert hasattr(pymysql, "install_as_MySQLdb"); '
          'print("Horizon:", version("horizon")); '
          'print("Octavia Dashboard:", version("octavia-dashboard"))'
], check=True)
print("Local image ready:", target)
print("Temporary filesystem archive:", archive)
PY
```

```bash
(
set -eu
: "${HORIZON_RAW_IMAGE:?Nạp thông số ở mục 13.2}"
: "${HORIZON_PUBLISH_IMAGE:?Nạp thông số ở mục 13.2}"
python3 ~/osh-lab/horizon-octavia/flatten-horizon-image.py \
  "$HORIZON_RAW_IMAGE" "$HORIZON_PUBLISH_IMAGE" \
  ~/osh-lab/horizon-octavia/flat
)
```

Tiêu chí kiểm tra: các file được kiểm tra có kích thước lớn hơn 0, Horizon 25.5.3.dev10 và Octavia Dashboard 16.0.0. Đây là kiểm tra nguồn/image trên bastion; mục 13.6 kiểm tra riêng trên node triển khai.

### 13.5. Xuất bản image trên GHCR và xác định digest

GHCR cần Personal access token (classic) có scope write:packages để push. Login thành công không tự chứng minh có quyền ghi package. Dùng token của tài khoản sở hữu namespace GHCR_OWNER. Tạo token tại GitHub Settings → Developer settings → Personal access tokens → Tokens (classic); không cần cấp delete:packages cho quy trình này. [Quyền GHCR](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).


```bash
(
set -eu
: "${GHCR_OWNER:?Nạp thông số ở mục 13.2}"
: "${HORIZON_PUBLISH_IMAGE:?Nạp thông số ở mục 13.2}"
docker login ghcr.io -u "$GHCR_OWNER"
docker push "$HORIZON_PUBLISH_IMAGE"
)
export HORIZON_IMAGE="$(docker image inspect "$HORIZON_PUBLISH_IMAGE" --format '{{index .RepoDigests 0}}')"
printf 'Image dùng cho Helm: %s\n' "$HORIZON_IMAGE"
printf '%s\n' "$HORIZON_IMAGE" > ~/osh-lab/horizon-octavia/published-image.txt
```

Ở trường Password của docker login, nhập token, không nhập mật khẩu tài khoản GitHub. Token không hiện ra trên terminal khi nhập là bình thường. Nếu Docker đang dùng credentials cũ không đúng quyền, đăng xuất GHCR trước khi đăng nhập lại bằng token phù hợp.

Sau lần push đầu, vào GitHub → trang tài khoản → Packages → horizon-octavia → Package settings → Change visibility → Public. Public package cho phép node tải không cần credentials. Docker login trên bastion không đăng nhập registry cho Talos nodes. Nếu cần package private phải cấu hình imagePullSecret cho pod; quy trình ở đây dùng package public.

published-image.txt chỉ chứa image reference/digest, có thể lưu cùng cấu hình public. Mỗi lần đổi image phải dùng digest mới; không giả định tag cố định luôn chứa bản đã kiểm tra.

### 13.6. Kiểm tra image trên node triển khai

Kiểm tra package, user và file ứng dụng ngay trên node sẽ chạy Horizon. Pod probe trên worker chỉ chứng minh image hoạt động ở worker, không nghiệm thu filesystem trên controlplane. Pod kiểm tra dùng UID/GID số 0 để vẫn chạy được lệnh chẩn đoán nếu file passwd có vấn đề.


```bash
(
set -eu
: "${HORIZON_IMAGE:?Nạp digest image đã push}"
: "${HORIZON_NODE:?Nạp thông số ở mục 13.2}"
POD="horizon-image-check-$(date +%s)"
OVERRIDES=$(python3 -c 'import json,os; print(json.dumps({"spec":{"nodeName":os.environ["HORIZON_NODE"],"securityContext":{"runAsUser":0,"runAsGroup":0}}}))')
kubectl -n openstack run "$POD" --restart=Never \
  --image="$HORIZON_IMAGE" --image-pull-policy=Always \
  --overrides="$OVERRIDES" \
  --command -- /var/lib/openstack/bin/python3 -c '
import pwd, pymysql
from pathlib import Path
from importlib.metadata import version
assert pwd.getpwnam("horizon")
for name in ["/etc/passwd", "/etc/group", pymysql.__file__, "/etc/apache2/envvars", "/usr/sbin/a2enmod"]:
    assert Path(name).stat().st_size > 0, "File rong: " + name
assert hasattr(pymysql, "install_as_MySQLdb")
print("Horizon:", version("horizon"))
print("Octavia Dashboard:", version("octavia-dashboard"))
print("FILES_OK")
'
if kubectl -n openstack wait "pod/$POD" \
  --for=jsonpath='{.status.phase}'=Succeeded --timeout=300s; then
  kubectl -n openstack logs "$POD"
  kubectl -n openstack delete pod "$POD"
else
  kubectl -n openstack logs "$POD" || true
  kubectl -n openstack describe pod "$POD"
  exit 1
fi
)
```

Điều kiện chuyển sang triển khai là đầu ra FILES_OK. Pod kiểm tra được giữ lại khi thất bại để phân tích log và Events. Trạng thái Succeeded/Completed biểu thị chương trình kết thúc thành công; các assertions trong chương trình xác định những tiêu chí kỹ thuật đã được kiểm tra.

Probe không chạy toàn bộ Horizon nên FILES_OK chưa thay thế rollout và kiểm tra trang đăng nhập.

### 13.7. Cấu hình quá trình tạo static assets khi khởi động

Static assets của Horizon gồm JavaScript, CSS và các tài nguyên giao diện. collectstatic tập hợp chúng vào thư mục phục vụ web; compress tạo các tài nguyên nén và manifest ánh xạ nội dung template đến tệp đã nén. Manifest này là dữ liệu của Django Compressor, khác với manifests Kubernetes do Helm tạo.

Startup script của chart bật panel trước khi chạy collectstatic/compress. Trong luồng cũ, bước compilemessages đổi thư mục sang plugin nhưng không quay lại thư mục Horizon trước khi tạo assets. Sau khi thêm plugin, trang đăng nhập đã gặp OfflineGenerationError; chạy compress thủ công và reload Apache xử lý được pod hiện tại. Điều chỉnh cuối đưa working directory về openstack_dashboard trước collectstatic/compress; pod mới đã đạt Ready mà không cần thao tác thủ công.

Đây là điều chỉnh đã nghiệm thu trên lab, không khẳng định working directory là nguyên nhân duy nhất của mọi OfflineGenerationError. Manifest vẫn cần phù hợp với templates, plugin, theme và cấu hình nén của lần triển khai.

Tạo bản chart riêng và script patch; không sửa trực tiếp chart gốc:

```bash
(
set -eu
test -f ~/osh-lab/charts/horizon/Chart.yaml
if [ ! -d ~/osh-lab/charts/horizon-octavia ]; then
  cp -a ~/osh-lab/charts/horizon ~/osh-lab/charts/horizon-octavia
fi
)
cat > ~/osh-lab/horizon-octavia/patch-horizon-static.py <<'PY'
#!/usr/bin/env python3
"""Patch a copied Horizon chart; safe to run again."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: patch-horizon-static.py CHART_DIR")
path = Path(sys.argv[1]).expanduser() / "templates/bin/_horizon.sh.tpl"
text = path.read_text()
marker = "  /tmp/manage.py collectstatic --noinput"
addition = '  # Return to Horizon after compiling plugin translations.\n  cd "${SITE_PACKAGES_ROOT}/openstack_dashboard"\n'
if text.count(marker) != 1:
    raise SystemExit("Unexpected startup script: collectstatic marker missing or duplicated")
if addition + marker not in text:
    path.write_text(text.replace(marker, addition + marker, 1))
print("Startup script ready:", path)
PY
python3 ~/osh-lab/horizon-octavia/patch-horizon-static.py \
  ~/osh-lab/charts/horizon-octavia
```

Script patch có thể chạy lại mà không chèn trùng. Nếu template chart đã đổi và không còn marker dự kiến, script dừng để đối chiếu phiên bản. Không chạy trực tiếp file .tpl: đây là nguồn Helm tạo ConfigMap horizon-bin, rồi pod mount script thành /tmp/horizon.sh.

Sau này nâng chart phải áp dụng lại patch lên chart mới, kiểm tra render và rollout. Version trong Chart.yaml vẫn là version upstream; giữ script patch trong Git để giải thích khác biệt của chart local.

### 13.8. Cấu hình Helm và triển khai Horizon

Tạo override public với image digest đã kiểm tra, hostname controlplane và danh sách panel. Không thêm nhãn openstack-control-plane lên worker chỉ để Horizon được schedule. extra_panels là danh sách nên values mới thay toàn bộ danh sách cũ; luồng này chỉ bật octavia_dashboard vì image 2025.2 đã kiểm tra không có Heat/TaaS dashboard.


```bash
: "${HORIZON_IMAGE:?Nạp digest image đã kiểm tra}"
: "${HORIZON_NODE:?Nạp thông số ở mục 13.2}"
cat > ~/osh-lab/horizon-octavia/octavia-values.yaml <<EOF
images:
  tags:
    horizon: $HORIZON_IMAGE
labels:
  dashboard:
    node_selector_key: kubernetes.io/hostname
    node_selector_value: $HORIZON_NODE
conf:
  horizon:
    extra_panels:
      - octavia_dashboard
EOF
```

Export vị trí snapshot ra shell hiện tại để phần rollback dùng đúng lần cập nhật. Baseline lấy toàn bộ values đang hoạt động, giúp giữ cấu hình HTTPS, CSRF/cookie, Keystone/internal endpoints và các tùy chỉnh trước đó.

```bash
export HORIZON_WORK="$HOME/osh-lab/horizon-version/octavia-final-$(date +%Y%m%d-%H%M%S)"
(
set -eu
umask 077
CHART="$HOME/osh-lab/charts/horizon-octavia"
VALUES="$HOME/osh-lab/horizon-octavia/octavia-values.yaml"
mkdir -p "$HORIZON_WORK"
helm get values horizon -n openstack --all -o yaml > "$HORIZON_WORK/before.yaml"
helm history horizon -n openstack -o json > "$HORIZON_WORK/history.json"

python3 - "$CHART" "$HORIZON_WORK" <<'PY'
import json, sys
from pathlib import Path
import yaml
chart, work = map(Path, sys.argv[1:])
meta = yaml.safe_load((chart / "Chart.yaml").read_text())
history = json.loads((work / "history.json").read_text())
latest = max(history, key=lambda x: int(x["revision"]))
assert latest["status"] == "deployed", "Release chưa deployed; xử lý trạng thái trước"
assert latest["chart"] == "horizon-" + str(meta["version"]), "Chart local khác release"
(work / "rollback-revision.txt").write_text(str(latest["revision"]) + "\n")
PY

helm template horizon "$CHART" -n openstack --is-upgrade \
  -f "$HORIZON_WORK/before.yaml" -f "$VALUES" > "$HORIZON_WORK/rendered.yaml"

python3 - "$HORIZON_WORK/rendered.yaml" <<'PY'
import os, sys
import yaml
docs = [d for d in yaml.safe_load_all(open(sys.argv[1])) if isinstance(d, dict)]
deployment = next(d for d in docs if d.get("kind") == "Deployment"
                  and d["metadata"]["name"] == "horizon")
spec = deployment["spec"]["template"]["spec"]
assert spec["nodeSelector"] == {"kubernetes.io/hostname": os.environ["HORIZON_NODE"]}
container = next(c for c in spec["containers"] if c["name"] == "horizon")
assert container["image"] == os.environ["HORIZON_IMAGE"]
script = next(d for d in docs if d.get("kind") == "ConfigMap"
              and d["metadata"]["name"] == "horizon-bin")["data"]["horizon.sh"]
assert 'cd "${SITE_PACKAGES_ROOT}/openstack_dashboard"' in script
print("PASS: image/node/startup script trong render đúng")
PY

printf 'Snapshot: %s\n' "$HORIZON_WORK"
helm upgrade horizon "$CHART" -n openstack \
  -f "$HORIZON_WORK/before.yaml" -f "$VALUES" \
  --no-hooks --wait --timeout 10m

kubectl -n openstack rollout status deployment/horizon --timeout=300s
kubectl -n openstack get pods -l application=horizon,component=server -o wide
kubectl -n openstack exec deployment/horizon -c horizon -- \
  /var/lib/openstack/bin/python3 -c '
from importlib.metadata import version
print("Horizon:", version("horizon"))
print("Octavia Dashboard:", version("octavia-dashboard"))
'
)
```

--no-hooks dùng cho cập nhật giao diện trên release đã tồn tại, bỏ các hook DB init/sync không cần trong thay đổi này. Không áp dụng mặc định khi cài mới Horizon hoặc nâng phiên bản cần migration. --wait và rollout status là hai kiểm tra khác nhau: rollout status xác nhận pod mới đã hoàn tất thay thế; chỉ exec sau đó để tránh đọc pod cũ đang Terminating.

Lỗi ở bước kiểm tra hoặc render ngăn quá trình chuyển sang upgrade. Snapshot và rendered manifests có thể chứa Secret hoặc thông tin xác thực, nên được lưu riêng tư và loại khỏi Git cũng như các bản công bố.

### 13.9. Nghiệm thu giao diện quản lý Load Balancer

Kết quả kỹ thuật cần có: pod Horizon mới 1/1 Running trên controlplane, rollout hoàn tất, package đúng và trang đăng nhập mở được qua URL HTTPS đã cấu hình ở tài liệu Gateway.

Sau khi đăng nhập lại Horizon, lựa chọn project sở hữu load balancer và truy cập Project → Network → Load Balancers. Vị trí menu có thể khác theo theme; mục Load Balancers thuộc giao diện Project. Tài khoản phải có quyền truy vấn LB trong project đó. study-lb của cụm tham chiếu sử dụng VIP 10.20.0.50; các cụm khác sử dụng tài nguyên và địa chỉ được cấp phát riêng.

Thấy menu xác nhận plugin đã được nạp; mở danh sách và chi tiết LB xác nhận Horizon truy cập được Octavia API bằng cấu hình/catalog đang dùng. Giao diện không thay đổi giới hạn của OVN provider: các chức năng L7/TLS không được coi là đã hỗ trợ chỉ vì có nút/menu. Theo mục 1 để chọn OVN hoặc Amphora theo yêu cầu bài lab.

### 13.10. Quản lý phiên bản và hoàn tác triển khai

Cấu hình đang hoạt động trong lần nghiệm thu 13/10/2026:

| Thành phần | Giá trị |
|---|---|
| Release | horizon, namespace openstack, revision 10 |
| Image | ghcr.io/erintn2025/horizon-octavia@sha256:5a0e344e9ef4193ca2da2c7f98a7f3a131603c715c94770a1a2ce8b0b6952587 |
| Node | controlplane-01 |
| Chart tùy chỉnh thực tế lúc nghiệm thu | ~/osh-lab/horizon-version/persistent-static-20261013-110039/horizon |
| Các package | Horizon 25.5.3.dev10, Django 4.2.23, Octavia Dashboard 16.0.0 |
| Thay đổi chart | cd về openstack_dashboard trước collectstatic/compress |

Vị trí ~/osh-lab/charts/horizon-octavia trong luồng trên là nơi chuẩn hóa cho lần triển khai tiếp theo; không khẳng định thư mục này đã tồn tại trên bastion cũ. Trên cụm đang chạy dùng chart tùy chỉnh thực tế trong bảng cho tới khi sao chép/chuẩn hóa nó sang vị trí mới. Chart gốc và chart tùy chỉnh có thể hiển thị cùng version trong Chart.yaml nhưng khác script khởi động. Việc cập nhật phải sử dụng đúng nguồn chart đã lưu cùng bản triển khai.

Mỗi lần đổi image hoặc thêm panel: build image/tag mới → push → lấy digest → kiểm tra trên node → sửa octavia-values.yaml → chạy lại mục 13.8. Giữ các panel đã cài mà muốn tiếp tục sử dụng khi thay extra_panels. Nâng backend Heat/TaaS/Barbican là công việc riêng; thêm package giao diện không tự triển khai các backend đó.

Rollback là quy trình riêng, chỉ chạy khi cần quay lại snapshot trước một lần upgrade:

```bash
(
set -eu
: "${HORIZON_WORK:?Đặt HORIZON_WORK bằng đường dẫn snapshot của lần upgrade cần hoàn tác}"
REVISION=$(cat "$HORIZON_WORK/rollback-revision.txt")
helm rollback horizon "$REVISION" -n openstack \
  --no-hooks --wait --timeout 10m
kubectl -n openstack rollout status deployment/horizon --timeout=300s
)
```

Rollback thay revision Horizon; không rollback dữ liệu Octavia hoặc LB. Khi nâng phiên bản có migration, cần đánh giá rollback DB riêng, không dùng quy trình panel này.

### 13.11. Phân tích sự cố trong quá trình triển khai

| Biểu hiện | Giải thích từ kết quả thực tế | Điều chỉnh giữ trong luồng cuối |
|---|---|---|
| Base image digest trả not found | Digest cũ từng tải được nhưng registry không còn trả image khi build lại. Pod đã cache vẫn có thể chạy | Kiểm tra nguồn/version và pin digest còn tải được; lưu image đã đóng gói trên registry của lab |
| No module named pip | Virtualenv trong image nền thiếu pip; pip trên bastion không bổ sung vào image | Bootstrap pip trong đúng Python /var/lib/openstack |
| pip tìm /tmp/horizon rồi báo không tồn tại | pip freeze giữ direct reference tới nguồn cài đã bị dọn | Constraints chỉ giữ tên-package==version bằng pip list --format=freeze |
| Build không phân giải bootstrap.pypa.io | DNS của mạng build không hoạt động ở thời điểm đó | Dùng mạng bastion cho RUN bằng --network=host; vẫn cần DNS bastion hoạt động |
| GHCR login được nhưng push permission_denied | Token được chấp nhận để login nhưng thiếu scope ghi package | PAT classic có write:packages; public package cho node tải không cần credentials |
| ImagePullBackOff | Có thể do quyền, tag sai, DNS hoặc kết nối; tên trạng thái không xác định nguyên nhân | Đọc Events và giữ probe khi lỗi. Trong lần flat1, lỗi cụ thể là DNS ghcr.io trên controlplane |
| chown: invalid user: horizon / no users found | Trên controlplane file passwd/group rỗng; cùng image trên worker và Docker bastion có user | Kiểm tra trên đúng node; đóng filesystem đầy đủ thành image một layer. Tạo user riêng hoặc chỉ pull lại không giải quyết đầy đủ |
| PyMySQL thiếu install_as_MySQLdb | File __init__.py là 4265 byte trên bastion nhưng 0 byte trên controlplane; envvars và a2enmod cũng 0 byte | Không cài lại package hay sửa DB URL để chữa triệu chứng; image một layer đã vượt kiểm tra FILES_OK |
| Xóa tag/digest rồi pull vẫn lỗi | Xóa tham chiếu image không đảm bảo mọi layer/snapshot đã bị dọn; chưa xác định gốc lỗi runtime | Không lặp việc pull hoặc xóa toàn bộ /var/lib/containerd; giữ kết luận giới hạn ở bằng chứng quan sát |
| PackageNotFoundError sau upgrade | Exec vào pod cũ đang Terminating khi pod mới còn Init | Chờ rollout xong trước kiểm tra package; nếu lỗi startup thì xem đúng tên pod mới |
| Running nhưng Ready 0/1, HTTP 500 | Container đang chạy không đồng nghĩa web đáp ứng thành công | Xem exception ứng dụng; không tăng timeout probe để che HTTP 500 |
| OfflineGenerationError ở /auth/login/ | Manifest nén không có key mà trang đăng nhập đang yêu cầu | Startup quay về thư mục Horizon trước collectstatic/compress. Điều chỉnh đã qua rollout mới; không dựa vào sửa manifest thủ công trong pod |
| container not found khi exec | Container crash đang ở khoảng nghỉ trước lần chạy tiếp theo | Dùng pod probe độc lập hoặc log current/previous, không kết luận package mất chỉ từ lỗi exec |
| Metrics API not available | kubectl top cần Metrics Server; lỗi này không chứng minh thiếu RAM | Không dùng nó làm bằng chứng OOM; exit code, reason và logs mới xác định lỗi |
| Warning PodSecurity restricted | Trong lab hiện tại admission cho phép tạo pod, kèm warning | Phân biệt warning với rejection. Cụm enforce restricted cần thiết kế securityContext phù hợp, không mặc định các lệnh root sẽ được chấp nhận |
| Apache ServerName / distutils warning | Đã xuất hiện nhưng không ngăn pod đạt Ready | Không coi là nguyên nhân khi không có lỗi khác kèm theo |

DNS ghcr.io từng thất bại giữa lúc tải layer rồi lần retry sau thành công. 127.0.0.53 trong thông báo là địa chỉ resolver, không phải lệnh Bash; không dán dòng báo lỗi thành lệnh. Không suy từ lỗi pull trên Talos rằng DNS bastion hay CoreDNS pod cũng đang lỗi.

Filesystem image 0 byte trên controlplane là bất thường chưa được giải thích tận gốc. Image một layer là workaround đã chạy được, không khẳng định mọi image của node đều khỏe hoặc lỗi runtime đã hết. Tại lúc kiểm tra filesystem còn 13.47 GiB trống, nên không có bằng chứng ổ đang đầy ở thời điểm đó; cũng không loại trừ sự cố trước đó.

### 13.12. Quản lý cấu hình và dữ liệu tạm

rootfs.tar chỉ phục vụ đóng image và có thể tạo lại từ script + image nguồn còn tồn tại. Trong phiên triển khai đã nghiệm thu, archive nằm tại ~/osh-lab/horizon-flat/rootfs.tar; luồng chuẩn hóa ở trên dùng ~/osh-lab/horizon-octavia/flat/rootfs.tar. Thư mục ~/osh-lab/horizon-account-fix chứa Dockerfile và file tài khoản cho thử nghiệm fix2, không phải cấu hình Helm đang sử dụng. Sau khi image cuối đã push, pod mới Ready và giao diện được kiểm tra, có thể xóa archive tạo bởi luồng chuẩn hóa để giảm dung lượng:

```bash
rm -f -- "$HOME/osh-lab/horizon-octavia/flat/rootfs.tar"
```

Giữ Dockerfile, script flatten, script patch, chart/archive upstream đúng pin, public override và image digest cuối. Không cần lưu mọi tag fix1/fix2 hoặc image nguồn ở registry chỉ để quản trị release hiện tại, nhưng phải giữ image mà deployment hoặc revision rollback còn cần tải. Việc xóa image trên bastion không xóa image trên GHCR hay cache Talos, và ngược lại.

Pod probe thất bại được giữ để chẩn đoán; sau khi đã đọc log, liệt kê pod kiểm tra rồi xóa theo tên cụ thể. Không xóa theo nhãn application=horizon vì đó là pod phục vụ dashboard.

Các snapshot before/current values và rendered manifests có thể chứa mật khẩu. Phần được lưu trong Git gồm cấu hình public ở octavia-values.yaml, mã nguồn script và phần sửa chart. Thư mục .docker/config.json chứa credentials đăng nhập registry, không phải cấu hình triển khai Horizon và không đưa vào repo.
