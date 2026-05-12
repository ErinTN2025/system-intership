# Tìm hiểu về Docker
Khi nhắc đến "Docker", chúng ta cần phân biệt rõ ba thực thể: **Docker, Inc.** (Công ty), **Docker Engine** (Công nghệ cốt lõi), và **Moby Project** (Dự án mã nguồn mở).

## Docker, Inc. - Công ty đứng sau cuộc cách mạng
- Tiền thân: Thành lập bởi Solomon Hykes với tên gọi dotCloud (một nhà cung cấp PaaS).
- Trọng tâm hiện tại: Docker, Inc. không còn tập trung vào việc duy trì toàn bộ hạ tầng container mã nguồn thấp mà chuyển sang cung cấp các công cụ hỗ trợ quy trình phát triển (Developer Experience - DX) như:
  - **Docker Desktop**: Công cụ GUI quản lý Docker trên Windows/macOS/Linux (lưu ý: có chính sách bản quyền cho doanh nghiệp lớn).
  - **Docker Hub**: Registry lưu trữ image lớn nhất thế giới.
  - **Docker Scout**: Công cụ phân tích bảo mật và chuỗi cung ứng phần mềm (ra mắt 2023, tích hợp sâu vào CLI từ 2024).

---

## 1. Khái niệm
**Docker** là nền tảng containerization mã nguồn mở, cho phép đóng gói ứng dụng cùng toàn bộ phụ thuộc (thư viện, runtime, cấu hình) vào một đơn vị chuẩn hóa gọi là **container**. Container chạy độc lập, nhẹ và nhất quán trên mọi môi trường (dev, test, production).

**Docker** giúp nhà phát triển:
  - Đóng gói toàn bộ ứng dụng cùng thư viện, công cụ, cấu hình vào một **Docker Image** nhỏ gọn.
  - Chạy ứng dụng đó ở bất kỳ đâu mà không lo khác biệt môi trường (máy thật, server, cloud, v.v.).

![altimage](../images/Screenshot_1.png)

---

## 2. Kiến trúc Công nghệ Docker (The Docker Stack)
Công nghệ Docker hiện nay không còn là một khối duy nhất (monolithic) mà được chia thành nhiều thành phần chuyên biệt theo tiêu chuẩn mở.

```
Docker CLI
    ↓
dockerd (Docker Engine)
    ↓
containerd (quản lý vòng đời)
    ↓
containerd-shim (giữ container sống độc lập)
    ↓
runc (tạo container → exit)
    ↓
Container Process (Linux process bị cô lập)
```

### 2.1 Container Runtime (Môi trường thực thi)

![altimage](../images/Screenshot_2.png)

Docker sử dụng kiến trúc phân tầng để quản lý container một cách hiệu quả và ổn định.

- **Low-level Runtime — runc**: Hiện thực hóa tiêu chuẩn OCI Runtime Spec. Làm việc ở tầng thấp nhất, Nhiệm vụ của nó rất đơn giản, tạo container bằng tính năng của Linux, sau đó thoát ngay — không duy trì trạng thái. Nó sẽ:
  - tạo namespace
  - tạo cgroup
  - mount filesystem
  - start process
- **High-level Runtime — containerd**: Là CNCF Graduated Project, đóng vai trò quản lý, điều phối toàn bộ vòng đời container: pull image, quản lý container, quản lý storage/network, start/stop container. Khi cần tạo container, **containerd** gọi runc.
- **containerd-shim**: Nó là tiến trình đứng giữa: containerd và container thực tế. Để đảm bảo container vẫn tiếp tục hoạt động ngay cả khi `containerd` hoặc `dockerd` bị restart. Tiến trình này giữ kết nối trực tiếp với process của container và duy trì trạng thái hoạt động của nó. Nhờ đó, container có thể tiếp tục chạy độc lập mà không bị ảnh hưởng khi Docker Engine được nâng cấp hoặc khởi động lại.

Về bản chất, container không phải là một máy ảo hoàn chỉnh mà chỉ là một process được cô lập trên Linux thông qua các cơ chế của kernel. Docker cung cấp lớp quản lý và tự động hóa giúp việc tạo, triển khai và vận hành các process cô lập này trở nên thuận tiện hơn.

