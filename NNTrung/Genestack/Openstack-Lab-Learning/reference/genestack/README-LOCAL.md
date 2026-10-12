# Các nguồn Genestack được giữ local

Đây là tập source chọn lọc để học/đối chiếu Octavia, RabbitMQ, MariaDB, Gateway. Không phải checkout Genestack đầy đủ. Installer có thể cần framework/config ở /etc/genestack và /opt/genestack chưa dựng; không chạy nguyên script lên lab chỉ vì file tồn tại.

Đọc ../../docs/08-Octavia-Genestack.md để biết default Amphora, OVN sidecar/post-rendering, secret/DB/broker assumptions và phần lab cần điều chỉnh. Source gốc dùng MkDocs admonitions/includes; các block --8<-- là include directive, không phải shell command. Những file đã trích có fingerprint trong ../GENESTACK-SOURCE-MANIFEST.csv.
