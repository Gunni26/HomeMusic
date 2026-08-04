from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import router

app = FastAPI(
    title="HomeMusic",
    version="0.1.0"
)

app.include_router(router)

# Statische Dateien
app.mount("/web", StaticFiles(directory="web"), name="web")


@app.get("/")
def index():
    return FileResponse("web/index.html")
