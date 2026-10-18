# HƯỚNG DẪN CHUYỂN DATABASE SANG GOOGLE SHEET & DEPLOY LÊN VERCEL

Tài liệu này tổng hợp chi tiết toàn bộ các bước cần thực hiện để chuyển đổi hệ thống **Hoàng Cung Học Đường** từ file Excel local sang **Google Sheet** và triển khai (deploy) hoàn chỉnh lên nền tảng **Vercel**.

---

## 📌 TỔNG QUAN KIẾN TRÚC VERCEL + GOOGLE SHEET

- **Tại sao Vercel cần Google Sheet?**
  Vercel hoạt động theo mô hình **Serverless (không có ổ cứng vĩnh viễn)**. Mỗi khi có request, serverless function được bật lên và tắt đi ngay sau đó. Nếu dùng file Excel cục bộ (`school_system.xlsx`), dữ liệu ghi vào sẽ bị mất sạch khi function tắt. Vì vậy, **Google Sheet đóng vai trò là Database đám mây (Cloud Database) vĩnh viễn và miễn phí**, cực kỳ phù hợp với Vercel.
- **Frontend:** Toàn bộ thư mục `frontend/` (HTML/CSS/JS) sẽ được Vercel phục vụ qua mạng CDN toàn cầu tốc độ cao.
- **Backend:** FastAPI được chạy dưới dạng Vercel Python Serverless Function xử lý mọi request tại `/api/*`.

---

## 📋 CHECKLIST CÁC BƯỚC CẦN LÀM

### BƯỚC 1: Khởi tạo 14 Sheets và Dữ liệu mẫu lên Google Sheet
Google Sheet `Linh_Chi_DB` của bạn (ID: `1Abfw5CMLtseRVwoXOgTjnkEpjGkzHhkg5nD4PcBOExk`) hiện đang trống. Cần tạo 14 tab tương ứng với các bảng:
1. `Users` (Tài khoản admin, giáo viên, học sinh)
2. `HocSinh` (Thông tin học sinh, điểm, cấp bậc)
3. `LopHoc` (Danh sách lớp học)
4. `BaiTap` (Tấu chương / Bài tập)
5. `CauHoi` (Ngân hàng câu hỏi trắc nghiệm)
6. `BaiNop` (Bài nộp của học sinh)
7. `ChiTietBaiNop` (Chi tiết câu trả lời)
8. `Diem` (Lịch sử cộng/trừ điểm)
9. `LichSuNopBai`
10. `RankHistory` (Lịch sử thăng/giáng chức)
11. `DiemDanh` (Chuyên cần)
12. `ThanhTich` (Huy hiệu/danh hiệu)
13. `ThongBao` (Thông báo triều đình)
14. `RankConfig` (Cấu hình phẩm hàm hoàng cung)

> 💡 *Dữ liệu hiện tại chỉ là mock data, nên chỉ cần chạy script khởi tạo bảng và chèn các tài khoản mẫu (admin/teacher/student) để đăng nhập thử nghiệm.*

---

### BƯỚC 2: Cập nhật Backend để kết nối Google Sheet

1. **Thêm thư viện vào `backend/requirements.txt`:**
   ```text
   fastapi>=0.100.0
   uvicorn[standard]>=0.23.0
   pydantic>=2.0.0
   pandas>=2.0.0
   openpyxl>=3.1.0
   python-multipart>=0.0.6
   python-jose[cryptography]>=3.3.0
   passlib[bcrypt]>=1.7.4
   gspread>=6.0.0
   google-auth>=2.0.0
   ```

2. **Cập nhật `backend/app/core/config.py`:**
   - Cấu hình lấy `GOOGLE_SHEET_ID` từ biến môi trường (fallback về ID hiện tại của bạn).
   - Cấu hình xác thực Service Account linh hoạt:
     - Chạy Local: đọc từ file `backend/service_account.json`.
     - Chạy trên Vercel: đọc chuỗi JSON từ biến môi trường `GOOGLE_SERVICE_ACCOUNT_JSON` (để không cần đưa file private key lên Git).

3. **Cập nhật `backend/app/services/excel_service.py`:**
   - Giữ nguyên các hàm: `read_sheet`, `insert_row`, `update_row`, `delete_row`, `get_next_id`, `find_one`.
   - Thay thế ruột bên trong bằng `gspread`.
   - **Tích hợp bộ nhớ đệm (In-memory TTL Cache ~30s-60s):** Tránh việc mỗi request lại gọi tới Google API gây chậm trang và vượt quá giới hạn quota (60 requests/phút).
   - Thao tác ghi (`insert_row`) sử dụng `append_row` thay vì ghi đè cả sheet.

