# Hướng dẫn tích hợp Redis + MinIO vào Flasky

Áp dụng cho project Flasky (Flask 0.12.2, Flask-SQLAlchemy 2.2, Python 3.6, chạy Docker
với 2 backend `web1`/`web2` đứng sau HAProxy, DB MariaDB tách riêng).

Mục tiêu:
- **Redis** → chống brute-force login (rate limit theo IP, dùng chung giữa web1/web2)
- **MinIO** → cho user upload avatar riêng, thay vì chỉ dùng Gravatar

---

## 0. Thông tin server đã có sẵn

```
REDIS_URL=redis://:redis1234@10.0.30.30:6379/0
MINIO_ENDPOINT=10.0.30.30:9000
```

---

## Phần A — Chuẩn bị MinIO (tạo access key riêng cho app, không dùng root key)

### A.1. Cài MinIO Client `mc`

Cách 1 — cài vào `~/bin` (không cần quyền root):
```bash
mkdir -p ~/bin
curl https://dl.min.io/client/mc/release/linux-amd64/mc -o ~/bin/mc
chmod +x ~/bin/mc
export PATH=$PATH:~/bin
echo 'export PATH=$PATH:~/bin' >> ~/.bashrc
```

Cách 2 — dùng `mc` có sẵn trong container MinIO (nếu image hỗ trợ):
```bash
sudo docker exec -it minio mc --version
```
Nếu có, thêm tiền tố `sudo docker exec -it minio` trước mọi lệnh `mc` ở các bước dưới.

Thoát khỏi container khi cần: gõ `exit` hoặc `Ctrl+D` (không làm dừng container).

### A.2. Trỏ `mc` tới MinIO server bằng root key

```bash
mc alias set myminio http://10.0.30.30:9000 admin_minio1234 minio1234
mc admin info myminio
```

### A.3. Tạo bucket riêng cho avatar

```bash
mc mb myminio/flasky-avatars
```

### A.4. Tạo policy least-privilege (chỉ đọc/ghi đúng bucket này)

```bash
cat > flasky-avatars-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::flasky-avatars",
        "arn:aws:s3:::flasky-avatars/*"
      ]
    }
  ]
}
EOF

mc admin policy create myminio flasky-avatars-rw flasky-avatars-policy.json
```

### A.5. Tạo access key riêng cho app + gắn policy

```bash
openssl rand -base64 24   # dùng chuỗi này làm secret key
mc admin user add myminio flasky-app <secret-key-vừa-tạo>
mc admin policy attach myminio flasky-avatars-rw --user flasky-app
mc admin user list myminio   # xác nhận user đã tạo
```

> **Vì sao không dùng thẳng root key:** nếu `.env` trên web1/web2 bị lộ, kẻ tấn công
> chỉ đụng được đúng 1 bucket avatar, không có quyền admin toàn bộ MinIO.

---

## Phần B — Sửa code Flasky

### B.1. `requirements/common.txt` — thêm cuối file

```
Flask-Limiter==1.4
redis==3.5.3
minio==5.0.10
```
(chọn bản cũ vì Flask 0.12.2 quá cũ, Flask-Limiter mới đòi Flask ≥ 2)

### B.2. `config.py` — thêm vào class `Config`, ngay sau `FLASKY_SLOW_DB_QUERY_TIME`

```python
    FLASKY_SLOW_DB_QUERY_TIME = 0.5

    # Redis (rate limiting)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_HEADERS_ENABLED = True

    # MinIO (avatar storage)
    MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT') or 'localhost:9000'
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY')
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY')
    MINIO_BUCKET = os.environ.get('MINIO_BUCKET') or 'flasky-avatars'
    MINIO_SECURE = os.environ.get('MINIO_SECURE', 'false').lower() in \
        ['true', 'on', '1']
```

Tùy chọn — trong `class TestingConfig` thêm để test không bị giới hạn rate limit:
```python
    RATELIMIT_ENABLED = False
```

### B.3. `.env` trên **cả web1 và web2** (phải giống hệt nhau)

```
REDIS_URL=redis://:redis1234@10.0.30.30:6379/0
MINIO_ENDPOINT=10.0.30.30:9000
MINIO_ACCESS_KEY=flasky-app
MINIO_SECRET_KEY=<secret key tạo ở bước A.5>
MINIO_BUCKET=flasky-avatars
MINIO_SECURE=false
```

### B.4. `app/__init__.py` — khởi tạo Flask-Limiter

Thêm import đầu file:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
```

Thêm biến global (cạnh `pagedown = PageDown()`):
```python
limiter = Limiter(key_func=get_remote_address)
```

Trong `create_app()`, thêm ngay sau `pagedown.init_app(app)`:
```python
    pagedown.init_app(app)
    limiter.init_app(app)
```

### B.5. File mới `app/storage.py`

```python
import uuid
from flask import current_app
from minio import Minio


def get_minio_client():
    return Minio(
        current_app.config['MINIO_ENDPOINT'],
        access_key=current_app.config['MINIO_ACCESS_KEY'],
        secret_key=current_app.config['MINIO_SECRET_KEY'],
        secure=current_app.config['MINIO_SECURE']
    )


def upload_avatar(file_storage, user_id):
    client = get_minio_client()
    bucket = current_app.config['MINIO_BUCKET']
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    object_name = 'avatars/{}/{}.{}'.format(user_id, uuid.uuid4().hex, ext)

    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)

    client.put_object(bucket, object_name, file_storage.stream, size,
                       content_type=file_storage.mimetype)

    scheme = 'https' if current_app.config['MINIO_SECURE'] else 'http'
    return '{}://{}/{}/{}'.format(
        scheme, current_app.config['MINIO_ENDPOINT'], bucket, object_name)
