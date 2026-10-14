# Nguồn cấu hình và chức năng của các tệp

Các tệp YAML trong examples được trích từ cấu hình bastion và các ví dụ bổ sung. Bộ ví dụ không chứa toàn bộ thư mục home hoặc các snapshot chứa thông tin xác thực của cụm. Hostname, địa chỉ IP và tham số storage được điều chỉnh theo môi trường đích trước khi áp dụng.

| Tệp trong repository | Nguồn dưới bastion/ | Nội dung cấu hình |
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

## 1. Phân loại tài liệu YAML

1. Các trường apiVersion và kind xác định loại tài nguyên Kubernetes hoặc tài liệu cấu hình Talos; loại tài nguyên quyết định công cụ áp dụng.
2. Tệp không có các trường trên có thể là Helm values hoặc đầu vào của script. Các khóa chỉ có tác dụng khi chart/script sử dụng chúng; Helm values không được áp dụng trực tiếp bằng kubectl.
3. Thành phần sử dụng tệp có thể là Helm, Kubernetes, Talos hoặc ứng dụng trong pod.
4. Phạm vi thay đổi được xác định từ tài nguyên được tạo/cập nhật và tác động đến disk hoặc dữ liệu.
5. Các tham số phụ thuộc môi trường gồm địa chỉ IP, tên node, UUID, registry và tên Secret.

Ví dụ worker-user-volume.yaml là Talos document, không kubectl apply. ceph-single-node.yaml là Helm values, không Talos patch. gateway-https.yaml là Kubernetes resources, dùng kubectl apply nhưng cần CRD/controller/Secret có trước.

## 2. Nguồn lịch sử và bản sao trong repository

- `../bastion/osh-lab/charts/libvirt`: đã patch Talos; đọc templates/daemonset-libvirt.yaml và templates/bin/_libvirt.sh.tpl. Không thay bằng chart tgz gốc rồi cho rằng tương đương.
- `../bastion/osh-lab/charts/nova`: đọc templates/daemonset-compute.yaml cùng values/mounts; socket /run/libvirt và /run/openvswitch.
- `../bastion/osh-lab/charts/neutron`: chart và cấu hình shared OVN; NB/SB ClusterIP phải lấy từ cluster đang dùng.
- `../bastion/.cache/helm/repository`: tgz chart tải sẵn; đây không phải image archive/container cache.
- `../bastion/osh-lab/operators/rabbitmq-cutover/*-current.yaml` và finish-*/: snapshots theo thời điểm migration, không gọi là source-of-truth mới nhất và không commit raw.
- `../bastion/osh-lab/gateway-api/tls/tls.key`: private key, không đưa vào folder học/Git.
- `.kube/.talos/.ssh/controlplane.yaml/worker.yaml/talosconfig`: credentials/machine config có secrets, không copy vào examples.

## 3. Dung lượng và tính phụ thuộc môi trường của storage

Worker sdb hiện khoảng 10GB, user volume 9GB; Glance overrides cũ yêu cầu images 10Gi và staging 2Gi. Dung lượng yêu cầu 10Gi và 2Gi vượt khả năng lưu trữ của volume 9 GB nếu các PVC được ghi đầy. Local-path thường không enforce quota theo request PVC nên PVC Bound không chứng minh còn đủ dung lượng ghi. Cụm cũ có PVC đã tồn tại cần xử lý khác cụm mới; không shrink PVC bằng Helm để thử.

Cinder dùng Ceph key/FSID/MON do cluster sinh, không lấy key/IP cũ từ snapshot sang lab khác. Ceph single-node replica1 và control plane một node là thiết kế học/test, không có HA như mô hình production Genestack.

## 4. Tài liệu tham chiếu

- reference/06.OpenstackOperatorMigration.md: file 06 về Operator migration, không phải 06.KubeOVN.md. Có command lịch sử, chỉ đọc đúng phần cần học.
- reference/18.Infrastructure.md: file 18 kiến trúc, đã copy ảnh Screenshot_17.png nếu có trong nguồn.

Các đường bastion ở trên chỉ ghi nguồn lịch sử. Chart/config cần dùng đã giữ ở assets/config; tài liệu 05/06/07/18/19 ở reference; nguồn Octavia/Genestack được trích ở reference/genestack. Không cần folder bastion hoặc bản 05/19 bên ngoài để đọc và sử dụng các file đã giữ. Các source trích không tự trở thành framework Genestack đầy đủ để chạy installer nguyên xi.


Nguồn Genestack Octavia đã đối chiếu: xem reference/GENESTACK-SOURCE-MANIFEST.csv (SHA256 các file trích); xem bài 08 để biết khác biệt MariaDB/broker/provider/post-rendering của lab.

## 5. Cấu hình triển khai và dữ liệu lịch sử

Các hướng dẫn lab trong docs/ và reference/05,06,19 được biên tập theo cấu hình cuối: bước sửa bị thay thế không còn là một thao tác cài mới. Lý do chọn key/endpoint nằm cạnh bước cấu hình, kết quả cụm cũ ghi riêng. reference/genestack và README/CHANGELOG trong assets là nguồn upstream để đối chiếu, giữ nguyên để không làm lệch SHA/source; không chạy như installer lab.
