# DB+Cache+MinIO
```bash
sudo mkdir -p /opt/dbstack/{mariadb-init,redis-conf,minio-data,mariadb-data,redis-data}
cd /opt/dbstack
```
## 1. Docker-compose.yml
```yaml
services:
  mariadb:
    image: mariadb:11.4          
    container_name: mariadb
    restart: unless-stopped
    env_file: .env-mariadb
    ports:
      - "10.0.30.30:3306:3306"
    volumes:
      - ./mariadb-data:/var/lib/mysql
      - ./mariadb-init:/docker-entrypoint-initdb.d:ro
    networks:
      - back
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    command: ["redis-server", "/usr/local/etc/redis/redis.conf"]
    ports:
      - "10.0.30.30:6379:6379"
    volumes:
      - ./redis-conf/redis.conf:/usr/local/etc/redis/redis.conf:ro
      - ./redis-data:/data
    networks:
      - back
  minio:
    image: minio/minio:latest
    container_name: minio
    restart: unless-stopped
    env_file: .env-minio
    command: server /data --console-address ":9001"
    ports:
      - "10.0.30.30:9000:9000"
      - "10.0.40.39:9001:9001"
    volumes:
      - ./minio-data:/data
    networks:
      - back
  node_exporter:
    image: prom/node-exporter:latest
    container_name: node_exporter
    restart: unless-stopped
    pid: host
    network_mode: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/host/root:ro,rslave
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/host/root'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
  mysqld_exporter:
    image: prom/mysqld-exporter:latest
    container_name: mysqld_exporter
    restart: unless-stopped
    env_file: .env-mysqld-exporter
    ports:
      - "10.0.40.39:9104:9104"
    networks:
      - back
    depends_on:
      - mariadb
  redis_exporter:
    image: oliver006/redis_exporter:latest
    container_name: redis_exporter
    restart: unless-stopped
    environment:
      - REDIS_ADDR=redis://:redis1234@redis:6379
    ports:
      - "10.0.40.39:9121:9121"
    networks:
      - back
    depends_on:
      - redis
  blackbox_exporter:
    image: prom/blackbox-exporter:latest
    container_name: blackbox_exporter
    restart: unless-stopped
    ports:
      - "10.0.40.39:9115:9115"
    volumes:
      - ./blackbox/blackbox.yml:/etc/blackbox_exporter/config.yml:ro
    command:
      - '--config.file=/etc/blackbox_exporter/config.yml'
    cap_add:
      - NET_RAW
    networks:
      - back
  promtail:
    image: grafana/promtail:2.9.0
    container_name: promtail
    restart: unless-stopped
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./promtail/promtail-config.yml:/etc/promtail/config.yml:ro
    command:
      - '-config.file=/etc/promtail/config.yml'
    networks:
      - back
networks:
  back:
    driver: bridge
```
## 2. File `.env`
```bash
sudo tee .env-mariadb > /dev/null <<'EOF'
MYSQL_ROOT_PASSWORD=mysql1234
MYSQL_DATABASE=flasky_db
MYSQL_USER=flasky
MYSQL_PASSWORD=mysql1234
EOF

sudo tee .env-minio > /dev/null <<'EOF'
MINIO_ROOT_USER=admin_minio1234
MINIO_ROOT_PASSWORD=minio1234
EOF
sudo tee .env-redis > /dev/null <<'EOF' 
REDIS_PASSWORD=redis1234
EOF

sudo tee .env-mysqld-exporter > /dev/null <<'EOF' 
DATA_SOURCE_NAME=exporter:mysql1234@(mariadb:3306)/
EOF
```
- Khóa toàn bộ quyền
```bash
find /opt -name ".env*" -exec chmod 600 {} \;
find /opt -name ".env*" -exec chown root:root {} \;
```
- Check kỹ lại `.venv` bên Backend
## 3. File `mariadb-init/01-create-exporter-user.sql` 
```sql
CREATE USER IF NOT EXISTS 'exporter'@'%' IDENTIFIED BY 'mysql1234';
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'%';
FLUSH PRIVILEGES;
```
Điều này đảm bảo nếu container `mysqld_exporter` bị chiếm quyền, kẻ tấn công chỉ có quyền SELECT/đọc trạng thái, không có quyền ghi/xóa dữ liệu — nguyên tắc least-privilege.

## 4. File `redis-conf/redis.conf` 
- Cấu hình bắt buộc set password
```conf
bind 0.0.0.0
protected-mode yes
requirepass redis1234

# --- Persistence ---
appendonly yes
appendfsync everysec
dir /data

# RDB snapshot dự phòng thêm (không bắt buộc nếu đã có AOF, nhưng an toàn hơn)
save 900 1
save 300 10
save 60 10000
```

## 5. File `blackbox.yml`
```yaml
modules: 
  tcp_connect:
    prober: tcp
    timeout: 5s
```
- Tạo thêm file config `promtail/promtail-config.yml`
```bash
mkdir -p promtail
```
```yaml
# promtail/promtail-config.yml (LB)
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://10.0.40.40:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
      - target_label: 'host'
        replacement: 'db'
```

### Test
- Truy cập database:
```bash
sudo docker exec -it mariadb mariadb -u root -p flasky_db
```
- Hoặc 
```bash
sudo docker exec -it mariadb 
mariadb -u root -p
SHOW DATABASES;
USE <ten_databases>;
SHOW TABLES;
DESC ten_bang;
SELECT * FROM ten_bang;
```
```bash
SELECT id, email, username, confirmed FROM users;
UPDATE users SET confirmed=1 WHERE email='email_đăng_ký@gmail.com';
```