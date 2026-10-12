# 07. Giữ gì, xóa gì, và vì sao?

## 1. Không có khái niệm mọi YAML đều phải giữ

Có nguồn cấu hình, output sinh ra, dữ liệu ứng dụng và công cụ. Nhìn extension không đủ: yaml có thể là override chính hoặc render/snapshot. Hãy xác định vai trò trước.

| Thứ | Mục đích | Khi nào có thể bỏ? |
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

## 2. Hai trường hợp khác nhau

**Dựng cụm mới, không giữ dữ liệu:** dùng chart/config, tạo secrets/cert/credentials mới, lấy NB/SB/MON/FSID từ cụm mới. Không cần bản backup dữ liệu cũ.

**Quản trị cụm hiện tại từ bastion mới:** cần kubeconfig/talosconfig hợp lệ. Git public cố ý không có credentials đó; clone repo không tự cấp quyền vào cluster. Nếu chưa có client khác đang giữ quyền truy cập thì phải giải quyết phần truy cập trước khi máy cũ bị thu hồi.

## 3. Dọn đúng nơi

Folder học có assets khoảng 14MB đã chọn từ bastion, không có ISO 336MB hay venv Python 127MB. config là phần nên học và giữ. workspace/artifacts là output sinh trong lúc học, đã gitignore; trước khi dọn xem file nào đang là override duy nhất chưa đưa về config.

Bản Openstack-Lab-Private khoảng 50MB đã được copy ở lượt trước, nằm ngoài folder học và bị gitignore. Nó là lựa chọn riêng cho người muốn giữ originals/credentials, không phải dependency bắt buộc của việc dựng mới. Không có thao tác xóa nó hoặc bastion tự động trong script học.

ASSET-MANIFEST.csv ghi nguồn/đích/hash những asset được copy; dùng đối chiếu bản gốc, không phải installer. Bản copy hash đúng không chứng minh đầy đủ cấu hình runtime hay dữ liệu ứng dụng.

## 4. Trước khi bỏ bản chụp bastion

Xác nhận chart patched/config cuối đã có trong folder này; những thông tin phụ thuộc cluster phải được ghi lại/generate mới. Không còn source-of-truth chỉ nằm trong history/render. Mục tiêu là giữ ít file có mục đích rõ, không giữ mọi file vì sợ.

Hệ thống đang chạy không dùng bản chụp bastion trên Windows để phục vụ dashboard. Xóa bản chụp không tự xóa pod/PVC. Nhưng thu hồi máy bastion thật có thể mất nơi chạy CLI/port-forward/registry nếu chúng đặt ở đó. Gateway NodePort hiện tại không cần port-forward, còn registry local trong bài 04 là ví dụ mới, chưa phải dependency thực tế đã cài.
