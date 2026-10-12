# 08. Octavia OVN trên lab Talos: quy trình cấu hình cuối

Tài liệu này giữ một luồng cài đặt theo cấu hình đã hoạt động. Không chạy các phương án sai rồi sửa lại. Bắt đầu khi core OpenStack, RabbitMQ Operator và Gateway HTTPS đã có. Chưa hướng dẫn cài Talos.

**Trạng thái xác nhận:** Octavia cài thành công; Gateway/API/provider hoạt động; study-lb đã ACTIVE/ONLINE. Chưa có listener/pool/member/backend và chưa nghiệm thu traffic. Dựng lại trên cụm sạch chưa được thử trọn quy trình.

Nếu Octavia đã được cài, không chạy lại bước tạo release/LB: dùng phần quản trị mục 10. UUID/IP ở kết quả nghiệm thu chỉ là tham chiếu cụm hiện tại.

| File | Vai trò | Giữ/xóa |
|---|---|---|
| tools/prepare-octavia-rabbitmq.py | Sinh credentials và tạo topology broker | Giữ script nguồn |
| tools/prepare-octavia-credentials.py | Lấy admin từ Secret, sinh DB/Keystone/cache credentials | Giữ script nguồn |
| tools/prepare-octavia-ovn.py | Tạo lab values/post-renderer và kiểm tra render | Giữ script nguồn |
| ~/osh-lab/charts/octavia/ | Chart pin, kèm helm-toolkit | Giữ chart/archive |
| ~/osh-lab/octavia/lab-values.yaml | Cấu hình provider, endpoint, images/resources | Giữ cấu hình cuối |
| ~/osh-lab/octavia/credentials-private.yaml | DB/Keystone/admin/cache credentials | Private; giữ sau cài; không commit |
| ~/osh-lab/octavia/rabbitmq-private.yaml | Broker endpoint/password Octavia | Private; giữ sau cài; không commit |
| ~/osh-lab/octavia/post-render.py | Ghép agent/socket/tolerations | Luôn dùng khi render/install/upgrade |
| ~/osh-lab/octavia/rendered.yaml | Output render chứa Secrets | Có thể tạo lại; không commit/gửi |
| ~/osh-lab/gateway-api/manifests/octavia-route.yaml | Route HTTPS về octavia-api:9876 | Giữ manifest |

Các script dùng Python3/PyYAML và kubectl/Helm đúng context. Script generator ghi đè lab-values.yaml/post-render.py: chỉnh nguồn generator nếu muốn giữ thay đổi qua lần sinh tiếp theo. Không xóa private values rồi sinh password mới cho release đang chạy.
## 1. Kết luận từ source đang có

Các file Genestack liên quan đã copy vào [reference/genestack](../reference/genestack/docs/openstack-octavia.md). Không cần giữ folder Genestack bên ngoài để đọc những phần được trích này. Bản source là tài liệu để đối chiếu, không phải installer đã chỉnh xong cho lab.

| Nguồn local | Điều source thực sự làm |
|---|---|
| [openstack-octavia.md](../reference/genestack/docs/openstack-octavia.md) | Chuẩn bị secrets, preconf Amphora, đưa values sinh ra vào thư mục overrides, chạy installer |
| [install-octavia.sh](../reference/genestack/bin/install-octavia.sh) | Pin chart, đọc base/global/custom, lấy secrets, lấy NB/SB Service, xử lý Kube-OVN TLS, Helm với post-renderer |
| [base values](../reference/genestack/base-helm-configs/octavia/octavia-helm-overrides.yaml) | Bật providers ovn+amphora, mặc định amphora, ACTIVE_STANDBY; DB/MQ mặc định theo Genestack |
| [Kustomize](../reference/genestack/base-kustomize/octavia/base/kustomization.yaml) | Thêm driver-agent sidecar trong API pod, shared /var/run/octavia, MariaDB/RabbitMQ CR, HPA và policy |
| [post-renderer](../reference/genestack/base-kustomize/octavia/post-renderer.sh) | Gọi framework Kustomize; thêm/xóa TLS mounts theo trạng thái Kube-OVN |
| [preconf role](../reference/genestack/ansible/roles/octavia_preconf/README.md) | Network/subnet/SG, ports, quota, keypair/flavor/image, certificate, Helm values |
| [LB workflow](../reference/genestack/docs/octavia-loadbalancer-setup-guide.md) | LB → listener → pool → members → monitor; chọn provider explicit |