### 2.2 Docker Daemon — dockerd
Tiến trình chạy nền trung tâm của Docker Engine. Nó:
- Lắng nghe API request từ Docker CLI qua Unix socket (`/var/run/docker.sock`).
- Quản lý image, container, network, volume ở mức cao.
- Giao tiếp với **containerd** để thực thi container.
- Từ Docker Engine v23.0+, dùng **BuildKit** làm engine build mặc định.

### 2.3 Docker CLI
Giao diện dòng lệnh mà người dùng tương tác. CLI gửi lệnh đến dockerd qua Docker REST API. Bản thân CLI không thực thi container — nó chỉ là client.

### 2.4 BuildKit (Build Engine mặc định từ v23.0)
BuildKit là engine build thế hệ mới, mặc định từ Docker Engine v23.0 (2023). Điểm nổi bật:
- **Build song song**: Phân tích Dockerfile như dependency graph, chạy các bước độc lập đồng thời.
- **Cache thông minh**: Hỗ trợ cache mount cho package manager (npm, pip, apt...).
- **Bỏ qua stage không cần thiết**: Chỉ build các stage mà target stage phụ thuộc vào.
- **Build đa nền tảng**: `docker buildx build --platform linux/amd64,linux/arm64`.

### 2.5 Thay đổi lớn năm 2026 — containerd image store
Từ **Docker Engine v27+**, containerd image store trở thành mặc định cho cài đặt mới. Đây là thay đổi kiến trúc lớn nhất kể từ khi tích hợp containerd:
- Trước đây: Docker dùng image store riêng → Kubernetes dùng containerd store riêng → hai "thế giới" không thấy nhau.
- Từ Docker v27+: Dùng chung một image store → `docker images` và `crictl images` thấy cùng image → giảm lãng phí và nhất quán hơn.

---

## 3. Các Khái niệm Cốt lõi

### 3.1 Image
- Là **template chỉ đọc (read-only)** dùng để tạo container.
- Được xây dựng từ nhiều **layer** chồng lên nhau (Union Filesystem). Mỗi lệnh `RUN`, `COPY`, `ADD` trong Dockerfile tạo ra một layer mới.
- Layer được **cache và tái sử dụng** — nếu layer không thay đổi, Docker không build lại.
- Được đặt tên theo format: `[registry/][user/]name[:tag]`
  - Ví dụ: `nginx:1.27-alpine`, `docker.io/library/ubuntu:24.04`

### 3.2 Container
- Là **instance đang chạy** của một Image — giống như class (image) và object (container).
- Có thêm một **writable layer** trên cùng (chỉ tồn tại trong vòng đời container).
- Các container **độc lập** với nhau và với host nhờ Linux Namespaces (PID, NET, MNT, UTS, IPC, USER).
- Tài nguyên (CPU, RAM) bị giới hạn bởi **Cgroups**.

### 3.3 Volume
- Là cơ chế lưu trữ **persistent** dành cho container (dữ liệu không mất khi container bị xóa).
- Được Docker quản lý, lưu tại `/var/lib/docker/volumes/` trên host.
- Ưu tiên dùng **named volume** thay vì bind mount cho production.

### 3.4 Network
Docker cung cấp nhiều loại network driver:

| Driver | Mô tả | Dùng khi |
|---|---|---|
| `bridge` | Mạng nội bộ, mặc định cho container đơn lẻ | Dev, test |
| `host` | Dùng thẳng network stack của host | Cần performance cao |
| `none` | Không có network | Container hoàn toàn cô lập |
| `overlay` | Kết nối nhiều Docker host | Docker Swarm / multi-host |

> Các container trong **cùng một custom bridge network** có thể giao tiếp với nhau qua **tên container** (DNS tự động).

### 3.5 Registry
Kho lưu trữ và phân phối image. Mặc định là **Docker Hub** (`docker.io`). Ngoài ra còn có:
- **GitHub Container Registry** (ghcr.io)
- **Google Artifact Registry** (gcr.io)
- **Self-hosted**: Harbor, Nexus, Gitea...

---

## 4. Lệnh Docker Cơ bản

### 4.1 Quản lý Image

