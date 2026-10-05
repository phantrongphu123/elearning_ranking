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
def root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
        "status": "running"
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": APP_NAME}

# Phục vụ thư mục Frontend (Phải đặt ở cuối cùng để không đè lên các API routes)
frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