---

### BƯỚC 3: Cấu hình Vercel (`vercel.json` & Entry Point)

Tệp `vercel.json` ở thư mục gốc của dự án đã được tối ưu hoàn chỉnh cho Vercel Serverless:
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "functions": {
    "api/index.py": {
      "includeFiles": "backend/**"
    }
  },
  "rewrites": [
    {
      "source": "/api",
      "destination": "/api/index.py"
    },
    {
      "source": "/api/(.*)",
      "destination": "/api/index.py"
    },
    {
      "source": "/docs",
      "destination": "/api/index.py"
    },
    {
      "source": "/redoc",
      "destination": "/api/index.py"
    },
    {
      "source": "/openapi.json",
      "destination": "/api/index.py"
    },
    {
      "source": "/",
      "destination": "/frontend/index.html"
    },
    {
      "source": "/admin",
      "destination": "/frontend/admin/index.html"
    },
    {
      "source": "/admin/",
      "destination": "/frontend/admin/index.html"
    },
    {
      "source": "/teacher",
      "destination": "/frontend/teacher/index.html"
    },
    {
      "source": "/teacher/",
      "destination": "/frontend/teacher/index.html"
    },
    {
      "source": "/student",
      "destination": "/frontend/student/index.html"
    },
    {
      "source": "/student/",
      "destination": "/frontend/student/index.html"
    },
    {
      "source": "/(.*)",
      "destination": "/frontend/$1"
    }
  ]
}
```

Cầu nối `api/index.py` ở thư mục gốc tự động nhận diện module `backend`:
```python
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(root_dir, "backend")
cwd = os.getcwd()
backend_cwd = os.path.join(cwd, "backend")

for path in [backend_dir, backend_cwd, root_dir, cwd, current_dir]:
    if path not in sys.path and os.path.exists(path):
        sys.path.insert(0, path)

try:
    from app.main import app
except ImportError:
    try:
        from backend.app.main import app
    except ImportError as e:
        raise ImportError(f"Không thể import app: {e}. sys.path={sys.path}")
```

---

### BƯỚC 4: Sửa đường dẫn API ở Frontend (`frontend/js/api.js`)

Hệ thống đã được thiết lập tự động:
- Khi chạy cục bộ (`file://` hoặc `localhost`): Tự động kết nối tới `http://localhost:8000/api`.
- Khi chạy trên Vercel: Tự động dùng relative path `/api` (không cần sửa đổi).
- Bắt lỗi thông minh: Nếu Vercel trả về HTML lỗi 404 hoặc 500, hệ thống sẽ hiển thị thông báo tiếng Việt dễ hiểu thay vì lỗi cú pháp `Unexpected token 'T'`.

---

### BƯỚC 5: Bảo mật Git (`.gitignore`)

File `.gitignore` ngăn không đưa file khóa bí mật lên GitHub:
```gitignore
.venv/
__pycache__/
*.pyc
backend/service_account.json
database/backup/
.env
```

---

### BƯỚC 6: Thao tác Deploy trên Vercel Dashboard

1. **Đẩy code mới lên GitHub:**
   ```bash
   git add .
   git commit -m "fix: hoan thien cau hinh deploy Vercel va xu ly loi dinh tuyen"
   git push origin main
   ```
2. **Cài đặt Biến Môi Trường (Environment Variables) trên Vercel:**
   Truy cập vào dự án trên **Vercel** ➔ Vào **Settings** ➔ **Environment Variables**, thêm 3 biến sau:
   - `GOOGLE_SHEET_ID`:
     `1Abfw5CMLtseRVwoXOgTjnkEpjGkzHhkg5nD4PcBOExk`
   - `GOOGLE_SERVICE_ACCOUNT_JSON`:
     *(Mở file `backend/service_account.json`, copy toàn bộ nội dung dán vào ô Value)*
     > 💡 *Hệ thống đã hỗ trợ tự động xử lý ký tự xuống dòng `\n` và hỗ trợ cả chuỗi mã hóa Base64.*
   - `SECRET_KEY`:
     `hoangcung_secret_key_2026_thpt_linh_chi`
3. **Redeploy lại trên Vercel:**
   - Vào tab **Deployments** ➔ Bấm dấu 3 chấm `...` ở commit mới nhất ➔ Chọn **Redeploy**.
   - Sau khi deploy xong, truy cập link Vercel và đăng nhập thử nghiệm!

