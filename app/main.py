from fastapi import FastAPI

from app.config import settings
from app.routers import bonds

app = FastAPI(title=settings.app_name)

app.include_router(bonds.router)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {"app": settings.app_name}
