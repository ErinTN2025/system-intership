# Tìm hiểu về Docker
Khi nhắc đến "Docker", chúng ta cần phân biệt rõ ba thực thể: **Docker, Inc.** (Công ty), **Docker Engine** (Công nghệ cốt lõi), và **Moby Project** (Dự án mã nguồn mở).

## Docker, Inc. - Công ty đứng sau cuộc cách mạng
- Tiền thân: Thành lập bởi Solomon Hykes với tên gọi dotCloud(một nhà cung cấp PaaS).
- Trọng tâm hiện tại: Docker, Inc. không còn tập trung vào việc duy trì toàn bộ hạ tầng container mã nguồn thấp mà chuyển sang cung cấp các công cụ hỗ trợ quy trình phát triển (Developer Experience - DX) như:
  - **Docker Desktop**: Công cụ GUI quản lý docker trên Windows/MAC/Linux ( lưu ý: có chính sách bản quyền cho doanh nghiệp lớn).
  - **Docker Hub**: Registry lưu trữ image lớn nhất thế giới.
  - **Docker Scout**: Công cụ phân tích bảo mật và chuỗi cung ứng phần mềm.
## 1. Khái niệm
**Docker** là nền tảng containerization mã nguồn mở, cho phép đóng gói ứng dụng cùng toàn bộ phụ thuộc (thư viện, runtime, cấu hình) vào một đơn vị chuẩn hóa gọi là container. Container chạy độc lập, nhẹ và nhất quán trên mọi môi trường (dev, test, production).

**Docker** giúp nhà phát triển:
  - Đóng gói toàn bộ ứng dụng cùng thư viện, công cụ, cấu hình và một **Docker Image** nhỏ gọn.
  - Chạy ứng dụng đó ở bất kỳ đâu mà không lo khác biệt môi trường (máy thật, server, cloud, v.v.).

## 2. Kiến trúc Công nghệ Docker (The Docker Stack)
Công nghệ Docker hiện nay không còn là một khối duy nhất (monolithic) mà được chia thành nhiều thành phần chuyên biệt theo tiêu chuẩn mở.

### 2.1 Container Runtime (Môi trường thực thi)
Đây là tầng trực tiếp quản lý vòng đời container. Docker sử dụng kiến trúc phân tầng: 
- **Low-level Runtime (runc)**: Là hiện thực hóa tiêu chuẩn OCI. Nhiệm vụ duy nhất của nó là tương tác với kernel Linux( Namespaces, Cgroups) để tạo ra container. Nó chạy xong rồi thoát, không duy trì trạng thái.
- **High-level Runtime (containerd)**: Ban đầu 