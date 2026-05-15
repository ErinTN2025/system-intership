# OpenStack Kolla-Ansible Command Cheatsheet

## 1. Kích hoạt môi trường Kolla

```bash
source ~/kolla-venv/bin/activate
```

Kiểm tra:

```bash
which openstack
which kolla-ansible
```

---

# 2. Kiểm tra node và service

## Kiểm tra container Docker

```bash
docker ps
```

Xem tất cả container:

```bash
docker ps -a
```

---

## Xem log container

```bash
docker logs <container>
```

Realtime:

```bash
docker logs -f <container>
```

Ví dụ:

```bash
docker logs -f neutron_server
```

---

## Kiểm tra network namespace

```bash
ip netns
```

Thường sẽ thấy:

```text
qrouter-xxxx
qdhcp-xxxx
```

---

## Xem IP/interface trong namespace

```bash
sudo ip netns exec qrouter-xxxx ip a
```

---

## Ping từ router namespace

> ⚠️ Với setup dummy eth1, KHÔNG ping được floating IP thẳng từ host.
> Phải vào namespace của Neutron router:

```bash
# Lấy tên namespace tự động
NS=$(sudo ip netns list | grep qrouter | awk '{print $1}')

# Ping từ trong namespace
sudo ip netns exec $NS ping 10.0.2.185
```

---

# 3. Quản lý OpenStack Service

## Xem service

```bash
openstack service list
```

---

## Xem endpoint

```bash
openstack endpoint list
```

---

## Xem network agent

```bash
openstack network agent list
```

Quan trọng:

* DHCP Agent
* L3 Agent
* Open vSwitch Agent

Tất cả nên là:

```text
:-)
```

---

## Xem hypervisor

```bash
openstack hypervisor list
```

Xem chi tiết từng node:

```bash
openstack hypervisor show compute01
openstack hypervisor show compute02
```

---

## Xem compute service

```bash
openstack compute service list
```

Kết quả mong muốn:

```text
nova-conductor    → up/enabled (control01)
nova-scheduler    → up/enabled (control01)
nova-compute      → up/enabled (compute01)
nova-compute      → up/enabled (compute02)
```

---

## Verify VM đang chạy trên từng compute node

```bash
# SSH vào compute node, check qua virsh
ssh kolla@compute01 'sudo docker exec nova_compute virsh list'
ssh kolla@compute02 'sudo docker exec nova_compute virsh list'
```

Output mẫu:

```text
 Id   Name                State
 1    instance-00000001   running
```

---

# 4. Quản lý Image

## List image

```bash
openstack image list
```

---

## Upload image

```bash
openstack image create "Ubuntu-22.04" \
  --file ubuntu.img \
  --disk-format qcow2 \
  --container-format bare \
  --public
```

---

## Xem image

```bash
openstack image show cirros
```

---

# 5. Flavor

## List flavor

```bash
openstack flavor list
```

---

## Tạo flavor

```bash
openstack flavor create \
  --ram 512 \
  --disk 1 \
  --vcpus 1 \
  m1.tiny
```

---

# 6. Network

## List network

```bash
openstack network list
```

---

## Tạo network

```bash
openstack network create demo-net
```

---

## Tạo subnet

```bash
openstack subnet create demo-subnet \
  --network demo-net \
  --subnet-range 10.0.0.0/24 \
  --gateway 10.0.0.1 \
  --dns-nameserver 8.8.8.8
```

---

## Xem network chi tiết

```bash
openstack network show demo-net
```

---

## Xem subnet

```bash
openstack subnet list
```

---

# 7. Router

## Tạo router

```bash
openstack router create demo-router
```

---

## Gắn subnet vào router

```bash
openstack router add subnet demo-router demo-subnet
```

---

## Set external gateway

```bash
openstack router set demo-router \
  --external-gateway public1
```

---

## Xem router

```bash
openstack router show demo-router
```

Quan trọng:

* external_gateway_info
* interfaces_info

---

# 8. Provider / External Network

## List network

```bash
openstack network list
```

---

## Xem external network

