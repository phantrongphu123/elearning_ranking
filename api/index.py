import sys
import os

# Thêm thư mục backend vào Python path để Vercel tìm thấy module `app`
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