Chart pin Octavia trong bản repo này: **2026.1.8+d03dd061a**; Barbican: **2026.1.8+a659ab8a2**. Pin giữ ở [versions](../reference/genestack/helm-chart-versions.yaml). Chart Octavia được tải riêng theo pin ở bước 3; assets ban đầu từ bastion không có chart này. Đây là chart version, không tự đảm bảo image tag -latest bất biến.


### Octavia khác Envoy Gateway

Envoy nhận HTTPS cho API/dashboard. Octavia API quản lý load balancer trong cloud tenant. Thêm route octavia.lab.test chỉ mở API, không tạo LB cho VM. Amphora image qcow2 là VM image đưa vào Glance, khác container image octavia chạy API/worker trong Kubernetes.

### Chọn provider

| Provider | Đường thực thi | Cần chuẩn bị |
|---|---|---|
| OVN | Octavia API + driver-agent → OVN NB/SB → OVS dataplane | Neutron OVN, DB connectivity, driver-agent/socket đúng, tenant network |
| Amphora | Octavia worker → Nova tạo VM Amphora → cấu hình HAProxy | VM boot được, mgmt network/ports/SG, certificate, Glance image, flavor, worker/health manager reachability |

Genestack mặc định Amphora và hỗ trợ OVN. Với lab nhỏ đã shared OVN, có thể test OVN trước để không thêm VM LB; phải ghi rõ đây là đổi default/provider của lab so với source. Nếu bài yêu cầu L7/TLS termination ở tenant LB, không coi OVN demo TCP là đã đáp ứng: đối chiếu capability provider của phiên bản đang cài, sau đó chọn Amphora/Barbican cho bài đó.

Không tạo Amphora ACTIVE_STANDBY trên một compute node rồi mặc định anti-affinity/HA sẽ hoạt động. SINGLE là lựa chọn lab khác default Genestack, cần cấu hình explicit và giải thích giới hạn.

### Những điều chỉnh so với installer Genestack

| Phần | Genestack source | Lab đang dùng | Việc phải làm |
|---|---|---|---|
| MariaDB | mariadb-cluster-primary + k8s.mariadb.com CR | OSH mariadb + controller/Jobs | Giữ MariaDB, dùng DB provisioning tương ứng; không apply CR Operator không có |
| RabbitMQ | rabbitmq + secret rabbitmq-default-user | rabbitmq-genestack | Đổi host/reference, tạo user/vhost/permission Octavia với Topology Operator |
| Keystone admin secret | keystone-admin.data.password | nova-keystone-admin có OS_* | Đọc key đúng, giữ service credentials mới; không giả định secret gốc tồn tại |
| Memcache key | os-memcached.data.memcache_secret_key | Chưa xác nhận key/config thực tế | Kiểm tra chiến lược cache/key, không dùng random key lệch giữa app/cấu hình |
| Kube-OVN SSL | networking.ENABLE_SSL, TLS Secret nếu true | Cần đọc effective values mới | TCP/SSL và CA/key phải khớp NB/SB, không dùng localhost mặc định |
| HPA | hpa-octavia-api | Lab chưa có Metrics API | Chưa đưa HPA vào lab; replicas/resources chọn theo dung lượng |
| Redis jobboard | Source có endpoint Sentinel, jobboard_enabled=false | Chưa cài Redis | Đọc flags/workload/dependencies thực tế; không cài Redis chỉ vì thấy chuỗi host |
| Kustomize | Thêm driver-agent vào API | Helm thuần sẽ bỏ phần này | Giữ cùng ý tưởng shared socket/sidecar, kiểm tra render sau post-render |