```

### B.6. `app/models.py` — thêm cột `avatar_url`

Thêm cột (gần `last_seen`):
```python
    avatar_url = db.Column(db.String(255))
```

Sửa hàm `gravatar()` — ưu tiên avatar upload nếu có:
```python
    def gravatar(self, size=100, default='identicon', rating='g'):
        if self.avatar_url:
            return self.avatar_url
        url = 'https://secure.gravatar.com/avatar'
        ...  # phần còn lại giữ nguyên
```

### B.7. `app/main/views.py` — route upload avatar

Thêm import đầu file:
```python
from ..storage import upload_avatar
```

Thêm route (đặt gần route `user`):
```python
@main.route('/upload-avatar', methods=['POST'])
@login_required
def upload_avatar_route():
    file = request.files.get('avatar')
    allowed_ext = {'png', 'jpg', 'jpeg', 'gif'}
    if not file or '.' not in file.filename or \
            file.filename.rsplit('.', 1)[-1].lower() not in allowed_ext:
        flash('File không hợp lệ (chỉ nhận png/jpg/jpeg/gif).')
        return redirect(url_for('main.user', username=current_user.username))

    url = upload_avatar(file, current_user.id)
    current_user.avatar_url = url
    db.session.add(current_user)
    db.session.commit()
    flash('Cập nhật avatar thành công.')
    return redirect(url_for('main.user', username=current_user.username))
```

### B.8. `app/templates/user.html` — thêm form upload

Chỉ hiện nếu đang xem đúng profile của mình:
```html
{% if user == current_user %}
<form method="POST" action="{{ url_for('main.upload_avatar_route') }}" enctype="multipart/form-data">
    <input type="file" name="avatar" accept="image/*">
    <button type="submit">Đổi avatar</button>
</form>
{% endif %}
```

### B.9. `app/auth/views.py` — gắn rate-limit chống brute-force login

Thêm import:
```python
from .. import limiter
```

Gắn decorator lên route `login`:
```python
@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
```

Gắn decorator lên route `register`:
```python
@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
```

Vượt giới hạn sẽ tự trả `429 Too Many Requests`, counter lưu trong Redis nên
dùng chung được giữa web1 và web2.

---

## Phần C — Migration DB cho cột `avatar_url`

> **Sự cố gặp phải:** `alembic.util.exc.CommandError: Can't locate revision
> identified by 'bb77a70811e3'` — do bảng `alembic_version` trong DB đang trỏ
> tới 1 revision không tồn tại trong `migrations/versions/` của code hiện tại
> (lệch lịch sử migration). `flask db stamp head` cũng fail vì lệnh này vẫn cần
> đọc revision hiện tại trong DB trước.

### C.1. Xác định revision "head" thật của code

Truy vết chuỗi `down_revision` trong `migrations/versions/*.py`, kết quả:
```
38c4e85512a9 → 456a945560f6 → 190163627111 → 56ed7d33de8d → d66f086b258
→ 198b0eebcf9 → 1b966e7f4b9e → 288cd3dc5a8 → 2356a38169ea → 51f5ccfba190
```
**Head = `51f5ccfba190`**

### C.2. Update thẳng bảng `alembic_version` trong DB (bỏ qua Alembic)

```bash
sudo docker exec -it mariadb mariadb -u root -p flasky_db -e \
"UPDATE alembic_version SET version_num='51f5ccfba190';"

sudo docker exec -it mariadb mariadb -u root -p flasky_db -e \
"SELECT * FROM alembic_version;"
```
Kết quả phải ra đúng `51f5ccfba190`.

### C.3. Generate migration cho cột avatar_url

```bash
sudo docker exec -it flasky-master-flasky-1 /home/flasky/venv/bin/flask db migrate -m "add avatar_url"
```

> Lưu ý: binary `flask` nằm trong venv (`/home/flasky/venv/bin/flask`), không có
> sẵn trong PATH của `docker exec` vì venv chỉ được activate lúc `boot.sh` chạy
> lúc container start, không áp dụng cho session `exec` mới.

Kiểm tra file migration mới sinh ra trước khi upgrade:
```bash
sudo docker exec -it flasky-master-flasky-1 ls -la migrations/versions/
sudo docker exec -it flasky-master-flasky-1 cat migrations/versions/<tên_file_mới>.py
```
Đảm bảo có dòng:
```python
op.add_column('users', sa.Column('avatar_url', sa.String(length=255), nullable=True))
```

### C.4. Apply migration thật

```bash
sudo docker exec -it flasky-master-flasky-1 /home/flasky/venv/bin/flask db upgrade
```

### C.5. Xác nhận

```bash
sudo docker exec -it mariadb mariadb -u root -p flasky_db -e "DESCRIBE users;"
```
Phải thấy thêm dòng `avatar_url | varchar(255)`.

> Chỉ cần chạy migration 1 lần trên 1 container (vd web1) vì cả web1/web2 dùng
> chung 1 DB MariaDB. Không cần chạy lại trên web2.

### C.6. Restart container để load code mới

```bash
sudo docker restart flasky-master-flasky-1
sudo docker restart <tên_container_web2>
```

---

## Phần D — Rebuild & deploy sau khi sửa xong toàn bộ code

```bash
docker-compose build
docker-compose up -d
```

Kiểm tra log nếu có lỗi:
```bash
sudo docker logs flasky-master-flasky-1 --since 5m
```

