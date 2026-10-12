# File nào lấy từ đâu và đọc để hiểu gì?

Các file YAML trong examples được chọn từ bastion, không chứa snapshot effective values/render chứa cluster credentials. Không copy toàn bộ home, không đổi file nguồn. Hostname/IP/storage trong ví dụ là của lab hiện tại; muốn dùng cho môi trường khác phải hiểu và sửa.

| File trong folder học | Nguồn dưới bastion/ | Bạn học gì? |
|---|---|---|
| examples/horizon/https-final.yaml | osh-lab/gateway-api/horizon/https-values.yaml + internal-endpoint-values.yaml | Host/origin/secure cookie/proxy header; endpoint_type đã sửa internalURL |
| examples/horizon/internal-endpoint-values.yaml | osh-lab/gateway-api/horizon/internal-endpoint-values.yaml | Override một key, không copy cả effective values |
| examples/horizon/local-image.yaml | Ví dụ mới, chưa deploy | Đổi hai image keys sang registry local; các image khác chưa đổi |
| examples/gateway/controller-values.yaml | osh-lab/gateway-api/controller-values.yaml | Tắt cài CRD lặp trong controller chart |
| examples/gateway/gateway-https.yaml | osh-lab/gateway-api/manifests/gateway-https.yaml | EnvoyProxy → GatewayClass → Gateway/listeners/TLS Secret ref |
| examples/gateway/horizon-route.yaml | osh-lab/gateway-api/manifests/horizon-route.yaml | Host dashboard → horizon-int:80, attach listener HTTPS |
| examples/gateway/openstack-routes-https.yaml | osh-lab/gateway-api/manifests/openstack-routes-https.yaml | Host của từng API → Service/port; HTTP+HTTPS parents |
| examples/rabbitmq/cluster.yaml | osh-lab/operators/rabbitmq-genestack.yaml | Custom Resource: replicas/image/PVC/resources/placement |
| examples/rabbitmq/service-endpoint.yaml | osh-lab/operators/rabbitmq-cutover/endpoint.yaml | Values chuyển OSH service sang broker Operator, tắt provisioning cũ |
| examples/storage/worker-user-volume.yaml | local-path-provisioner.yaml | Talos UserVolumeConfig chọn sdb, tạo/mount volume 9GB |
| examples/storage/ceph-single-node.yaml | osh-lab/overrides/rook/ceph-single-node.yaml | Helm values giới hạn worker/sdc và Ceph một node |

## Tự đọc một YAML bằng năm câu hỏi

1. Có apiVersion/kind không? Nếu có, đó có thể là Kubernetes CR/manifest hoặc Talos document; đọc tên kind để chọn công cụ.
2. Nếu không, chart/script nào sẽ đọc keys này? Helm values không thể kubectl apply trực tiếp.
3. Ai đọc file? Helm, Kubernetes, Talos hay app trong pod?
4. Chạy apply/upgrade sẽ đổi tài nguyên nào, có đụng disk/data không?
5. Có giá trị phụ thuộc môi trường như IP, node name, UUID, registry, Secret name không?

Ví dụ worker-user-volume.yaml là Talos document, không kubectl apply. ceph-single-node.yaml là Helm values, không Talos patch. gateway-https.yaml là Kubernetes resources, dùng kubectl apply nhưng cần CRD/controller/Secret có trước.

## Nguồn lịch sử và bản đã giữ local

- `../bastion/osh-lab/charts/libvirt`: đã patch Talos; đọc templates/daemonset-libvirt.yaml và templates/bin/_libvirt.sh.tpl. Không thay bằng chart tgz gốc rồi cho rằng tương đương.
- `../bastion/osh-lab/charts/nova`: đọc templates/daemonset-compute.yaml cùng values/mounts; socket /run/libvirt và /run/openvswitch.
- `../bastion/osh-lab/charts/neutron`: chart và cấu hình shared OVN; NB/SB ClusterIP phải lấy từ cluster đang dùng.
- `../bastion/.cache/helm/repository`: tgz chart tải sẵn; đây không phải image archive/container cache.
- `../bastion/osh-lab/operators/rabbitmq-cutover/*-current.yaml` và finish-*/: snapshots theo thời điểm migration, không gọi là source-of-truth mới nhất và không commit raw.
- `../bastion/osh-lab/gateway-api/tls/tls.key`: private key, không đưa vào folder học/Git.
- `.kube/.talos/.ssh/controlplane.yaml/worker.yaml/talosconfig`: credentials/machine config có secrets, không copy vào examples.

## Lưu ý storage khi học dựng mới

Worker sdb hiện khoảng 10GB, user volume 9GB; Glance overrides cũ yêu cầu images 10Gi và staging 2Gi. Không dùng lại kích thước này để hứa cài mới trên disk 9GB sẽ đủ. Local-path thường không enforce quota theo request PVC nên PVC Bound không chứng minh còn đủ dung lượng ghi. Cụm cũ có PVC đã tồn tại cần xử lý khác cụm mới; không shrink PVC bằng Helm để thử.

Cinder dùng Ceph key/FSID/MON do cluster sinh, không lấy key/IP cũ từ snapshot sang lab khác. Ceph single-node replica1 và control plane một node là thiết kế học/test, không có HA như mô hình production Genestack.

## Bản sao tham khảo

- reference/06.OpenstackOperatorMigration.md: file 06 về Operator migration, không phải 06.KubeOVN.md. Có command lịch sử, chỉ đọc đúng phần cần học.
- reference/18.Infrastructure.md: file 18 kiến trúc, đã copy ảnh Screenshot_17.png nếu có trong nguồn.

Các đường bastion ở trên chỉ ghi nguồn lịch sử. Chart/config cần dùng đã giữ ở assets/config; tài liệu 05/06/07/18/19 ở reference; nguồn Octavia/Genestack được trích ở reference/genestack. Không cần folder bastion hoặc bản 05/19 bên ngoài để đọc và sử dụng các file đã giữ. Các source trích không tự trở thành framework Genestack đầy đủ để chạy installer nguyên xi.


Nguồn Genestack Octavia đã đối chiếu: xem reference/GENESTACK-SOURCE-MANIFEST.csv (SHA256 các file trích); xem bài 08 để biết khác biệt MariaDB/broker/provider/post-rendering của lab.

## Quy ước bản cuối

Các hướng dẫn lab trong docs/ và reference/05,06,19 được biên tập theo cấu hình cuối: bước sửa bị thay thế không còn là một thao tác cài mới. Lý do chọn key/endpoint nằm cạnh bước cấu hình, kết quả cụm cũ ghi riêng. reference/genestack và README/CHANGELOG trong assets là nguồn upstream để đối chiếu, giữ nguyên để không làm lệch SHA/source; không chạy như installer lab.
