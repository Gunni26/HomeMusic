from fastapi import APIRouter
from fastapi.responses import FileResponse
import sqlite3
import os

from app.database import connect

router = APIRouter()


@router.get("/songs")
def get_songs():

    conn = connect()
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            artist,
            album,
            title,
            year,
            genre,
            duration,
            filepath
        FROM songs
        ORDER BY artist, album, track, title
        LIMIT 100
    """)

    songs = [dict(row) for row in cur.fetchall()]

    conn.close()

    return songs


@router.get("/search")
def search(q: str, mode: str = "all"):

    conn = connect()
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    search_text = f"%{q}%"

    if mode == "artist":
        where = "artist LIKE ?"

    elif mode == "album":
        where = "album LIKE ?"

    elif mode == "title":
        where = "title LIKE ?"

    elif mode == "year":
        where = "year LIKE ?"

    else:
        where = """
            artist LIKE ?
            OR album LIKE ?
            OR title LIKE ?
            OR year LIKE ?
        """

    sql = f"""
        SELECT
            id,
            artist,
            album,
            title,
            year,
            duration,
            filepath
        FROM songs
        WHERE {where}
        ORDER BY artist, album, track, title
        LIMIT 2000
    """

    if mode == "all":
        params = (
            search_text,
            search_text,
            search_text,
            search_text,
        )
    else:
        params = (search_text,)

    cur.execute(sql, params)

    result = [dict(row) for row in cur.fetchall()]

    conn.close()

    return result


@router.get("/artists")
def get_artists():

    conn = connect()
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT artist
        FROM songs
        WHERE artist <> ''
        ORDER BY artist
    """)

    artists = [row["artist"] for row in cur.fetchall()]

    conn.close()

    return artists


@router.get("/albums")
def get_albums():

    conn = connect()
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT album
        FROM songs
        WHERE album <> ''
        ORDER BY album
    """)

    albums = [row["album"] for row in cur.fetchall()]

    conn.close()

    return albums


@router.get("/play")
def play(path: str):

    if not os.path.exists(path):
        return {"error": "Datei nicht gefunden"}

    return FileResponse(path)