Installer gốc còn in command có giá trị password sau khi lấy Secrets. Không chạy nguyên script rồi gửi stdout lên chat; bản hướng dẫn lab phải tránh in credentials/đặt chúng vào lịch sử shell.

## 2. Chuẩn bị file và đầu vào

Chạy trên bastion Ubuntu, không chạy Bash trên PowerShell:

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

Luồng này dành cho ENABLE_SSL=False, broker rabbitmq-genestack Ready, node controlplane-01 Ready và Gateway HTTPS có sẵn. Nếu khác, chỉnh generator trước; không áp dụng TCP cho OVN SSL. Project/domain và admin passwords được đọc từ nova-keystone-admin, nova-keystone-user, nova-db-admin; không dùng mẫu password từ chart.

Copy nguyên folder học sang ~/Openstack-Lab-Learning. Nếu chỉ chuyển ba script, chạy lệnh sau **trên PowerShell Windows**, sau khi đã tạo thư mục nhận trên bastion; đổi IP/path theo máy thực tế:

```powershell
scp "D:\system-intership\NNTrung\Genestack\Openstack-Lab-Learning\tools\prepare-octavia-*.py" bastion@192.168.207.138:~/osh-lab/octavia/
```

Các lệnh bên dưới dùng script ở ~/osh-lab/octavia. Nếu đã copy cả folder, trên bastion:

```bash
cp ~/Openstack-Lab-Learning/tools/prepare-octavia-*.py ~/osh-lab/octavia/
```

Đường dẫn D:\ chỉ có trên Windows. File chart có trên bastion không có nghĩa script Windows đã được chuyển sang.

## 3. Tải chart pin và kiểm tra dependency

Lệnh chỉ ghi file, chưa cài dịch vụ. Dùng archive cache nếu có; không thay chart Talos của dịch vụ khác.

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

helm-toolkit cần unpacked. Không dependency update chỉ để thử nếu dependency đã có. Chart local tránh tải lại chart, nhưng node vẫn cần pull image. Image Genestack có tag mutable; dựng offline cần giữ image/digest theo [bài 04](04-Images.md), không chỉ giữ tgz.

## 4. Tạo topology RabbitMQ

Script sinh password Octavia một lần, lưu rabbitmq-private.yaml, tạo Secret và User/Vhost/Permission trên broker mới. Vhost mặc định quorum theo Genestack; không thêm policy group size 3 cho lab một replica. Chạy lại giữ password và dừng nếu file/Secret không khớp.

```bash
python3 ~/osh-lab/octavia/prepare-octavia-rabbitmq.py
kubectl -n openstack wait users.rabbitmq.com/gs-octavia-user --for=condition=Ready --timeout=180s
kubectl -n openstack wait vhosts.rabbitmq.com/gs-octavia-vhost --for=condition=Ready --timeout=180s
kubectl -n openstack wait permissions.rabbitmq.com/gs-octavia-permission --for=condition=Ready --timeout=180s
```

Không dùng Rabbit init Job của chart để provision broker Operator. Không đổi credentials các service hiện tại.

## 5. Tạo credentials DB/Keystone

```bash
python3 ~/osh-lab/octavia/prepare-octavia-credentials.py
```

Script đọc admin credentials qua kubectl, dùng project/domain của service hiện tại, sinh password DB/Keystone và cache encryption key riêng cho Octavia. File private mode 600; không in passwords. Key cache dùng thống nhất trong cấu hình Octavia, không sửa Memcached server. Chưa tạo DB/user ở bước này; Job của chart sẽ thực hiện khi install. Chạy lại giữ password Octavia, cập nhật admin từ Secret hiện tại.

## 6. Tạo cấu hình cuối và render

```bash
python3 ~/osh-lab/octavia/prepare-octavia-ovn.py
```

Generator lấy NB/SB Service và HTTPS NodePort thực tế, tạo lab-values.yaml/post-render.py và render theo thứ tự lab → credentials-private → rabbitmq-private. Kiểm tra API/agent socket, DB/MQ/auth credentials, Neutron adapter, đủ DB/Keystone Jobs, không có Rabbit init/Amphora workload.

Cấu hình cuối cần hiểu:

