Công thức cần nhớ:
- Số subnet có thể có: 2<sup>số bit mượn</sup>
- Số host trên mỗi subnet: 2<sup>số bit host còn lại</sup> - 2
- Bước nhảy: 2<sup>số bit host trong octet bị chia cắt</sup>
- Địa chỉ mạng: Bội số của bước nhảy.
- Host đầu: Network + 1
- Broadcast: Next Network - 1
- Host cuối: Broadcast -1
- Subnet zero là khi tất cả các bit mượn(Subnet bits) = 0
- Subnet cuối cùng là khi tất cả các bit mượn (Subnet bits) = 1
- Khi subnet bị chia cắt, octet bị chia cắt là octet chứa phần ranh giới giữa phần mạng (Network) và phần host trong subnet mask.
---
## 4.6.1
**a\)** 192.168.2.0/24 mượn 5 bit.
- Số subnet có thể có = 2<sup>5</sup> 
- Số host trên mỗi subnet: 2<sup>8-5</sup>
- Địa chỉ mạng có octet thứ 4 là bội số của 8(octet này bị mượn 5 bit)
  - 192.168.2.0 : địa chỉ mạng
  - 192.168.2.1 : địa chỉ host đầu

    .......

  - 192.168.2.6 : địa chỉ host cuối
  - 192.168.2.7 : địa chỉ broadcast
  

  - 192.168.2.8 : địa chỉ mạng
  - 192.168.2.9 : địa chỉ host đầu

    .......

  - 192.168.2.14 : địa chỉ host cuối
  - 192.168.2.15 : địa chỉ broadcast
    
    **................................**

  - 192.168.2.248 : địa chỉ mạng
  - 192.168.2.249 : địa chỉ host đầu

    .......

  - 192.168.2.254 : địa chỉ host cuối
  - 192.168.2.255 : địa chỉ broadcast

**b\)**192.168.12.0/24 mượn 3 bit
- Số subnet có thể có: 2<sup>3</sup>
- Số host trên mỗi subnet: 2<sup>8-3</sup>
- Địa chỉ mạng có octet thứ 4 là bội số của 32(octet này bị mượn 3 bit)
  - 192.168.2.0 : địa chỉ mạng
  - 192.168.2.1 : địa chỉ host đầu

    .......

  - 192.168.2.30 : địa chỉ host cuối
  - 192.168.2.31 : địa chỉ broadcast
  

  - 192.168.2.32 : địa chỉ mạng
  - 192.168.2.33 : địa chỉ host đầu

    .......

  - 192.168.2.62 : địa chỉ host cuối
  - 192.168.2.63 : địa chỉ broadcast
    
    **................................**

  - 192.168.2.224 : địa chỉ mạng
  - 192.168.2.225 : địa chỉ host đầu

    .......

  - 192.168.2.254 : địa chỉ host cuối
  - 192.168.2.255 : địa chỉ broadcast

**c\)**172.16.2.0/24 mượn 2 bit
- Số subnet có thể có: 2<sup>2</sup> = 4
- Số host trên mỗi subnet: 2<sup>8-2</sup>
- Địa chỉ mạng có octet thứ 4 là bội số của 64(octet này bị mượn 2 bit)
  - 172.16.2.0 : địa chỉ mạng
  - 172.16.2.1 : địa chỉ host đầu

    .......

  - 172.16.2.62 : địa chỉ host cuối
  - 172.16.2.63 : địa chỉ broadcast
  

  - 172.16.2.64 : địa chỉ mạng
  - 172.16.2.65 : địa chỉ host đầu

    .......

  - 172.16.2.126 : địa chỉ host cuối
  - 172.16.2.127 : địa chỉ broadcast
    
    **................................**

  - 172.16.2.192 : địa chỉ mạng
  - 172.16.2.193 : địa chỉ host đầu

    .......

  - 172.16.2.254 : địa chỉ host cuối
  - 172.16.2.255 : địa chỉ broadcast

**d\)**172.16.0.0/16 mượn 3 bit
- Số subnet có thể có: 2<sup>3</sup> = 8
- Số host trên mỗi subnet: 2<sup>13</sup>
- Địa chỉ mạng có octet thứ 3 là bội số của 32(octet này bị mượn 3 bit)
  - 192.168.2.0 : địa chỉ mạng
  - 192.168.2.1 : địa chỉ host đầu

    .......

  - 192.168.2.62 : địa chỉ host cuối
  - 192.168.2.63 : địa chỉ broadcast
  

  - 192.168.2.64 : địa chỉ mạng
  - 192.168.2.65 : địa chỉ host đầu

    .......

  - 192.168.2.126 : địa chỉ host cuối
  - 192.168.2.127 : địa chỉ broadcast
    
    **................................**

  - 192.168.2.192 : địa chỉ mạng
  - 192.168.2.193 : địa chỉ host đầu

    .......

  - 192.168.2.254 : địa chỉ host cuối
  - 192.168.2.255 : địa chỉ broadcast