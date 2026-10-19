# 07. Chính sách lưu trữ cấu hình và dữ liệu

## 1. Phân loại tệp theo chức năng

Dữ liệu được phân loại thành nguồn cấu hình, đầu ra được sinh, dữ liệu ứng dụng và công cụ thực thi. Phần mở rộng không xác định đầy đủ chức năng của tệp: YAML có thể là override, manifests hoặc snapshot. Chính sách lưu trữ được lựa chọn theo chức năng và khả năng tái tạo.

| Loại tài nguyên | Chức năng | Điều kiện loại bỏ |
|---|---|---|
| Chart Libvirt/Nova/Neutron/Cinder local | Có template/patch riêng, Helm cần để dựng lại | Chỉ khi đã lưu chính xác nơi khác; không coi tgz upstream thay được patch |
| Overrides chính + manifests cuối | Quyết định cách chạy lab | Giữ trong Git sau khi tách secret |
| Chart tgz | Nguồn pin sẵn để unpack/install | Khi giữ cùng chart đủ dependencies và chấp nhận tải lại; offline thì giữ |
| before/current snapshots | Trạng thái tại thời điểm sửa | Sau khi đã xác nhận cấu hình chính đầy đủ và không cần rollback đó |
| rendered.yaml | Xem trước chart, có thể chứa Secret | Sau kiểm tra nếu source chart/values còn; render lại được |
| Preview VXLAN/API-only cũ | Nhánh thử bỏ | Sau xác nhận không còn dùng; không trộn vào cấu hình cuối |
| ISO Talos | Boot/cài VM | Sau cài nếu không cần cài mới offline và có nơi tải/lưu lại |
| Binary tool | Chạy talosctl/kubectl/Helm | Nếu có bản cài hoạt động hoặc cách cài lại; máy offline cần giữ bộ cài |
| Python virtualenv | Thư viện CLI tại máy cũ | Có requirements/wheels/cách tạo lại; không coi venv Linux cũ portable sang mọi máy |
| Image archive/registry data | Container images offline | Khi có nguồn đáng tin để tải/nạp lại; chart không thay thế image |
| DB/PVC/Ceph/VM disk | Dữ liệu ứng dụng | Khi chủ động bỏ dữ liệu, không nhầm với cache/file render |
| kubeconfig/talosconfig/SSH/TLS key | Quyền truy cập vào cụm đang có | Với cụm bỏ hẳn có thể bỏ; cụm còn dùng cần cách truy cập thay thế |

## 2. Dựng cụm mới và quản trị cụm hiện tại

**Dựng cụm mới, không giữ dữ liệu:** dùng chart/config, tạo secrets/cert/credentials mới, lấy NB/SB/MON/FSID từ cụm mới. Không cần bản backup dữ liệu cũ.

**Quản trị cụm hiện tại từ bastion mới:** cần kubeconfig/talosconfig hợp lệ. Git public cố ý không có credentials đó; clone repo không tự cấp quyền vào cluster. Nếu chưa có client khác đang giữ quyền truy cập thì phải giải quyết phần truy cập trước khi máy cũ bị thu hồi.

## 3. Phạm vi dữ liệu trong repository

Folder học có assets khoảng 14MB đã chọn từ bastion, không có ISO 336MB hay venv Python 127MB. config là phần nên học và giữ. workspace/artifacts là output sinh trong lúc học, đã gitignore; trước khi dọn xem file nào đang là override duy nhất chưa đưa về config.

Bản Openstack-Lab-Private khoảng 50MB đã được copy ở lượt trước, nằm ngoài folder học và bị gitignore. Nó là lựa chọn riêng cho người muốn giữ originals/credentials, không phải dependency bắt buộc của việc dựng mới. Các script chuẩn bị không tự xóa bản lưu riêng tư hoặc dữ liệu bastion.

ASSET-MANIFEST.csv ghi nguồn/đích/hash những asset được copy; dùng đối chiếu bản gốc, không phải installer. Bản copy hash đúng không chứng minh đầy đủ cấu hình runtime hay dữ liệu ứng dụng.

## 4. Điều kiện loại bỏ bản chụp bastion

Xác nhận chart patched/config cuối đã có trong folder này; những thông tin phụ thuộc cluster phải được ghi lại/generate mới. Không còn source-of-truth chỉ nằm trong history/render. Bộ lưu trữ duy trì các nguồn cấu hình cần thiết và các dữ liệu có yêu cầu phục hồi rõ ràng.

Hệ thống đang chạy không dùng bản chụp bastion trên Windows để phục vụ dashboard. Xóa bản chụp không tự xóa pod/PVC. Nhưng thu hồi máy bastion thật có thể mất nơi chạy CLI/port-forward/registry nếu chúng đặt ở đó. Gateway NodePort hiện tại không cần port-forward, còn registry local trong bài 04 là ví dụ mới, chưa phải dependency thực tế đã cài.
