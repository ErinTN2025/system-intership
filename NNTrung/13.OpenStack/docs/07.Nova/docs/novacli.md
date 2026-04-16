# Các lệnh thường dùng trong Nova
## 1. Cài và Chuẩn bị OpenStack Cli (Check lại thường đã tải cùng với OPS)
```bash
# Cài trên máy local hoặc utility container
pip install python-openstackclient python-novaclient  # novaclient chỉ khi cần

# Source file credentials (thường do admin cung cấp)
source admin-openrc.sh     # hoặc user-openrc.sh
# Kiểm tra
openstack --version
openstack server list
```
## 2. OpenStack Cli
### 2.1 Quản lý Instance (Server) - Nhóm lệnh quan trọng
```bash
# Liệt kê
openstack server list [--all-projects] [--long] [--name <tên>] [--status ACTIVE|SHUTOFF|ERROR]
openstack server show <tên-hoặc-uuid> [--fit-width]

# Tạo instance (cú pháp đầy đủ nhất)
openstack server create <tên-vm> \
  --image <image-id-hoặc-tên> \
  --flavor <flavor-id-hoặc-tên> \
  --network <net-id-hoặc-tên> \
  --key-name <keypair> \
  --security-group <secgroup> \
  --boot-from-volume <size-GB> \     # boot từ volume
  --volume <volume-id> \             # attach volume
  --min 1 --max 3 \                  # tạo nhiều instance
  --availability-zone <az> \
  --user-data <file-cloudinit.yaml> \
  --tag <tag1> --tag <tag2>

# Thao tác cơ bản
openstack server start <vm>
openstack server stop <vm>
openstack server reboot <vm> [--hard]
openstack server delete <vm> [--wait]

# Resize (thay flavor)
openstack server resize <vm> --flavor <new-flavor>
openstack server resize confirm <vm>
openstack server resize revert <vm>

# Rebuild (cài lại từ image)
openstack server rebuild <vm> --image <new-image>

# Pause / Suspend / Shelve (tiết kiệm tài nguyên)
openstack server pause <vm>
openstack server unpause <vm>
openstack server suspend <vm>
openstack server resume <vm>
openstack server shelve <vm>
openstack server unshelve <vm>

# Rescue mode (fix khi boot lỗi)
openstack server rescue <vm>
openstack server unrescue <vm>

# Lock / Unlock (ngăn user thay đổi)
openstack server lock <vm>
openstack server unlock <vm>

# Evacuate (khi compute node chết)
openstack server evacuate <vm> [--host <target-host>] [--force]
```
**Network & Volume trên VM**
```bash
openstack server add volume <vm> <volume-id>
openstack server remove volume <vm> <volume-id>
openstack server add floating ip <vm> <floating-ip>
openstack server remove floating ip <vm> <floating-ip>
openstack server add security group <vm> <secgroup>
openstack server remove security group <vm> <secgroup>
```
### 2.2 Flavor (Template cấu hình VM)
```bash
openstack flavor list [--all]
openstack flavor show <flavor>
openstack flavor create <tên> --ram <MB> --disk <GB> --vcpus <số> \
  --public --property hw:cpu_policy=dedicated
openstack flavor set <flavor> --property hw:mem_page_size=large
openstack flavor delete <flavor>
```

### 2.3 Keypair (SSH key)
```bash
openstack keypair create <tên> --public-key <file.pub>   # import key
openstack keypair create <tên>                           # tạo mới
openstack keypair list
openstack keypair show <tên>
openstack keypair delete <tên>
```

### 2.4 Compute Service & Hypervisor (Admin/Operator)
```bash
openstack compute service list [--host <host>] [--service nova-compute]
openstack compute service set <host> nova-compute --enable   # hoặc --disable
openstack hypervisor list
openstack hypervisor show <hypervisor>
openstack hypervisor stats show
```

### 2.5 Availability Zone
```bash
openstack availability zone list [--compute]
```

### 2.6 Migration & Live Migration
```bash
openstack server migrate <vm> --live <target-host> --block-migration
openstack server migration list
openstack server migration show <vm> <migration-id>
openstack server migration abort <vm> <migration-id>
```
### 2.7 Consolde & Debug
```bash
openstack console log show <vm> [--length 1000]          # console.log của VM
openstack console url show <vm>                          # noVNC/SPICE
openstack server dump create <vm>                        # dump memory (debug)
```

### 2.8 Các lệnh khác hay dùng
```bash
openstack server group list
openstack server event list <vm>
openstack server add fixed ip <vm> <fixed-ip>
openstack limits show [--project <project>]
```
## 3. NOVA-MANAGE Lệnh Admin (chỉ root hoặc sudo trên controller)
Chạy lệnh: `nova-manage <category> <action> [options]`
### 3.1 Database & Maintenance 
```bash
nova-manage db version
nova-manage api_db version
nova-manage api_db sync
nova-manage db sync [--local_cell]
nova-manage db archive_deleted_rows --until-complete --verbose   # dọn dẹp DB
nova-manage db online_data_migrations [--max-count 100]
```
### 3.2 Cells v2 
```bash
nova-manage cell_v2 simple_cell_setup
nova-manage cell_v2 map_cell0
nova-manage cell_v2 map_instances --cell_uuid <uuid> --max-count 50
nova-manage cell_v2 discover_hosts --verbose
nova-manage cell_v2 list_cells [--verbose]
nova-manage cell_v2 verify_instance --uuid <instance-uuid>
```

### 3.3 Placement & Ironic
```bash
nova-manage placement heal_allocations --verbose
nova-manage placement sync_aggregates
nova-manage db ironic_compute_node_move --ironic-node-uuid <uuid> --destination-host <host>
```

### 3.4 Các lệnh khác
```bash
nova-manage service list
nova-manage volume_attachment show <instance-uuid> <volume-id>
nova-manage limits migrate_to_unified_limits   # migrate quota Keystone
```
## 4. Một vài lệnh hữu dụng
- **Trace request**: Luôn dùng `openstack --debug` hoặc grep `req-` trong log.
- **Tạo script nhanh**:
```bash
openstack server create my-vm --image ubuntu-24.04 --flavor m1.medium --network private --key-name mykey --wait
```
- **Debug khi VM lỗi**:
  - `openstack server show <vm>`: Xem fault message
  - `openstack console log show`
  - Kiểm tra nova-compute.log trên node compute

- **Dọn dẹp định kỳ**:
```bash
nova-manage db archive_deleted_rows --until-complete
nova-manage db purge --all
```
- **Live migration** an toàn:
```bash
openstack server migrate <vm> --live <host> --block-migration --max-bandwidth 10000
```
- **Xem version Nova**: 
```bash
openstack compute service list
nova-manage --version
```