```bash
openstack network show public1
```

---

## Xem subnet external

```bash
openstack subnet show public1-subnet
```

---

# 9. Security Group

## List security group

```bash
openstack security group list
```

---

## Xem rule

```bash
openstack security group rule list <security-group-id>
```

---

## Mở SSH

```bash
openstack security group rule create \
  --proto tcp \
  --dst-port 22 \
  default
```

---

## Mở ICMP (ping)

```bash
openstack security group rule create \
  --proto icmp \
  default
```

---

## Mở port web

```bash
openstack security group rule create \
  --proto tcp \
  --dst-port 80 \
  default
```

---

# 10. Keypair

## List keypair

```bash
openstack keypair list
```

---

## Tạo keypair

```bash
ssh-keygen
```

---

## Upload public key

```bash
openstack keypair create \
  --public-key ~/.ssh/id_rsa.pub \
  mykey
```

---

## Xem keypair

```bash
openstack keypair show mykey
```

---

# 11. VM / Instance

## List VM

```bash
openstack server list
```

---

## List VM chi tiết

```bash
openstack server list --long
```

---

## Tạo VM

```bash
openstack server create \
  --image cirros \
  --flavor m1.tiny \
  --network demo-net \
  --key-name mykey \
  --security-group default \
  test-vm
```

---

## Chỉ định compute node

```bash
openstack server create \
  --image cirros \
  --flavor m1.tiny \
  --network demo-net \
  --availability-zone nova:compute01 \
  vm-on-compute01
```

---

## Xem VM chi tiết

```bash
openstack server show test-vm
```

Xem VM đang chạy trên node nào:

```bash
openstack server show test-vm -f value -c "OS-EXT-SRV-ATTR:host"
```

Quan trọng:

* status
* addresses
* host
* key_name
* security_groups

---

## Xem console log (debug khi không SSH được)

```bash
openstack console log show test-vm
```

---

## Xem VNC console trên browser

```bash
openstack console url show --novnc test-vm
# Mở URL trả về trên browser để vào console VM
```

---

## Reboot VM

```bash
openstack server reboot test-vm
```

---

## Hard reboot

```bash
openstack server reboot --hard test-vm
```

---

## Delete VM

```bash
openstack server delete test-vm
```

---

# 12. Floating IP

## List floating IP

```bash
openstack floating ip list
```

---

## Tạo floating IP

```bash
openstack floating ip create public1
```

---

## Attach floating IP

```bash
openstack server add floating ip test-vm 10.0.2.185
```

---

## Remove floating IP

```bash
openstack server remove floating ip test-vm 10.0.2.185
```

---

## Delete floating IP

```bash
openstack floating ip delete 10.0.2.185
```

---

# 13. Port

## List port

```bash
openstack port list
```

---

## Port theo VM

```bash
openstack port list --server test-vm
```

---

## Xem port

```bash
openstack port show <port-id>
```

Quan trọng:

* fixed_ips
* security_group_ids
* binding_host_id

---

# 14. SSH vào VM

> ⚠️ Với setup dummy eth1, KHÔNG thể SSH thẳng từ host vào floating IP.
> Phải đi qua namespace của Neutron router.

## Lấy namespace router

```bash
NS=$(sudo ip netns list | grep qrouter | awk '{print $1}')
echo $NS
```

---

## SSH bằng keypair

```bash
sudo ip netns exec $NS ssh -i ~/.ssh/id_rsa cirros@10.0.2.185
```

---

## SSH bằng password

```bash
sudo ip netns exec $NS ssh cirros@10.0.2.185
# Password mặc định Cirros: gocubsgo
```

---

## SSH verbose (debug)

```bash
sudo ip netns exec $NS ssh -vvv -i ~/.ssh/id_rsa cirros@10.0.2.185
```

---

## Test port 22 có mở không

```bash
sudo ip netns exec $NS nc -zv 10.0.2.185 22
```

---

# 15. Debug Network

> ⚠️ Với setup dummy eth1, các lệnh ping/nc/telnet phải chạy từ trong namespace.

## Lấy namespace