```bash
docker pull nginx:1.27-alpine          # Tải image từ registry
docker images                          # Liệt kê image trên máy
docker image ls                        # Tương tự lệnh trên
docker image inspect nginx:1.27-alpine # Xem chi tiết image
docker rmi nginx:1.27-alpine           # Xóa image
docker image prune                     # Xóa image không dùng (dangling)
docker image prune -a                  # Xóa tất cả image không được dùng bởi container nào
```

### 4.2 Quản lý Container

```bash
# Tạo và chạy container
docker run nginx                          # Chạy và gắn vào terminal
docker run -d nginx                       # Chạy ngầm (detached)
docker run -d -p 8080:80 nginx            # Map port host:container
docker run -d --name my-web nginx         # Đặt tên container
docker run -it ubuntu:24.04 bash          # Chạy tương tác với shell
docker run --rm ubuntu:24.04 echo "hello" # Tự xóa sau khi chạy xong
docker run -e MY_VAR=value nginx          # Truyền biến môi trường
docker run -v my-vol:/data nginx          # Mount named volume
docker run --memory="512m" --cpus="1" nginx  # Giới hạn tài nguyên

# Quản lý vòng đời
docker ps                    # Liệt kê container đang chạy
docker ps -a                 # Liệt kê tất cả container (cả đã dừng)
docker stop <name|id>        # Dừng container (gửi SIGTERM, chờ 10s rồi SIGKILL)
docker start <name|id>       # Khởi động lại container đã dừng
docker restart <name|id>     # Restart container
docker rm <name|id>          # Xóa container đã dừng
docker rm -f <name|id>       # Buộc xóa container đang chạy

# Tương tác
docker exec -it <name> bash          # Mở shell vào container đang chạy
docker exec <name> cat /etc/hosts    # Chạy lệnh trong container
docker logs <name>                   # Xem log
docker logs -f <name>                # Xem log realtime (follow)
docker logs --tail 100 <name>        # Xem 100 dòng log cuối
docker inspect <name>                # Xem toàn bộ metadata

# Dọn dẹp
docker container prune               # Xóa tất cả container đã dừng
docker system prune                  # Xóa container, image, network không dùng
docker system prune -a --volumes     # Xóa sạch toàn bộ (cẩn thận!)
```

### 4.3 Quản lý Volume & Network

```bash
# Volume
docker volume create my-data          # Tạo volume
docker volume ls                      # Liệt kê volume
docker volume inspect my-data         # Xem chi tiết
docker volume rm my-data              # Xóa volume
docker volume prune                   # Xóa volume không được dùng

# Network
docker network create my-net          # Tạo custom bridge network
docker network ls                     # Liệt kê network
docker network inspect my-net         # Xem chi tiết
docker network connect my-net <name>  # Kết nối container vào network
docker network rm my-net              # Xóa network
```

### 4.4 Build Image

```bash
docker build -t my-app:1.0 .                      # Build từ Dockerfile ở thư mục hiện tại
docker build -t my-app:1.0 -f Dockerfile.prod .   # Chỉ định Dockerfile
docker build --no-cache -t my-app:1.0 .           # Build không dùng cache
docker buildx build --platform linux/amd64,linux/arm64 -t my-app:1.0 . --push  # Build đa nền tảng
```

---

## 5. Dockerfile

### 5.1 Các lệnh cơ bản

```dockerfile
FROM ubuntu:24.04               # Base image (luôn là lệnh đầu tiên)
LABEL maintainer="ten@email.com" # Metadata

# Biến môi trường
ENV NODE_ENV=production
ARG BUILD_VERSION=1.0           # Biến chỉ dùng lúc build (không có trong container)

# Lệnh thực thi khi build
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

# Thư mục làm việc trong container
WORKDIR /app

# Copy file từ host vào image
COPY package*.json ./           # Chỉ copy file cần thiết trước (tận dụng cache)
COPY . .                        # Copy toàn bộ source

# Expose port (chỉ là tài liệu, không tự map ra host)
EXPOSE 3000

# Mount point cho volume
VOLUME ["/data"]

# Lệnh chạy khi container khởi động
CMD ["node", "server.js"]       # Có thể bị override bởi docker run
ENTRYPOINT ["node"]             # Không bị override, CMD là tham số mặc định
```

