# Backend 
- Dưới đây là cấu hình cho backend 1, backend 2 đổi ip `10.0.20.21` và `10.0.40.38`
## 1. File `docker-compose`
```yaml
services:
  flasky:
    build: .
    ports:
      - "10.0.20.20:5000:5000"
    env_file: .env
    restart: always
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
  blackbox_exporter:
    image: prom/blackbox-exporter:latest
    container_name: blackbox_exporter
    restart: unless-stopped
    ports:
      - "10.0.40.37:9115:9115"
    volumes:
      - ./blackbox/blackbox.yml:/etc/blackbox_exporter/config.yml:ro
    command:
      - '--config.file=/etc/blackbox_exporter/config.yml'
    networks:
      - back
    cap_add:
      - NET_RAW
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
## 2. file `.env`
```bash
# .env
SERVER_NAME=flasky.lab.local
DATABASE_URL=mysql+pymysql://flasky:mysql1234@10.0.30.30:3306/flasky_db
REDIS_URL=redis://:redis1234@10.0.30.30:6379/0
MINIO_ENDPOINT=10.0.30.30:9000
```
- Khóa toàn bộ quyền
```bash
find /opt -name ".env*" -exec chmod 600 {} \;
find /opt -name ".env*" -exec chown root:root {} \;
```
## 3. File config `blackbox.yml`
```bash
# blackbox/blackbox.yml — check chính app Flask thay vì check HAProxy như bên LB
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1"]
      valid_status_codes: [200, 301, 302]
      method: GET
      preferred_ip_protocol: "ip4"
  tcp_connect:
    prober: tcp
    timeout: 5s
```
## 4. File config `promtail/promtail-config.yml`
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
        replacement: 'web1'
```