```bash
NS=$(sudo ip netns list | grep qrouter | awk '{print $1}')
```

---

## Ping floating IP

```bash
sudo ip netns exec $NS ping 10.0.2.185
```

---

## Ping gateway external network

```bash
sudo ip netns exec $NS ping 10.0.2.1
```

---

## Xem interface trong namespace

```bash
sudo ip netns exec $NS ip a
```

---

## Xem route trong namespace

```bash
sudo ip netns exec $NS ip route
```

---

## Xem route host

```bash
ip route
```

---

## Xem interface host

```bash
ip a
```

---

## Xem bridge OVS

```bash
sudo ovs-vsctl show
```

---

## Xem Open vSwitch port

```bash
sudo ovs-vsctl list-ports br-int
```

---

## Xem flow OVS

```bash
sudo ovs-ofctl dump-flows br-int
```

---

# 16. Migration (Multinode)

## Xem VM đang ở node nào

```bash
openstack server show <vm> -f value -c "OS-EXT-SRV-ATTR:host"
```

---

## Watch trạng thái migration

```bash
watch openstack server show <vm> \
  -f value \
  -c status \
  -c "OS-EXT-SRV-ATTR:host" \
  -c "OS-EXT-STS:task_state"
```

---

## Cold Migration (VM tắt rồi chuyển node)

```bash
# Trigger migration, scheduler tự chọn node
openstack server migrate <vm>

# Sau khi trạng thái VERIFY_RESIZE, confirm
openstack server resize confirm <vm>

# Hoặc rollback
openstack server resize revert <vm>
```

Các state sẽ đi qua:

```text
ACTIVE → SHUTOFF (MIGRATING) → VERIFY_RESIZE → ACTIVE
```

---

## Live Migration (VM vẫn chạy trong khi chuyển)

```bash
# Chỉ định node đích
openstack server migrate \
  --live-migration \
  --host compute02 \
  <vm>
```

Các state sẽ đi qua:

```text
ACTIVE (task: migrating) → ACTIVE (host: compute02)
```

> Mở 2 terminal: 1 terminal ping VM liên tục, 1 terminal trigger migration
> để quan sát downtime thực tế.

---

## Evacuate (kịch bản node chết)

```bash
# Simulate node chết
openstack compute service set --disable compute01 nova-compute

# Evacuate VM sang node khác
openstack server evacuate <vm> --host compute02

# Bật lại node sau khi xong
openstack compute service set --enable compute01 nova-compute
```

---

## So sánh các loại migration

| | Cold Migration | Live Migration | Evacuate |
|---|---|---|---|
| VM state | Tắt rồi chuyển | Chạy xuyên suốt | Node cũ đã chết |
| Downtime | Có | Gần như không | Có |
| Confirm | Cần resize confirm | Tự động | Tự động |
| Dùng khi | Maintenance | Production | Disaster recovery |

---

# 17. Server Group / Anti-affinity

## Tạo server group

```bash
openstack server group create --policy anti-affinity sg-spread
```

---

## List server group

```bash
openstack server group list
```

---

## Tạo VM trong server group

```bash
openstack server create \
  --image cirros --flavor m1.tiny \
  --network demo-net \
  --hint group=$(openstack server group show sg-spread -f value -c id) \
  vm-spread-1

openstack server create \
  --image cirros --flavor m1.tiny \
  --network demo-net \
  --hint group=$(openstack server group show sg-spread -f value -c id) \
  vm-spread-2
```

Verify 2 VM nằm trên 2 node khác nhau:

```bash
openstack server list --long | grep vm-spread
```

---

# 18. Docker Debug

## Restart container

```bash
docker restart <container>
```

---

## Stop container

```bash
docker stop <container>
```

---

## Start container

```bash
docker start <container>
```

---

## Xem resource container

```bash
docker stats
```

---

# 19. Kolla-Ansible

## Deploy

```bash
kolla-ansible deploy -i multinode
```

---

## Reconfigure

```bash
kolla-ansible reconfigure -i multinode
```

## Reconfigure 1 service cụ thể