> **CMD vs ENTRYPOINT**: Dùng `ENTRYPOINT` khi muốn container hoạt động như một executable cố định. Dùng `CMD` cho tham số mặc định có thể thay đổi.

### 5.2 Multi-stage Build (Best practice 2026)
Kỹ thuật dùng nhiều `FROM` trong một Dockerfile: stage đầu để build, stage cuối chỉ copy artifact cần thiết → **image production nhỏ gọn, không chứa compiler hay build tools**.

```dockerfile
# Stage 1 — Build
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production    # npm ci nhanh và tái lập được hơn npm install
COPY . .
RUN npm run build

# Stage 2 — Production (chỉ chứa kết quả build)
FROM node:22-alpine AS runner
WORKDIR /app
# Tạo user không phải root (bảo mật)
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
USER appuser
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### 5.3 Cache Mount với BuildKit (tối ưu tốc độ build)

```dockerfile
# Cache thư mục npm để không tải lại mỗi lần build
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production

# Cache apt để không download lại package
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y curl
```

### 5.4 .dockerignore
Tương tự `.gitignore` — loại trừ file không cần thiết khỏi build context, giúp build nhanh hơn và image nhỏ hơn.

```
node_modules
.git
.env
*.log
dist
coverage
.DS_Store
```

### 5.5 Best Practices Dockerfile

| Nguyên tắc | Lý do |
|---|---|
| Dùng image tag cụ thể (`node:22-alpine`) | Tránh build bị thay đổi do tag `latest` |
| Dùng `alpine` hoặc `distroless` cho production | Image nhỏ, ít lỗ hổng |
| Gộp `RUN` liên quan thành một lệnh | Giảm số layer |
| Copy `package.json` trước khi copy source | Cache layer dependencies |
| Xóa cache apt ngay trong cùng `RUN` | Không để cache vào layer |
| Chạy bằng user không phải root | Bảo mật |
| Dùng `COPY` thay vì `ADD` | `ADD` có hành vi ẩn (tự giải nén) |
| Dùng multi-stage build | Image production nhỏ gọn |

---

## 6. Docker Compose

Docker Compose dùng để định nghĩa và chạy **ứng dụng đa container** (web + db + cache...) từ một file YAML duy nhất.

> **Lưu ý 2024+**: Compose V1 (`docker-compose`) đã bị **deprecated**. Luôn dùng **Compose V2**: `docker compose` (có dấu cách, không có gạch nối).

### 6.1 Cấu trúc `compose.yaml`

> Từ Compose V2, tên file được khuyến nghị là `compose.yaml` (thay vì `docker-compose.yml`), tuy nhiên cả hai đều hoạt động.

```yaml
# compose.yaml
services:
  web:
    build: .                          # Build từ Dockerfile ở thư mục hiện tại
    image: my-app:latest
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DB_HOST=db                    # Tên service = hostname tự động
    env_file:
      - .env                          # Load biến từ file .env
    depends_on:
      db:
        condition: service_healthy    # Chờ db healthy mới start
    volumes:
      - ./src:/app/src                # Bind mount (dev)
    networks:
      - app-net
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - db-data:/var/lib/postgresql/data   # Named volume (production)
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-net

  cache:
    image: redis:7-alpine
    networks:
      - app-net

volumes:
  db-data:                            # Named volume được Docker quản lý

networks:
  app-net:
    driver: bridge
```

### 6.2 Lệnh Docker Compose cơ bản

```bash
docker compose up                    # Khởi động tất cả service (foreground)
docker compose up -d                 # Khởi động ngầm (detached)
docker compose up -d --build         # Build lại image rồi khởi động
docker compose up -d web             # Chỉ khởi động service "web"

docker compose down                  # Dừng và xóa container, network
docker compose down -v               # Dừng và xóa cả volume (mất data!)

docker compose ps                    # Liệt kê service và trạng thái
docker compose logs -f               # Xem log realtime tất cả service
docker compose logs -f web           # Xem log service "web"

docker compose exec web bash         # Mở shell vào service "web"
docker compose exec db psql -U user  # Chạy lệnh trong service "db"

docker compose restart web           # Restart service "web"
docker compose stop                  # Dừng service (không xóa)
docker compose start                 # Khởi động lại service đã dừng

