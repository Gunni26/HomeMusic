from fastapi import FastAPI
from fastapi.responses import FileResponse
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


@app.get("/receiver")
def receiver():
    return FileResponse("web/receiver.html")

@app.get("/zwei")
def player_zwei():
    return FileResponse("web/zwei.html")

@app.get("/player01")
def player01():
    return FileResponse("web/player01.html")

@app.get("/Partymodus")
def partymodus():
    return FileResponse("web/partymodus.html")

# ============================================================
# Party Player 02-06
# ============================================================

@app.get("/player02")
def player02():
    return FileResponse("web/player02.html")

@app.get("/player03")
def player03():
    return FileResponse("web/player03.html")

@app.get("/player04")
def player04():
    return FileResponse("web/player04.html")

@app.get("/player05")
def player05():
    return FileResponse("web/player05.html")

@app.get("/player06")
def player06():
    return FileResponse("web/player06.html")