- Provider ovn, agent ovn; API một process/hai threads; không thêm VM Amphora.
- Job DB init/sync và Keystone Jobs bật; worker/health-manager/housekeeping/boot/image-sync/Rabbit-init tắt.
- Jobboard tắt vì không có Valkey. Quorum flags khớp vhost broker.
- API/agent cùng Pod, chung emptyDir /var/run/octavia và config/snippets. Hai Deployment độc lập với emptyDir riêng không chia sẻ socket.
- Service auth explicit dùng tài khoản Octavia; mặc định chart có thể dùng admin.
- **Neutron adapter có valid_interfaces=internal, endpoint_type=internalURL và endpoint_override=http://neutron-server.openstack.svc.cluster.local:9696.** service_auth.interface hoặc biến CLI trên bastion không thay adapter này; thiếu nó có thể khiến create LB gọi public neutron:80 không tồn tại dù provider list đã PASS.
- Agent dùng --config-file /etc/octavia/octavia.conf và --config-dir cho thư mục snippets. Không truyền tên file vào --config-dir.
- API/agent UID 0 theo patch Genestack; có control-plane toleration. Đây là cấu hình lab, chưa tương thích PodSecurity restricted. API request 512Mi/limit1536Mi, agent request128Mi/limit512Mi; không HPA khi chưa có Metrics API.

Render PASS kiểm tra cấu hình, chưa chứng minh runtime. Không tìm settings trong YAML Secret bằng grep raw: nội dung có thể base64. Không gửi rendered.yaml hoặc private values.

## 7. Cài release Octavia OVN

Bastion đã render PASS: OVN-only, API/agent chia sẻ socket, DB/MQ/auth khớp; đủ octavia-db-init, octavia-db-sync, octavia-ks-service, octavia-ks-user và octavia-ks-endpoints. Public API dùng HTTPS NodePort thực tế. Kết quả runtime của cụm tham chiếu được ghi riêng ở mục 11.

Cài bằng chart local và đúng ba file values đã kiểm tra. Post-renderer phải được dùng cả khi cài và khi upgrade sau này. Không kubectl apply rendered.yaml thay Helm, vì sẽ mất xử lý hooks/release.

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

Dùng install cho lần đầu; nếu release đã tồn tại thì dừng, xem helm status/history rồi quyết định, không uninstall hoặc tạo password mới. Không dùng --wait ở lần cài này: Job DB init của chart là post-install hook, trong khi API init chờ DB/Keystone Jobs. Helm đợi API Ready trước post-install hooks có thể tạo vòng chờ. Helm vẫn đợi hook Job hoàn tất theo timeout; rollout API được kiểm tra riêng sau đó. Hook khác nếu fail/timeout thì giữ output và kiểm tra Job thay vì chạy mù lại.

```bash
helm -n openstack status octavia
kubectl -n openstack get jobs,pods -l application=octavia -o wide
kubectl -n openstack rollout status deployment/octavia-api --timeout=300s
kubectl -n openstack get deployment octavia-api \
  -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\n"}{end}'
kubectl -n openstack get svc octavia-api
```

Mong đợi API pod 2/2 Running (octavia-api + octavia-agent), rollout thành công, Service port 9876. Các Job có thể bị Helm xóa theo hook-delete-policy sau thành công, không mặc định việc không còn Job là lỗi. Sau runtime Ready mới thêm HTTPRoute và dùng CLI provider list. Helm deployed/Pod Ready chưa phải nghiệm thu traffic LB.

Nếu install fail, gửi output lệnh install và bảng jobs/pods; không gửi file private hoặc rendered.yaml. Chưa thay đổi public catalog/route các service hiện tại; Keystone Jobs đăng ký service/user/endpoints riêng Octavia.

## 8. Mở Octavia API qua Gateway HTTPS

