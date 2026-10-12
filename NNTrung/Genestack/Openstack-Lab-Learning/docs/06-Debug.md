# 06. Đọc lỗi theo đường đi, không thử lệnh ngẫu nhiên

## 1. Sơ đồ tìm vị trí lỗi

Browser → node IP/NodePort → Envoy listener/route → Service endpoint → Horizon → Keystone catalog → API → DB/MQ/storage.

Chọn bước gần triệu chứng nhất, kiểm tra kết quả rồi mới đi sâu. Không restart tất cả ngay khi thấy 500.

| Triệu chứng | Đọc ở đâu đầu tiên | Câu hỏi |
|---|---|---|
| Không kết nối node:port | Network/Service NodePort | Có tới LAN đúng IP/port không? |
| Lỗi certificate | URL hostname, cert SAN/hạn/trust | Có đúng hostname và CA không? |
| Gateway 404 | Gateway listener/HTTPRoute | Host/path có match, route Accepted không? |
| 503/backend unavailable | EndpointSlice, readiness, proxy log | Service có pod Ready không? |
| Horizon Something went wrong / 500 | Log Horizon đúng thời điểm | Exception gọi API/DB/cache nào? |
| ImagePullBackOff | describe pod/events | Registry, auth, CA, DNS hay image tag? |
| Pending | describe pod/events | Affinity, taint, resources hay PVC? |
| PVC Bound nhưng app hỏng | Mount/filesystem/data/application log | Bound không chứng minh dữ liệu đúng/đủ disk |

## 2. Ca thật: HTTPS login 200 nhưng /project/ 500

GET login 200 cho biết browser → Gateway → Horizon hoạt động. Log /project/ báo không resolve neutron.openstack.svc.cluster.local. Service thực là neutron-server:9696; DNS của keystone-api và neutron-server resolve được. Catalog Network internal đã đúng; URL public mới là neutron:80.

Sai nằm ở chọn endpoint_type trong Horizon: internal cần sửa thành internalURL. Sửa values + upgrade xong người dùng xác nhận dashboard chạy, log Volumes/static trả 200. Không cần tắt CSRF, sửa DNS toàn cluster hay tạo Service neutron alias để che URL public sai.

Đây là cách suy luận: lấy hostname từ exception → kiểm tra Service tồn tại → test DNS từ đúng pod → đối chiếu catalog/interface. DNS bastion không resolve cluster hostname và DNS pod không resolve là hai ngữ cảnh khác nhau.

## 3. Lệnh chỉ đọc, chạy khi có lỗi

```bash
kubectl -n openstack get pods -l application=horizon -o wide
kubectl -n openstack logs deployment/horizon -c horizon --since=5m --tail=100
kubectl -n openstack describe httproute horizon-gateway-route
kubectl -n openstack get endpointslices -l kubernetes.io/service-name=horizon-int
```

--since giới hạn khoảng thời gian; --tail giới hạn số dòng. Tạo lại lỗi trên browser rồi đọc log ngay để nối hai sự kiện. Không paste raw Secret/local_settings/password lên chat.

Nếu cần kiểm tra HTTP, dùng GET thay HEAD. Ca lab có HEAD /403 nhưng GET /302, GET login200; không kết luận CSRF từ HEAD:

```bash
HTTPS_NODEPORT=$(kubectl -n envoyproxy-gateway-system get svc openstack-gateway -o jsonpath='{.spec.ports[?(@.port==443)].nodePort}')
: "${HTTPS_NODEPORT:?Gateway chua co HTTPS NodePort}"
curl --max-time 20 -sS -D - -o /dev/null \
  --cacert ~/osh-lab/gateway-api/tls/tls.crt \
  --resolve "horizon.lab.test:${HTTPS_NODEPORT}:192.168.207.139" \
  "https://horizon.lab.test:${HTTPS_NODEPORT}/auth/login/"
```

--resolve ép hostname/port tới IP nhưng vẫn giữ Host/SNI. --cacert tin certificate lab. -D - in response headers, -o /dev/null bỏ body; lệnh vẫn gửi GET. HTTP login200 không kiểm tra token/API panel.

## 4. Vì sao lag không nên kết luận do Gateway?

Horizon gọi nhiều API để dựng trang. Chậm có thể nằm ở xử lý Horizon, API, DB hoặc tài nguyên VM, cũng có thể ở mạng/browser. Log policy scope warning không đủ chứng minh nguyên nhân chậm. Chọn project phù hợp khi thao tác tài nguyên project; không sửa policy chỉ để bỏ warning.

F12 → Network → reload → tìm request chậm và Waiting/TTFB. Ghi request nào chậm, thời gian, response status; đối chiếu log cùng thời điểm. Chưa có Metrics API nên kubectl top sẽ lỗi; không coi lỗi Metrics API là nguyên nhân Horizon hỏng.

## 5. Tài liệu tham khảo ở đâu?

[06 migration RabbitMQ](../reference/06.OpenstackOperatorMigration.md) giải thích cluster/topology/cutover. [18 Infrastructure](../reference/18.Infrastructure.md) là kiến trúc Genestack tổng quan, không chứng minh lab có mọi thành phần như MetalLB/HA. Quy trình thực tế Gateway ở [file 19 local](../reference/19.Gateway.md); bản này đã nằm trong folder học.

## 6. Horizon timeout khi workload đang restart

Output ngày 09/10/2026: Horizon 0/1 Ready, restart18, lần cuối khoảng61s trước; log hiện tại là startup compilemessages/collectstatic/compress và Apache. Nova conductor vừa restart khoảng3 phút trước; nhiều pod MariaDB/Nova/RabbitMQ có lần restart khoảng28 phút trước. Đây là bằng chứng workload không ổn định, chưa xác định OOM/probe/node/containerd hay thao tác quản trị. Các mốc restart giống nhau không tự chứng minh node reboot. Warning distutils/Apache ServerName không đủ để quy nguyên nhân timeout.

Route Horizon không có rules.timeouts trong output không bảo đảm timeout effective nếu có policy khác. Envoy default request timeout15s là tham chiếu [Envoy Gateway1.9](https://gateway.envoyproxy.io/v1.9/tasks/traffic/http-timeouts/). Chưa tăng timeout khi backend đang restart: cần lastState, events và previous log để xác định tại sao container dừng. Không suy ra readiness failed gây restart; liveness/startup failure hoặc các nguyên nhân khác cần evidence.

Dùng tên pod trong snapshot bên dưới; nếu pod đã được thay thì lấy tên mới bằng kubectl -n openstack get pods -l application=horizon trước.

```bash
kubectl -n openstack get pod horizon-74f65df6cb-tjk4f \
  -o jsonpath='{range .status.containerStatuses[*]}{.name}{" ready="}{.ready}{" restarts="}{.restartCount}{" lastState="}{.lastState}{"\n"}{end}'
kubectl -n openstack describe pod horizon-74f65df6cb-tjk4f
kubectl -n openstack logs horizon-74f65df6cb-tjk4f -c horizon --previous --tail=80
```

Các lệnh chỉ đọc. describe cho resources/probes/events, lastState có reason/exitCode/timestamps; previous log là lần container trước. Không kết luận OOM chỉ từ exit137. Nếu previous log chứa credentials phải lọc trước chia sẻ. Sau kết quả mới quyết định sửa resource/probe/API dependency hoặc node issue; không restart để xóa triệu chứng.