```bash
kolla-ansible reconfigure -i multinode -t nova
```

---

## Upgrade

```bash
kolla-ansible upgrade -i multinode
```

---

## Destroy

```bash
kolla-ansible destroy -i multinode --yes-i-really-really-mean-it
```

---

## Pull image

```bash
kolla-ansible pull -i multinode
```

---

## Bootstrap server

```bash
kolla-ansible bootstrap-servers -i multinode
```

---

## Precheck

```bash
kolla-ansible prechecks -i multinode
```

---

## Backup MariaDB

```bash
kolla-ansible mariadb_backup -i multinode
```

---

## Stop toàn cụm

```bash
kolla-ansible stop -i multinode --yes-i-really-really-mean-it
```

---

# 20. Ansible

## Ping node

```bash
ansible all -i multinode -m ping
```

---

## Chạy command

```bash
ansible all -i multinode -a "hostname"
```

---

## Kiểm tra clock skew (quan trọng cho MariaDB cluster)

```bash
ansible -i multinode all -m shell -a "chronyc tracking | grep offset"
```

Offset phải < 100ms.

---

## Kiểm tra inventory

```bash
cat multinode
```

---

# 21. Service Database / MQ

## MariaDB

```bash
docker exec -it mariadb bash
```

---

## RabbitMQ

```bash
docker exec -it rabbitmq bash
```

---

## Redis

```bash
docker exec -it redis redis-cli
```

---

# 22. Horizon

## Truy cập dashboard

```text
http://<controller-ip>
```

Lấy password admin:

```bash
grep keystone_admin_password /etc/kolla/passwords.yml
```

Login:

* Username: `admin`
* Domain: `default`

---

# 23. Lỗi thường gặp

## Floating IP không ping được

Check:

* router external gateway
* security group (ICMP mở chưa)
* L3 agent alive chưa
* Dùng namespace: `sudo ip netns exec $NS ping <FIP>`

---

## SSH treo hoặc không được

Check:

* security group port 22 mở chưa
* Phải SSH từ trong namespace: `sudo ip netns exec $NS ssh cirros@<FIP>`
* VM boot xong chưa: `openstack console log show <vm>`
* keypair đúng chưa

---

## VM stuck BUILD

```bash
docker logs nova_compute
openstack compute service list
openstack console log show <vm>
```

---

## Không schedule được VM

```bash
openstack hypervisor list
docker logs nova_scheduler
```

---

## Compute node không register vào cụm

```bash
ssh compute01 'sudo docker logs nova_compute | tail -50'

# Check nested KVM
ssh compute01 'cat /sys/module/kvm_intel/parameters/nested'
```

Nếu không có `Y`, thêm vào `globals.yml`:

```yaml
nova_compute_virt_type: "qemu"
```

Rồi:

```bash
kolla-ansible reconfigure -i multinode -t nova
```

---

## MariaDB restart liên tục

```bash
# Check clock skew
ansible -i multinode all -m shell -a "chronyc tracking | grep offset"
# Offset > 100ms → sync lại chrony trước khi deploy
```

---

## VM tạo được nhưng không có IP

```bash
openstack network agent list | grep DHCP
docker logs neutron_dhcp_agent
```

---

# 24. Cleanup nhanh

## Xóa VM

```bash
openstack server delete test-vm
```

---

## Xóa floating IP

```bash
openstack floating ip delete <ip>
```

---

## Xóa router interface

```bash
openstack router remove subnet demo-router demo-subnet
```

---

## Xóa router

```bash
openstack router delete demo-router
```

---

## Xóa subnet

```bash
openstack subnet delete demo-subnet
```

---

## Xóa network

```bash
openstack network delete demo-net
```

---

## Reset toàn bộ (khi lỗi không fix được)

```bash
# Xóa container
sudo docker stop $(sudo docker ps -aq)
sudo docker rm $(sudo docker ps -aq)

# Kiểm tra port sạch chưa
sudo ss -tlnp | grep -E "3306|5672|15672"

# Deploy lại
kolla-ansible deploy -i ~/multinode
```
