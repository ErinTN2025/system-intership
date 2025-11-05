# DNS
### 1. Khái niệm
DNS (Domain Name System) là hệ thống dịch tên miền (human-readable) như example.com sang địa chỉ IP (ví dụ 93.184.216.34) mà máy tính và router dùng để định tuyến.

Nó hoạt động như “sổ địa chỉ” phân tán toàn cầu: bạn hỏi tên, DNS trả về địa chỉ tương ứng (cũng trả về mail servers, bản ghi xác thực, v.v.)
### 4. Các bản ghi (record) quan trọng trong DNS
- `A`: IPv4
- `AAAA`: IPv6
- `CNAME`: canonical name (alias) — trỏ một tên tới tên khác (không dùng cùng lúc với A/AAAA trên cùng tên).
- `MX`: mail exchange (máy chủ mail)
- `NS`: Name server (delegation)
- `SOA`: Start of Authority (metadata zone: primary server, serial, refresh/retry/expire, TTL).
- `TXT`: văn bản (dùng cho SPF, DKIM, verifications)
- `SRV`: dịch vụ (service discovery, nội dung: priority, weight, port, target). 
- `PTR`: reverse lookup( IP -> tên)
- `DS, DNSKEY, RRSIG`: liên quan DNSSEC( chữ ký và khóa)