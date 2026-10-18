from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import APP_NAME, APP_VERSION, CORS_ORIGINS
from .api import auth, students, teachers, classes, assignments, submissions, scores, attendance, leaderboard, dashboard
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Hệ thống quản lý điểm học sinh phong cách Hoàng Cung",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import urllib.parse


class PrefixMiddleware:
    """Tự động chuẩn hóa đường dẫn để hoạt động hoàn hảo cả trên local và Vercel serverless."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            query_string = scope.get("query_string", b"").decode("utf-8")

            # 1. Trích xuất __path__ được Vercel rewrite chuyển tiếp qua query param
            if "__path__=" in query_string:
                qs_parts = urllib.parse.parse_qs(query_string, keep_blank_values=True)
                if "__path__" in qs_parts and qs_parts["__path__"]:
                    extracted = qs_parts.pop("__path__")[0]
                    # Loại bỏ __path__ khỏi query string để không làm bẩn endpoint của route
                    new_qs = urllib.parse.urlencode(qs_parts, doseq=True)
                    scope["query_string"] = new_qs.encode("utf-8")
                    path = f"/{extracted.lstrip('/')}"

            # 2. Nếu path bị Vercel đặt thành /api/index.py hoặc /api, đọc header định tuyến
            if path in ("/api/index.py", "/api/index", "/api/index.py/", "/api", "/api/"):
                headers = dict(scope.get("headers", []))
                # Vercel x-now-route-matches có dạng: 1=auth/login
                route_matches = headers.get(b"x-now-route-matches", b"").decode("utf-8", errors="ignore")
                if "1=" in route_matches:
                    m_parts = urllib.parse.parse_qs(route_matches)
                    if "1" in m_parts and m_parts["1"]:
                        path = f"/{m_parts['1'][0].lstrip('/')}"
                else:
                    matched = headers.get(b"x-matched-path", b"").decode("utf-8", errors="ignore")
                    if matched and matched not in ("/api/index.py", "/api/index", "/api", "/api/", "/"):
                        path = matched

            # 3. Xóa tiền tố /api/index.py nếu vẫn còn dính
            if path.startswith("/api/index.py"):
                path = path[len("/api/index.py"):]
            elif path.startswith("/api/index"):
                path = path[len("/api/index"):]

            if not path:
                path = "/"
            elif not path.startswith("/"):
                path = "/" + path

            # 4. Chuẩn hóa: nếu request thiếu /api mà thuộc các endpoint của router thì tự thêm /api
            prefixes = (
                "/auth", "/students", "/teachers", "/classes", "/assignments",
                "/submissions", "/scores", "/attendance", "/leaderboard", "/dashboard", "/health"
            )
            if any(path.startswith(p) for p in prefixes):
                path = f"/api{path}"

            scope["path"] = path
            scope["raw_path"] = path.encode("utf-8")

        await self.app(scope, receive, send)


app.add_middleware(PrefixMiddleware)

# Include all routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(classes.router)
app.include_router(assignments.router)
app.include_router(submissions.router)
app.include_router(scores.router)
app.include_router(attendance.router)
app.include_router(leaderboard.router)
app.include_router(dashboard.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"Lỗi hệ thống: {str(exc)}"}
    )


@app.get("/")
@app.get("/api")
def root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": APP_NAME}

# Phục vụ thư mục Frontend (Phải đặt ở cuối cùng để không đè lên các API routes)
frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
