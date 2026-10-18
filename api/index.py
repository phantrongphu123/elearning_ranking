import sys
import os

# Thêm tất cả đường dẫn tiềm năng vào sys.path để Vercel serverless function tìm thấy backend
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
