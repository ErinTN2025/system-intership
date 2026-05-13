# Install Docker
## 1. Windows
- Tải trực tiếp từ link nhà sản xuất:
`https://docs.docker.com/desktop/setup/install/windows-install/`

## 2. Ubuntu
Để bắt đầu với Docker Engine trên Ubuntu, hãy đảm bảo bạn đã đáp ứng các điều kiện tiên quyết, sau đó thực hiện theo các bước cài đặt

### Điều kiện tiên quyết

#### Hạn chế của tường lửa

Trước khi cài đặt Docker, hãy lưu ý các tác động bảo mật và sự không tương thích của tường lửa sau đây.

* Nếu bạn sử dụng `ufw` hoặc `firewalld` để quản lý cài đặt tường lửa, hãy lưu ý rằng khi bạn công khai (expose) các cổng container bằng Docker, các cổng này sẽ **bỏ qua** các quy tắc tường lửa của bạn. Để biết thêm thông tin, hãy tham khảo [Docker và ufw](https://www.google.com/search?q=/engine/network/packet-filtering-firewalls/%23docker-and-ufw).
* Docker chỉ tương thích với `iptables-nft` và `iptables-legacy`. Các quy tắc tường lửa được tạo bằng `nft` không được hỗ trợ trên hệ thống đã cài đặt Docker. Đảm bảo rằng mọi bộ quy tắc tường lửa bạn sử dụng đều được tạo bằng `iptables` hoặc `ip6tables` và bạn đã thêm chúng vào chuỗi `DOCKER-USER`.

### Yêu cầu về hệ điều hành (OS)

Để cài đặt Docker Engine, bạn cần phiên bản 64-bit của một trong các phiên bản Ubuntu sau:

* Ubuntu Resolute 26.04 (LTS)
* Ubuntu Questing 25.10
* Ubuntu Noble 24.04 (LTS)
* Ubuntu Jammy 22.04 (LTS)

Docker Engine cho Ubuntu tương thích với các kiến trúc: x86_64 (hoặc amd64), armhf, arm64, s390x, và ppc64le (ppc64el).

**Lưu ý**: Việc cài đặt trên các bản phân phối dựa trên Ubuntu (như Linux Mint) không được hỗ trợ chính thức (mặc dù nó có thể hoạt động).

### Gỡ cài đặt các phiên bản cũ

Trước khi cài đặt Docker Engine, bạn cần gỡ bỏ bất kỳ gói nào gây xung đột.

Các bản phân phối Linux của bạn có thể cung cấp các gói Docker không chính thức, điều này có thể xung đột với các gói chính thức từ Docker. Bạn phải gỡ cài đặt các gói này trước:

* `docker.io`
* `docker-compose`
* `docker-compose-v2`
* `docker-doc`
* `podman-docker`

Ngoài ra, Docker Engine phụ thuộc vào `containerd` và `runc`. Docker Engine gộp các phụ thuộc này thành một gói: `containerd.io`. Nếu bạn đã cài đặt `containerd` hoặc `runc` trước đó, hãy gỡ cài đặt chúng để tránh xung đột.

Chạy lệnh sau để gỡ cài đặt tất cả các gói xung đột:

```console
$ sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1)

```

`apt` có thể report rằng bạn không cài đặt gói nào trong số này.

Các hình ảnh (images), container, volume và mạng được lưu trữ tại `/var/lib/docker/` sẽ **không** tự động bị xóa.

1. **Gỡ bỏ các gói:**
```console
$ sudo apt purge docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras
```


2. **Xóa dữ liệu (Cảnh báo: Hành động này sẽ xóa sạch dữ liệu Docker của bạn):**
```console
$ sudo rm -rf /var/lib/docker
$ sudo rm -rf /var/lib/containerd
```


3. **Xóa nguồn danh sách và khóa:**
```console
$ sudo rm /etc/apt/sources.list.d/docker.sources
$ sudo rm /etc/apt/keyrings/docker.asc
```
---

### Các phương thức cài đặt

Bạn có thể cài đặt Docker Engine theo nhiều cách khác nhau:

1. **Docker Desktop cho Linux:** Cách dễ nhất và nhanh nhất.
2. **Từ kho lưu trữ apt của Docker:** Cách phổ biến nhất (khuyên dùng).
3. **Cài đặt thủ công:** Tải gói `.deb` và quản lý cập nhật thủ công.
4. **Script tiện ích:** Chỉ khuyến nghị cho môi trường thử nghiệm và phát triển.

### I. Cài đặt bằng kho lưu trữ apt 

Trước khi cài đặt Docker Engine lần đầu tiên, bạn cần thiết lập kho lưu trữ Docker.

**1. Thiết lập kho lưu trữ apt của Docker:**

```bash
# Thêm khóa GPG chính thức của Docker:
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Thêm kho lưu trữ vào Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
```

**2. Cài đặt các gói Docker:**

*Cài đặt phiên bản mới nhất:*

```bash
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

*Cài đặt phiên bản cụ thể (tùy chọn):*
Liệt kê các phiên bản có sẵn:

```bash
sudo apt list --all-versions docker-ce

docker-ce/noble 5:29.4.3-1~ubuntu.24.04~noble <arch>
docker-ce/noble 5:29.4.2-1~ubuntu.24.04~noble <arch>
...
```

Sau đó chọn phiên bản và cài đặt:

```bash
$ VERSION_STRING=5:29.4.3-1~ubuntu.24.04~noble
$ sudo apt install docker-ce=$VERSION_STRING docker-ce-cli=$VERSION_STRING containerd.io docker-buildx-plugin docker-compose-plugin
```

Sau khi cài đặt, kiểm tra xem Docker đã chạy chưa:
```bash
sudo systemctl status docker
```
Nếu chưa chạy, hãy khởi động thủ công:

```bash
sudo systemctl start docker`
```

**3. Kiểm tra cài đặt:**

```bash
sudo docker run hello-world
```

###  II. Cài đặt từ gói (Package)

Nếu bạn không thể sử dụng kho lưu trữ, hãy tải tệp `.deb` thủ công:

1. Truy cập [download.docker.com/linux/ubuntu/dists/](https://download.docker.com/linux/ubuntu/dists/).
2. Chọn phiên bản Ubuntu của bạn.
3. Vào `pool/stable/` và chọn kiến trúc máy (ví dụ: `amd64`, `armhf`, `arm64`, or `s390x`).
4. Tải về các tệp `.deb` cho Docker Engine, CLI, containerd, and Docker Compose packages: 
  - `containerd.io_<version>_<arch>.deb`
  - `docker-ce_<version>_<arch>.deb`
  - `docker-ce-cli_<version>_<arch>.deb`
  - `docker-buildx-plugin_<version>_<arch>.deb`
  - `docker-compose-plugin_<version>_<arch>.deb`
5. Cài đặt các gói:
```bash
sudo dpkg -i ./containerd.io_<version>_<arch>.deb \
  ./docker-ce_<version>_<arch>.deb \
  ./docker-ce-cli_<version>_<arch>.deb \
  ./docker-buildx-plugin_<version>_<arch>.deb \
  ./docker-compose-plugin_<version>_<arch>.deb
```


### III. Cài đặt bằng script tiện ích
Docker cung cấp một script tiện ích tại [https://get.docker.com/](https://get.docker.com/) để cài đặt Docker vào môi trường phát triển một cách tự động (non-interactively).

**Cảnh báo quan trọng:**
* Script này **không được khuyến nghị** cho môi trường production (môi trường vận hành thực tế).
* Nó hữu ích để tạo các script cấp phát (provisioning) tùy chỉnh theo nhu cầu của bạn.
* Luôn kiểm tra kỹ các script tải từ internet trước khi chạy cục bộ trên máy.

**Các rủi ro và hạn chế cần biết**
* **Quyền hạn:** Script yêu cầu quyền `root` hoặc `sudo` để chạy.
* **Tự động nhận diện:** Script cố gắng tự phát hiện bản phân phối và phiên bản Linux của bạn để tự cấu hình hệ thống quản lý gói.
* **Không thể tùy chỉnh:** Script không cho phép bạn tùy chỉnh hầu hết các tham số cài đặt.
* **Tự động cài đặt phụ thuộc:** Script sẽ cài đặt các gói phụ thuộc và đề xuất mà không hỏi ý kiến xác nhận. Điều này có thể cài đặt một lượng lớn các gói tùy thuộc vào cấu hình hiện tại của máy chủ.
* **Phiên bản:** Theo mặc định, script cài đặt phiên bản ổn định (stable) mới nhất của Docker, containerd và runc. Điều này có thể dẫn đến việc nâng cấp phiên bản lớn (major version) ngoài ý muốn. Hãy luôn thử nghiệm nâng cấp trong môi trường test trước.
* **Không dùng để nâng cấp:** Script không được thiết kế để nâng cấp một bản cài đặt Docker hiện có. Nếu dùng để cập nhật, các gói phụ thuộc có thể không được cập nhật lên phiên bản mong muốn, dẫn đến lỗi thời.

---

**Cách thực hiện**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**Lưu ý sau cài đặt**

* **Khởi động dịch vụ:** Dịch vụ Docker tự động khởi động trên các bản phân phối dựa trên **Debian** (như Ubuntu). Trên các bản phân phối dựa trên **RPM** (CentOS, Fedora, RHEL), bạn cần khởi động thủ công bằng `systemctl` hoặc lệnh `service`.
* **Quyền truy cập:** Mặc định người dùng không có quyền root sẽ không thể chạy lệnh Docker.

**Cài đặt các bản thử nghiệm (Pre-releases)**

Docker cũng cung cấp script tại [https://test.docker.com/](https://test.docker.com/) để cài đặt các bản tiền phát hành. Script này cấu hình trình quản lý gói của bạn sử dụng kênh **test**, bao gồm cả các bản ổn định và bản thử nghiệm (beta, release-candidates).

Để cài đặt bản mới nhất từ kênh test:

```bash
$ curl -fsSL https://test.docker.com -o test-docker.sh
$ sudo sh test-docker.sh
```

**Nâng cấp Docker sau khi dùng script**

Nếu bạn đã cài đặt Docker bằng script tiện ích, bạn nên **nâng cấp Docker trực tiếp bằng trình quản lý gói** (ví dụ: `apt upgrade`) của hệ điều hành.

**Không có lợi ích gì khi chạy lại script tiện ích.** Việc chạy lại có thể gây lỗi nếu nó cố gắng cài đặt lại các kho lưu trữ (repositories) đã tồn tại trên máy chủ.

## Tham khảo thêm cách cài đặt tại:
- `https://docs.docker.com/engine/install/`