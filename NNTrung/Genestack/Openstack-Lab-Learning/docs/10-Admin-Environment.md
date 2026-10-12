# 10. Một file nạp OpenStack CLI và Octavia

Sau khi cấu hình một lần, mỗi terminal mới chỉ chạy:

```bash
source ~/osh-lab/bin/admin.sh
openstack token issue -f value -c expires
openstack port list
openstack loadbalancer provider list
openstack loadbalancer list
```

source giữ biến trong shell hiện tại. admin.sh tự activate ~/openstack-client, đọc nova-keystone-admin qua kubectl, lấy HTTPS NodePort của openstack-gateway, nạp credentials và endpoint Identity/Nova/Neutron/Glance/Cinder. Octavia dùng public catalog được Jobs đăng ký. Script kiểm tra plugin octaviaclient nhưng không tự pip install hoặc deploy. Không cần gọi hàm riêng, không cần port-forward. Nạp môi trường không có nghĩa mọi API/backend đã nghiệm thu.

## Chuẩn bị một lần

Trên bastion:

```bash
mkdir -p ~/osh-lab/bin
```

Nếu đã copy folder học lên bastion:

```bash
cp ~/Openstack-Lab-Learning/tools/admin.sh ~/osh-lab/bin/admin.sh
chmod 600 ~/osh-lab/bin/admin.sh
```

Nếu file ở máy Windows, chạy lệnh này trong PowerShell Windows (đổi path/IP nếu khác):

```powershell
scp "D:\system-intership\NNTrung\Genestack\Openstack-Lab-Learning\tools\admin.sh" bastion@192.168.207.138:~/osh-lab/bin/admin.sh
```

Các hostname cần DNS/hosts trỏ node reachable. Cấu hình một lần trên bastion; nếu dòng đã có nhưng IP sai, sửa dòng đó thay vì thêm trùng. Đây là bước sudo riêng, admin.sh không tự sửa hosts:

```bash
for HOST in keystone nova neutron glance cinder octavia; do
  grep -q "${HOST}.lab.test" /etc/hosts ||
    echo "192.168.207.139 ${HOST}.lab.test" | sudo tee -a /etc/hosts
done
```

Nếu plugin thiếu, source venv rồi cài một lần khi có Internet:

```bash
source ~/openstack-client/bin/activate
python -m pip install python-octaviaclient
```

Chạy source admin.sh sau khi chuẩn bị. Không chạy bash admin.sh vì biến chỉ nằm trong tiến trình con. Không cần chuyển private password vào script: credentials đọc từ Kubernetes Secret theo context hiện tại.

## Cấu hình cho cụm mới

Defaults: namespace openstack, Secret nova-keystone-admin, domain lab.test, region RegionOne, venv ~/openstack-client, Gateway Service openstack-gateway tại envoyproxy-gateway-system. IP hosts cần đổi theo node mới; HTTPS NodePort tự lấy lại. Script phải có kubeconfig truy cập đúng cụm. Nếu topology/domain/route khác thì chỉnh script hoặc đặt biến trước source:

```bash
export OSH_DOMAIN=lab.test
export OSH_REGION=RegionOne
source ~/osh-lab/bin/admin.sh
```

Certificate lab tự ký dùng OS_INSECURE=true nên không cần gõ --insecure từng lệnh. Muốn kiểm tra TLS đúng CA:

```bash
export OSH_CACERT="$HOME/osh-lab/gateway-api/tls/tls.crt"
source ~/osh-lab/bin/admin.sh
```

CA này phải thật sự xác minh certificate Gateway. Script không in password hoặc ghi credentials ra file. Nó xóa một số auth selectors cũ như OS_CLOUD/OS_TOKEN để tránh lấy nhầm auth; không tự sửa public catalog. Placement/Barbican hoặc API chưa có route không được hứa sẽ hoạt động chỉ vì source.

## Lý do chọn một helper duy nhất

load-admin.sh cũ là helper credentials cho giai đoạn chưa có Gateway, mặc định URL localhost. Sau Gateway dùng admin.sh làm điểm vào duy nhất. Không source helper cũ tiếp sau admin.sh vì có thể ghi đè URL. Các phần hướng dẫn port-forward vẫn dùng khi Gateway chưa cài, không phải luồng quản trị hằng ngày.

Đóng terminal mất biến OS_*; mở terminal mới source một lần. Script không khởi động dịch vụ, không gọi kiểm thử API tự động và không thay cấu hình cluster.