Output người chạy cung cấp ngày 09/10/2026 xác nhận release revision 1 deployed; năm Jobs Complete; rollout octavia-api thành công, Service ClusterIP 10.96.128.238 port 9876. Bảng pod trước rollout là 1/2 Running, sau đó rollout hoàn tất; không suy ra agent chưa từng restart hoặc LB đã chạy chỉ từ rollout. PodSecurity restricted warnings là cảnh báo trong output, không chặn lần cài này. UID 0 của API/agent là lựa chọn lab theo patch Genestack, chưa tương thích restricted policy.

Tạo route trong thư mục cấu hình bastion rồi apply. Route chỉ mở API HTTPS, không tạo tenant LB.

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

Chờ route Accepted=True và ResolvedRefs=True. API root thường trả discovery JSON; output curl dùng --resolve nên chưa cần hosts. Node IP phải đổi nếu dựng cluster khác.

### CLI qua Gateway, không port-forward

Chuẩn bị một lần theo [bài 10: admin.sh](10-Admin-Environment.md). Sau đó chỉ source một file để có credentials và endpoint Gateway cho OpenStack/Octavia:

```bash
source ~/osh-lab/bin/admin.sh
timeout 30s openstack loadbalancer provider list
timeout 30s openstack subnet list
```

--insecure dành cho certificate tự ký lab, có thể thay bằng CA trust khi chuẩn bị certificate. Provider cần có ovn; đây mới xác nhận API/provider được đăng ký, chưa xác nhận agent/OVN dataplane xử lý LB. Sau đó chọn subnet VIP và hai backend thật để nghiệm thu mục 9. Kết quả của cụm đã nghiệm thu ghi ở mục 11.

## 9. Tạo LB và chọn backend thật

Chạy sau provider list có ovn. UUID subnet mỗi cụm khác nhau: chọn từ subnet list, không copy UUID nghiệm thu cụm cũ.

```bash
read -r -p 'VIP subnet UUID: ' VIP_SUBNET_ID
: "${VIP_SUBNET_ID:?Chua chon subnet}"
timeout 30s openstack --insecure loadbalancer list
```

Nếu study-lb chưa tồn tại, tạo một lần:

```bash
timeout 30s openstack --insecure loadbalancer create \
  --name study-lb --provider ovn --vip-subnet-id "$VIP_SUBNET_ID"
timeout 30s openstack --insecure loadbalancer show study-lb \
  -c id -c provider -c vip_address -c provisioning_status -c operating_status
```

PENDING_CREATE: chờ vài giây rồi show lại, không create lại. timeout exit124 nghĩa là hết thời gian toàn tiến trình; request có thể đã gửi. Luôn list/show trước khi thử create lần nữa. ACTIVE/ONLINE mới xác nhận provisioning, không chứng minh backend/traffic.

```bash
read -r -p 'Tenant network UUID: ' TENANT_NETWORK_ID
: "${TENANT_NETWORK_ID:?Chua chon network}"
timeout 30s openstack --insecure port list --network "$TENANT_NETWORK_ID"
read -r -p 'Port UUID muon kiem tra backend: ' BACKEND_PORT_ID
: "${BACKEND_PORT_ID:?Chua chon port}"
timeout 30s openstack --insecure port show "$BACKEND_PORT_ID" \
  -c id -c fixed_ips -c device_owner -c device_id -c status
```

Nếu cần xem VM, dùng Nova Gateway hiện có trong shell đã nạp credentials:

```bash
timeout 30s openstack server list
```

Port DOWN/IP không tự chứng minh có VM/backend HTTP. VIP OVN không gắn vNIC như VM, nên không đánh giá LB chỉ bằng port status. Backend phải thật sự nghe TCP80, có security group phù hợp. Máy test cần route tới VIP tenant; NodePort API không cung cấp đường tới VIP.

**Chưa thực hiện:** listener TCP → pool SOURCE_IP_PORT → members → health monitor phù hợp capability → thử traffic. Đọc [LB guide Genestack](../reference/genestack/docs/octavia-loadbalancer-setup-guide.md) để học các tài nguyên; chỉ thêm backend sau khi kiểm tra VM/ứng dụng thực tế.

## 10. Cập nhật sau khi đã cài

