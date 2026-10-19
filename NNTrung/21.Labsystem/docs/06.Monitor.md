# Monitor
- Tạo 1 thư mục:
```bash
sudo mkdir -p /opt/monitor-stack/{prometheus,loki,grafana/provisioning/datasources}
cd /opt/monitor-stack
```
## 1. File `docker-compose.yml`
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "10.0.40.40:9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - back

  loki:
    image: grafana/loki:2.9.0
    container_name: loki
    restart: unless-stopped
    ports:
      - "10.0.40.40:3100:3100"
    volumes:
      - ./loki/loki-config.yml:/etc/loki/loki-config.yml:ro
      - ./loki/data:/loki
    command:
      - '-config.file=/etc/loki/loki-config.yml'
    networks:
      - back

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "10.0.40.40:3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=<đổi_mật_khẩu_mạnh>
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./grafana/data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
      - loki
    networks:
      - back

networks:
  back:
    driver: bridge
```
## 2. File cấu hình `prometheus.yml`
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # ---- node_exporter trên từng máy (network_mode: host nên bind thẳng IP:9100) ----
  - job_name: 'node_exporter'
    static_configs:
      - targets:
          - 10.0.40.36:9100   # LB
          - 10.0.40.37:9100   # Web1
          - 10.0.40.38:9100   # Web2
          - 10.0.40.39:9100   # DB+MinIO+Cache
        labels:
          env: production

  # ---- mysqld_exporter / redis_exporter (chỉ có trên máy DB) ----
  - job_name: 'mysqld_exporter'
    static_configs:
      - targets: ['10.0.40.39:9104']

  - job_name: 'redis_exporter'
    static_configs:
      - targets: ['10.0.40.39:9121']

  # ---- blackbox: check HTTPS trên LB ----
  - job_name: 'blackbox_http_lb'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - 'https://haproxy:443'   # target LOCAL với chính blackbox_exporter trên LB (Docker DNS nội bộ của LB)
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 10.0.40.36:9115   # blackbox_exporter đang chạy TRÊN LB, Prometheus gọi tới đây

  # ---- blackbox: check app Flask trên Web1 ----
  - job_name: 'blackbox_tcp_web1'
    metrics_path: /probe
    params:
      module: [tcp_connect]
    static_configs:
      - targets:
          - 'flasky:5000'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 10.0.40.37:9115

  # ---- blackbox: check app Flask trên Web2 ----
  - job_name: 'blackbox_tcp_web2'
    metrics_path: /probe
    params:
      module: [tcp_connect]
    static_configs:
      - targets:
          - 'flasky:5000'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 10.0.40.38:9115

  # ---- blackbox: check MariaDB/Redis/MinIO trên DB ----
  - job_name: 'blackbox_tcp_db'
    metrics_path: /probe
    params:
      module: [tcp_connect]
    static_configs:
      - targets:
          - 'mariadb:3306'
          - 'redis:6379'
          - 'minio:9000'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 10.0.40.39:9115
```
## 3. Cấu hình `loki-cofig.yml`
```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 720h   # 30 ngày, chỉnh theo nhu cầu lưu log
```
- grafana/provisioning/datasources/datasource.yml
- Provision sẵn 2 datasource để Grafana tự động nhận diện Prometheus + Loki ngay khi khởi động, không cần bạn click tay qua UI:
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
```
## 4. Đăng ký cron trên Monitor
```bash
sudo chmod +x /opt/backup/backup-mariadb.sh /opt/backup/backup-minio.sh
sudo chmod 700 /opt/backup

crontab -e 
0 2 * * * /opt/backup/backup-mariadb.sh
30 2 * * * /opt/backup/backup-minio.sh
```

## 5. Backup script MariaDB+MinIO
### 5.1 Backup MariaDB (mysqldump từ xa, nén, xoay vòng giữ 7 ngày):
```bash
#!/bin/bash
# /opt/backup/backup-mariadb.sh
set -euo pipefail

DB_HOST="10.0.30.30"
DB_USER="backup_user"
DB_PASS="<mật_khẩu_user_backup>"
BACKUP_DIR="/opt/backup/mariadb"
DATE=$(date +%F_%H%M)
KEEP_DAYS=7

mkdir -p "$BACKUP_DIR"

mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" \
  --single-transaction --routines --triggers flasky_db \
  | gzip > "${BACKUP_DIR}/flasky_db_${DATE}.sql.gz"

# xóa backup cũ hơn KEEP_DAYS
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +${KEEP_DAYS} -delete

echo "$(date) - Backup xong: flasky_db_${DATE}.sql.gz" >> /opt/backup/backup.log
```
Tạo user backup chỉ có quyền đọc (least privilege, giống cách bạn đã làm với exporter user):
```bash
CREATE USER 'backup_user'@'10.0.40.40' IDENTIFIED BY '<mật_khẩu_user_backup>';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON flasky_db.* TO 'backup_user'@'10.0.40.40';
FLUSH PRIVILEGES;
```
### 5.2 Backup MinIO(dùng mc `mirror` để đồng bộ bucket về Monitor):
```bash
#!/bin/bash
# /opt/backup/backup-minio.sh
set -euo pipefail

BACKUP_DIR="/opt/backup/minio"
DATE=$(date +%F)
KEEP_DAYS=7

mkdir -p "${BACKUP_DIR}/${DATE}"

# mc alias set (chạy 1 lần thủ công trước, không cần lặp lại mỗi lần chạy script)
# mc alias set dbminio http://10.0.30.30:9000 <MINIO_ROOT_USER> <MINIO_ROOT_PASSWORD>

mc mirror --overwrite dbminio/flasky-bucket "${BACKUP_DIR}/${DATE}"

# nén lại để tiết kiệm dung lượng
tar -czf "${BACKUP_DIR}/${DATE}.tar.gz" -C "${BACKUP_DIR}" "${DATE}"
rm -rf "${BACKUP_DIR}/${DATE}"

# xoay vòng
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +${KEEP_DAYS} -delete

echo "$(date) - Backup MinIO xong: ${DATE}.tar.gz" >> /opt/backup/backup.log
```