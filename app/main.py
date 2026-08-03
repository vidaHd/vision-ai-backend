from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.menu import router as menu_router
from app.api.routes.ocr import router as ocr_router
from app.api.routes.restaurants import router as restaurants_router
from app.api.routes.upload import router as upload_router
from app.core.config import APP_NAME, APP_VERSION, DEBUG, UPLOAD_DIR

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    debug=DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:8081",
        "http://localhost:8081",
    ],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(ocr_router)
app.include_router(menu_router)
app.include_router(restaurants_router)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