Sửa generator/nguồn chính, chạy render và kiểm tra PASS trước. Luôn giữ private credentials đang dùng. Generator cập nhật endpoint theo Service mới nhưng không phải công cụ tự sửa mọi khác biệt môi trường.

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

Job có thể chạy lại. Không kubectl apply rendered.yaml thay Helm; không sửa file trong container làm cấu hình lâu dài. Render/hook lỗi thì kiểm tra tại bước đó, không tạo password mới hoặc uninstall để thử. Chẩn đoán khi runtime lỗi:

```bash
helm -n openstack history octavia
kubectl -n openstack get pods,jobs -l application=octavia -o wide
kubectl -n openstack logs deployment/octavia-api -c octavia-agent --since=5m --tail=80
kubectl -n openstack logs deployment/octavia-api -c octavia-api --since=5m --tail=80
```

Log có thể chứa thông tin nhạy cảm; kiểm tra trước khi chia sẻ. Provider list thành công chỉ kiểm tra API; create LB mới đi sâu vào Neutron/agent/OVN.

## 11. Kết quả nghiệm thu cụm hiện tại

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

UUID/IP bảng này không đưa vào lệnh cài mới. Cấu hình cuối đã tích hợp Neutron internal; không có bước cài sai rồi upgrade sửa lại trong luồng dựng mới.

## 12. Amphora preconf: cần hiểu trước khi chạy Ansible

[Playbook](../reference/genestack/ansible/playbooks/octavia-preconf-main.yaml) và role được giữ local. Tasks có openstack.cloud.* với interface public hardcode, shell scripts dùng OS_CLOUD=default và cloud endpoints. Đặt mỗi OS_AUTH_URL=127.0.0.1 không đủ khiến mọi task dùng port-forward.

Cần chuẩn bị auth/catalog mà máy chạy role truy cập được và chỉnh những task interface/cloud assumptions trước. Dependencies gồm Ansible, openstacksdk/python-openstackclient/kubernetes và các collections dùng thực tế (openstack.cloud, community.crypto, kubernetes.core nếu tasks gọi); giữ versions/requirements sau khi đã chạy kiểm tra, không đoán pip freeze của venv cũ.

Role tạo lb-mgmt-net Geneve/subnet 172.16.29.0/24 theo defaults. Không dùng CIDR này nếu trùng pod/service/tenant/LAN. Flavor mặc định 2vCPU/1Gi RAM/5GB disk. Image nguồn là test-only Amphora Ubuntu noble qcow2; đây là image test, không phải container Octavia và không coi là production image.

Role còn cần mgmt ports cho worker/health manager và security rules; trên Talos phải kiểm tra cách pod gắn management network so với Kube-OVN của lab. Certificate giữa controller-Amphora khác certificate wildcard của browser. Generated amphora values có nhiều mounts/list; merge chúng có thể đè mounts khác nên kiểm tra render cuối.

Redis Sentinel endpoints trong base không tự đồng nghĩa phải cài Redis; jobboard_enabled=false ở bản source đang đọc. Muốn bật jobboard/HA thì thực hiện phần Redis tương ứng và test riêng.

## 13. Giao diện Load Balancer trên Horizon

### 13.1. Trạng thái đã xác nhận

Octavia API/provider OVN đã hoạt động và `study-lb` đạt ACTIVE/ONLINE. Giao diện Horizon là phần riêng: kiểm tra trong container Horizon hiện tại trả về `Octavia Dashboard: Chưa có trong image` và `Panel đang bật: Chưa thấy`. Vì vậy chưa thể bật giao diện chỉ bằng một giá trị Helm; image phải chứa package `octavia-dashboard` trước. Chưa triển khai hoặc nghiệm thu giao diện Load Balancer.

Genestack dùng image `ghcr.io/rackerlabs/genestack-images/horizon:2026.1-latest` trong `base-helm-configs/horizon/horizon-helm-overrides.yaml`; lab đang dùng image Airship. Tài liệu `docs/openstack-horizon.md` hướng dẫn cài Horizon nhưng không có bước riêng bật Octavia Dashboard. Chưa xác minh image Genestack chứa plugin nên không coi việc đổi image là cách sửa đã được kiểm tra.

