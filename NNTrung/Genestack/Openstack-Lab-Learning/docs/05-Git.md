# 05. Từ folder loạn tới repo mình hiểu được

## 1. Git giữ cấu hình, không giữ cụm đang chạy

Commit là mốc của file. Helm revision là mốc một release trong Kubernetes. Hai mốc không tự đồng bộ. Git không backup database, PVC, Ceph hoặc VM disk. Registry chứa image; Git thường giữ tên/tag/digest image và source build, không giữ hàng GB archive.

Genestack có giá trị ở cách tổ chức: version pin, cấu hình base, override môi trường, installer và tài liệu. Bạn không cần chép cả Genestack để học ý tưởng này.

## 2. Một cấu trúc mình có thể tiến tới

```text
my-openstack-lab/
  README.md                  # Đọc đầu tiên: mục tiêu, thứ tự, điều kiện
  versions.yaml              # Chart/app/image versions và digest đã xác nhận
  environments/lab.yaml      # IP/node/domain/disk theo môi trường
  charts/                    # Chart local có patch; giữ LICENSE/dependencies
  overrides/                 # Cấu hình chính theo service
  manifests/                 # Operator CR, Gateway, pool/client Ceph
  scripts/                   # Lệnh áp dụng có giải thích/kiểm tra đầu vào
  docs/                      # Cách dựng, cập nhật, đọc lỗi
  artifacts/                 # Render/snapshot/export, không commit
  private/                   # Secrets địa phương, không commit
```

Đây là thiết kế để học, không phải tất cả đã được tự động hóa trong folder hiện tại. environments/lab.yaml không tự thay IP trong mọi file: cần template/generator đọc nó và render đúng. Đặt biến vào YAML rồi quên viết cơ chế thay thế vẫn là cấu hình sai.

## 3. Chọn cấu hình cuối từ bastion

Thực hiện từng dịch vụ, không gom đồng thời tất cả:

1. Đọc helm list/history và chụp get values --all ở cluster hiện tại.
2. Đối chiếu các file overrides và chart local.
3. Chọn những override còn hiệu lực; ghi thứ tự file trong README/script.
4. Loại bản preview/before/render khỏi nguồn chính, nhưng giữ snapshot riêng nếu cần lịch sử.
5. Render bằng bộ được chọn; đối chiếu hostname, mounts, images, jobs, storage.
6. Đặt secrets vào file private riêng; xác nhận render không còn credentials cũ trong public file.
7. Kiểm tra trên môi trường thử trước khi coi là quy trình dựng mới.

Ví dụ cuối Horizon: distro → HTTPS config có internalURL. Bản example https-final.yaml đã hợp nhất hai override dễ đọc, nhưng chưa tự chứa toàn bộ DB/auth/placement của release. Nova/Libvirt cần giữ patch template; Neutron cần lấy NB/SB IP mới từ Service, không mang ClusterIP cũ sang cluster mới. Cinder cần key/FSID/MON mới do Ceph sinh.

## 4. Học Git trên folder tài liệu này

Sau khi copy folder sang bastion và kiểm tra không có credential nhạy cảm:

```bash
cd ~/Openstack-Lab-Learning
git init
git status --short
git add README.md SOURCE-MAP.md .gitignore docs examples tools reference
git diff --cached --stat
```

git init tạo repository local, không upload. git add chọn file vào staging. Xem nội dung staged riêng trước commit; .gitignore không xóa bí mật đã tracked. File reference có thể chứa hướng dẫn cũ/credential mẫu nên đọc lại trước khi đưa repo public.

Khi đã tự đọc diff:

```bash
git commit -m 'Add notes and examples for learning the OpenStack lab'
```

Git có thể yêu cầu user.name/user.email; cấu hình danh tính của bạn trong repo. Chưa cần GitHub hoặc Internet để commit local. Muốn đồng bộ server mới thêm remote/push; không đưa cluster credentials lên server để tiện copy.

## 5. Quy tắc sửa từ lần sau

Mỗi thay đổi ghi: vấn đề → file/key sửa → lệnh render/apply → kết quả → hạn chế. Giữ script đọc rõ thay vì một installer dài che toàn bộ logic. Render tốt chưa đủ để commit nhãn “tested deployment”: cần có bằng chứng runtime/tác vụ tương ứng.

Nếu muốn sửa code thật của Horizon: lấy đúng source version, lưu patch/Containerfile, build image tag mới, push registry, đổi images.tags và upgrade. helm upgrade không biên dịch Python và không tạo image từ source cho bạn.