docker compose pull                  # Pull image mới nhất cho tất cả service
docker compose build                 # Build lại tất cả image

docker compose up -d --scale web=3  # Scale service "web" lên 3 instance
```

---

## 7. Volume & Network chi tiết

### 7.1 Ba loại mount

| Loại | Cú pháp | Dùng khi |
|---|---|---|
| **Named Volume** | `-v my-vol:/data` | Lưu data production, DB |
| **Bind Mount** | `-v /host/path:/container/path` | Dev: sync code realtime |
| **tmpfs Mount** | `--tmpfs /tmp` | Data tạm thời, không cần persist |

```bash
# Named volume — Docker quản lý hoàn toàn
docker run -d -v db-data:/var/lib/postgresql/data postgres:16

# Bind mount — map thư mục thực trên host
docker run -d -v $(pwd)/src:/app/src node:22-alpine

# Read-only bind mount
docker run -d -v $(pwd)/config:/config:ro nginx
```

### 7.2 Giao tiếp giữa các container

```bash
# Tạo custom network
docker network create my-net

# Chạy 2 container trong cùng network — giao tiếp qua tên container
docker run -d --name db --network my-net postgres:16
docker run -d --name web --network my-net -e DB_HOST=db my-app

# Container "web" có thể kết nối đến "db:5432" bằng tên "db"
```

---

## 8. Docker Scout — Bảo mật Image (2026)

Docker Scout quét CVE (lỗ hổng bảo mật) trong image và đề xuất cách khắc phục.

```bash
# Quét image hiện tại
docker scout cves my-app:latest

# Xem tóm tắt nhanh
docker scout quickview my-app:latest

# So sánh 2 phiên bản
docker scout compare my-app:v1.0 my-app:v2.0

# Đề xuất base image tốt hơn
docker scout recommendations my-app:latest
```

---

## 9. Best Practices tổng hợp (2026)

### 9.1 Image
- Luôn chỉ định tag cụ thể, không dùng `latest` trong production.
- Dùng `alpine` hoặc `distroless` để giảm attack surface.
- Quét image định kỳ bằng Docker Scout hoặc Trivy.
- Dùng multi-stage build: image dev và production từ cùng một Dockerfile.

### 9.2 Container
- Một container = một tiến trình chính (Single Responsibility).
- Không lưu state quan trọng trong container layer — dùng volume.
- Thiết lập `--memory` và `--cpus` để tránh container chiếm hết tài nguyên host.
- Luôn dùng `--restart unless-stopped` hoặc `--restart always` cho production.
- Chạy bằng non-root user.

### 9.3 Bảo mật
- Không để secret (password, API key) trong Dockerfile hay image layer.
- Dùng **Docker Secrets** (Swarm) hoặc biến môi trường qua file `.env` không commit lên git.
- Giới hạn capabilities: `--cap-drop ALL --cap-add NET_BIND_SERVICE`.
- Dùng **read-only filesystem** nếu có thể: `--read-only`.

### 9.4 Hiệu năng build
- Sắp xếp lệnh trong Dockerfile: thứ tự **ít thay đổi → hay thay đổi** để tận dụng cache.
- Dùng `.dockerignore` để giảm build context.
- Dùng `--mount=type=cache` cho package manager.
- Dùng `docker buildx` để build đa nền tảng (amd64 + arm64).

---

## 10. Cheat Sheet nhanh

```bash
# Vòng đời cơ bản
docker pull image:tag                  # Tải image
docker build -t name:tag .             # Build image
docker run -d -p host:cont name:tag    # Chạy container
docker exec -it <name> sh             # Vào shell container
docker logs -f <name>                  # Xem log
docker stop <name> && docker rm <name> # Dừng và xóa

# Dọn dẹp
docker system df                       # Xem dung lượng Docker đang dùng
docker system prune -a                 # Xóa tất cả không dùng (trừ volume)
docker system prune -a --volumes       # Xóa tất cả kể cả volume

# Thông tin
docker version                         # Phiên bản Docker Client & Engine
docker info                            # Thông tin hệ thống Docker
docker stats                           # Monitor CPU/RAM realtime các container
docker top <name>                      # Xem process trong container
```