Theo [hướng dẫn Octavia Dashboard 2026.1](https://docs.openstack.org/octavia-dashboard/2026.1/installation.html), cần cài package, bật panel `_1482_project_load_balancer_panel.py`, chuẩn bị static files nếu dùng compressor rồi khởi động lại web server. Với chart đang lưu trong repo, `conf.horizon.extra_panels` tạo liên kết panel khi Horizon khởi động và startup script xử lý static files. Package vẫn phải được cài trong cùng môi trường Python mà Horizon sử dụng.

### 13.2. Cách triển khai bền vững

1. Xác định image và môi trường Python Horizon thực tế bằng lệnh dưới.
2. Chuẩn bị image Horizon chứa `octavia-dashboard` tương thích release 2026.1. Giữ Dockerfile, phiên bản package và digest image trong repo; package có thể được cài vào virtualenv nên không đoán đường dẫn pip.
3. Lưu file override riêng cho image và `conf.horizon.extra_panels`. Danh sách panel phải giữ các plugin hiện có rồi thêm `octavia_dashboard`, vì Helm thay toàn bộ danh sách.
4. Render bằng đúng chart Horizon hiện tại và các values đang dùng; sau đó upgrade bằng cùng các file. Đăng nhập lại, kiểm tra menu Load Balancers và truy vấn Octavia.

Không cài package trực tiếp trong pod đang chạy để làm cấu hình lâu dài: pod được tạo lại sẽ mất thay đổi. Các bước build/upgrade sẽ được bổ sung sau khi xác định môi trường image; đoạn dưới chỉ đọc thông tin và không thay đổi release.

Chạy trên bastion để biết image, Python và danh sách panel hiện tại, không in credentials:

```bash
kubectl -n openstack get deployment horizon \
  -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{" image="}{.image}{"\n"}{end}'

kubectl -n openstack exec -i deployment/horizon -c horizon -- python3 - <<'PY'
import sys
from importlib.util import find_spec
print('Python:', sys.executable)
for name in ['openstack_dashboard', 'octavia_dashboard']:
    spec = find_spec(name)
    print(name + ':', spec.origin if spec else 'NOT INSTALLED')
PY

helm get values horizon -n openstack --all -o json |
  python3 -c 'import json,sys; v=json.load(sys.stdin); print("extra_panels:", v.get("conf", {}).get("horizon", {}).get("extra_panels", []))'
```
### 13.3. Môi trường Horizon đã xác định và bước build tiếp theo

Kết quả trên cụm: Python `/var/lib/openstack/bin/python3`, Horizon nằm trong `/var/lib/openstack/lib/python3.12/site-packages/openstack_dashboard`, danh sách `extra_panels` hiện tại là `heat_dashboard` và `neutron_taas_dashboard`. Cần giữ cả hai rồi thêm `octavia_dashboard`.

[Dockerfile](../images/horizon-octavia/Dockerfile) bổ sung package vào đúng virtualenv. Pin `octavia-dashboard==17.0.0` theo [release OpenStack 2026.1](https://releases.openstack.org/gazpacho/index.html). Build giữ phiên bản dependencies đã có bằng constraints; nếu xung đột thì dừng để đối chiếu, không tự nâng Django/Horizon. Dockerfile chưa được build hoặc kiểm tra trên cụm.

Trước khi chọn nơi build và registry để các node tải image, chạy trên bastion:

```bash
command -v docker || true
command -v podman || true
```

Nếu có Docker, kiểm tra daemon:

```bash
docker info --format '{{.ServerVersion}}'
```

Không cần cài Docker vào Talos. Image được build trên bastion hoặc máy có container builder, sau đó lưu vào registry mà node truy cập được. Khi build, truyền `BASE_IMAGE` bằng digest của image hiện tại và `RUNTIME_USER` theo `docker image inspect` để giữ user gốc; ghi lại digest image mới. File Helm override cuối sẽ trỏ tới image đã push và đặt danh sách ba panel trên. Chưa có registry/image mới nên chưa có lệnh Helm upgrade ở bước này.