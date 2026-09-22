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

    if mode == "year":
        order_by = "CAST(year AS INTEGER), artist, album, track, title"
    else:
        order_by = "artist, album, track, title"

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
        ORDER BY {order_by}
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
@router.get("/import")
def import_music():
    import subprocess

    result = subprocess.run(
        ["/home/Gunni/HomeMusic/venv/bin/python", "app/import_library.py"],
        cwd="/home/Gunni/HomeMusic",
        capture_output=True,
        text=True
    )

    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr
    }

# ============================================================
# HomeMusic Netzwerk-Stream
# ============================================================

STREAM_STATE_FILE = "/home/Gunni/HomeMusic/app/current_stream.txt"


def get_current_stream_path():
    try:
        with open(STREAM_STATE_FILE, "r", encoding="utf-8") as f:
            path = f.read().strip()
            return path if path else None
    except FileNotFoundError:
        return None


STREAM_INFO_FILE = "/home/Gunni/HomeMusic/app/current_stream_info.txt"


def get_current_stream_info():
    try:
        with open(STREAM_INFO_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        return {
            "path": lines[0] if len(lines) > 0 else "",
            "artist": lines[1] if len(lines) > 1 else "",
            "title": lines[2] if len(lines) > 2 else ""
        }

    except FileNotFoundError:
        return {
            "path": "",
            "artist": "",
            "title": ""
        }


@router.get("/set_current")
def set_current(
    path: str,
    artist: str = "",
    title: str = ""
):

    if not os.path.isfile(path):
        return {
            "success": False,
            "error": "Datei nicht gefunden"
        }

    with open(STREAM_STATE_FILE, "w", encoding="utf-8") as f:
        f.write(path)

    with open(STREAM_INFO_FILE, "w", encoding="utf-8") as f:
        f.write(path + "\n")
        f.write(artist + "\n")
        f.write(title + "\n")

    return {
        "success": True,
        "path": path,
        "artist": artist,
        "title": title
    }


VOLUME_STATE_FILE = "/home/Gunni/HomeMusic/app/receiver_volume.txt"


def get_receiver_volume():
    try:
        with open(VOLUME_STATE_FILE, "r", encoding="utf-8") as f:
            value = float(f.read().strip())
            return max(0.0, min(1.0, value))
    except (FileNotFoundError, ValueError):
        return 1.0


@router.get("/set_volume")
def set_volume(value: float):

    value = max(0.0, min(1.0, value))

    with open(VOLUME_STATE_FILE, "w", encoding="utf-8") as f:
        f.write(str(value))

    return {
        "success": True,
        "volume": value
    }


@router.get("/volume")
def volume():
    return {
        "success": True,
        "volume": get_receiver_volume()
    }


@router.get("/current")
def current():

    info = get_current_stream_info()

    if not info["path"]:
        return {
            "success": False,
            "path": None,
            "artist": "",
            "title": ""
        }

    if not os.path.isfile(info["path"]):
        return {
            "success": False,
            "path": None,
            "artist": "",
            "title": ""
        }

    return {
        "success": True,
        "path": info["path"],
        "artist": info["artist"],
        "title": info["title"]
    }


@router.get("/stream")
def stream():

    current_stream_path = get_current_stream_path()

    if not current_stream_path:
        return {
            "success": False,
            "error": "Kein Titel ausgewählt"
        }

    if not os.path.isfile(current_stream_path):
        return {
            "success": False,
            "error": "Aktuelle Musikdatei nicht gefunden"
        }

    return FileResponse(current_stream_path)


# ============================================================
# HomeMusic – Playlists
# ============================================================

@router.get("/playlists")
def get_playlists():
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, created
        FROM playlists
        ORDER BY name
    """)

    playlists = [dict(row) for row in cur.fetchall()]
    conn.close()

    return playlists


@router.post("/playlists")
def create_playlist(name: str):
    name = name.strip()

    if not name:
        return {
            "success": False,
            "error": "Playlistname fehlt"
        }

    conn = connect()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO playlists (name) VALUES (?)",
            (name,)
        )
        conn.commit()

        playlist_id = cur.lastrowid

    except sqlite3.IntegrityError:
        conn.close()
        return {
            "success": False,
            "error": "Playlist existiert bereits"
        }

    conn.close()

    return {
        "success": True,
        "id": playlist_id,
        "name": name
    }


@router.delete("/playlists/{playlist_id}")
def delete_playlist(playlist_id: int):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM playlist_songs WHERE playlist_id = ?",
        (playlist_id,)
    )

    cur.execute(
        "DELETE FROM playlists WHERE id = ?",
        (playlist_id,)
    )

    deleted = cur.rowcount

    conn.commit()
    conn.close()

    return {
        "success": deleted > 0
    }


@router.get("/playlists/{playlist_id}/songs")
def get_playlist_songs(playlist_id: int):
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            songs.id,
            songs.artist,
            songs.album,
            songs.title,
            songs.year,
            songs.genre,
            songs.duration,
            songs.filepath,
            playlist_songs.position
        FROM playlist_songs
        JOIN songs
            ON songs.id = playlist_songs.song_id
        WHERE playlist_songs.playlist_id = ?
        ORDER BY playlist_songs.position, songs.artist, songs.album, songs.title
    """, (playlist_id,))

    songs = [dict(row) for row in cur.fetchall()]
    conn.close()

    return songs


@router.post("/playlists/{playlist_id}/songs/{song_id}")
def add_song_to_playlist(playlist_id: int, song_id: int):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM playlists WHERE id = ?",
        (playlist_id,)
    )

    if cur.fetchone() is None:
        conn.close()
        return {
            "success": False,
            "error": "Playlist nicht gefunden"
        }

    cur.execute(
        "SELECT id FROM songs WHERE id = ?",
        (song_id,)
    )

    if cur.fetchone() is None:
        conn.close()
        return {
            "success": False,
            "error": "Titel nicht gefunden"
        }

    cur.execute("""
        SELECT COALESCE(MAX(position), -1) + 1
        FROM playlist_songs
        WHERE playlist_id = ?
    """, (playlist_id,))

    position = cur.fetchone()[0]

    try:
        cur.execute("""
            INSERT INTO playlist_songs
            (playlist_id, song_id, position)
            VALUES (?, ?, ?)
        """, (playlist_id, song_id, position))

    except sqlite3.IntegrityError:
        conn.close()
        return {
            "success": False,
            "error": "Titel ist bereits in der Playlist"
        }

    conn.commit()
    conn.close()

    return {
        "success": True,
        "position": position
    }


@router.delete("/playlists/{playlist_id}/songs/{song_id}")
def remove_song_from_playlist(playlist_id: int, song_id: int):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM playlist_songs
        WHERE playlist_id = ?
        AND song_id = ?
    """, (playlist_id, song_id))

    deleted = cur.rowcount

    conn.commit()
    conn.close()

    return {
        "success": deleted > 0
    }

# ============================================================
# Receiver-Warteschlange
# ============================================================

RECEIVER_QUEUE_FILE = "/home/Gunni/HomeMusic/app/receiver_queue.json"


def load_receiver_queue():
    import json

    try:
        with open(RECEIVER_QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {
            "songs": [],
            "index": 0
        }


def save_receiver_queue(songs, index=0):
    import json

    with open(RECEIVER_QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "songs": songs,
                "index": index
            },
            f,
            ensure_ascii=False
        )


@router.get("/set_receiver_playlist")
def set_receiver_playlist(playlist_id: int, index: int = 0):
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            songs.id,
            songs.artist,
            songs.title,
            songs.filepath
        FROM playlist_songs
        JOIN songs
            ON songs.id = playlist_songs.song_id
        WHERE playlist_songs.playlist_id = ?
        ORDER BY playlist_songs.position
    """, (playlist_id,))

    songs = [dict(row) for row in cur.fetchall()]
    conn.close()

    if not songs:
        return {
            "success": False,
            "error": "Playlist ist leer"
        }

    index = max(0, min(index, len(songs) - 1))

    save_receiver_queue(songs, index)

    return {
        "success": True,
        "songs": songs,
        "index": index
    }


@router.get("/set_receiver_single")
def set_receiver_single(
    path: str,
    artist: str = "",
    title: str = ""
):
    if not os.path.isfile(path):
        return {
            "success": False,
            "error": "Datei nicht gefunden"
        }

    songs = [
        {
            "id": 0,
            "artist": artist,
            "title": title,
            "filepath": path
        }
    ]

    save_receiver_queue(songs, 0)

    return {
        "success": True,
        "songs": songs,
        "index": 0
    }


@router.get("/receiver_queue")
def receiver_queue():
    queue = load_receiver_queue()

    songs = queue.get("songs", [])
    index = queue.get("index", 0)

    if not songs or index >= len(songs):
        return {
            "success": False,
            "song": None,
            "index": index
        }

    return {
        "success": True,
        "song": songs[index],
        "index": index,
        "count": len(songs)
    }


@router.get("/receiver_stream")
def receiver_stream(path: str = ""):

    if not path:
        queue = load_receiver_queue()

        songs = queue.get("songs", [])
        index = queue.get("index", 0)

        if not songs or index >= len(songs):
            return {
                "success": False,
                "error": "Keine Receiver-Musik"
            }

        path = songs[index].get("filepath")

    if not path or not os.path.isfile(path):
        return {
            "success": False,
            "error": "Receiver-Musikdatei nicht gefunden"
        }

    return FileResponse(path)


@router.get("/receiver_next")
def receiver_next():
    queue = load_receiver_queue()

    songs = queue.get("songs", [])
    index = queue.get("index", 0)

    if not songs:
        return {
            "success": False,
            "song": None
        }

    next_index = index + 1

    if next_index >= len(songs):
        return {
            "success": False,
            "song": None,
            "finished": True
        }

    queue["index"] = next_index

    save_receiver_queue(
        songs,
        next_index
    )

    # Bei einer Party-Warteschlange die aktuelle Wunschposition
    # serverseitig speichern.
    next_song = songs[next_index]
    request_id = next_song.get("request_id")

    if request_id is not None:
        conn = connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT active_playlist_id
            FROM party_settings
            WHERE id = 1
        """)

        party = cur.fetchone()
        conn.close()

        if party and party[0]:
            save_party_resume_position(
                party[0],
                request_id
            )

    return {
        "success": True,
        "song": songs[next_index],
        "index": next_index,
        "count": len(songs)
    }



# ============================================================
# Gemeinsame Party-Liste
# ============================================================

@router.get("/party_add")
def party_add(path: str, artist: str = "", title: str = "", player: str = "player01"):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS party_queue(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT,
            artist TEXT,
            title TEXT,
            player TEXT,
            added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        INSERT INTO party_queue(filepath, artist, title, player)
        VALUES (?, ?, ?, ?)
    """, (path, artist, title, player))

    conn.commit()

    party_id = cur.lastrowid
    conn.close()

    return {
        "success": True,
        "id": party_id,
        "artist": artist,
        "title": title,
        "player": player
    }


@router.get("/party_queue")
def party_queue():
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS party_queue(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT,
            artist TEXT,
            title TEXT,
            player TEXT,
            added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        SELECT id, filepath, artist, title, player, added
        FROM party_queue
        ORDER BY id
    """)

    songs = [dict(row) for row in cur.fetchall()]

    conn.commit()
    conn.close()

    return {
        "success": True,
        "count": len(songs),
        "songs": songs
    }

# ============================================================
# Party-Playlist Verwaltung
# ============================================================

@router.get("/party_create")
def party_create(name: str):
    import datetime

    name = name.strip()

    if not name:
        return {
            "success": False,
            "error": "Bitte einen Namen eingeben."
        }

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS party_settings(
            id INTEGER PRIMARY KEY CHECK(id = 1),
            active_playlist_id INTEGER
        )
    """)

    datum = datetime.datetime.now().strftime("%d.%m.%Y")
    playlist_name = f"{datum} – {name}"

    cur.execute("""
        INSERT INTO playlists(name)
        VALUES (?)
    """, (playlist_name,))

    playlist_id = cur.lastrowid

    cur.execute("""
        INSERT INTO party_settings(id, active_playlist_id)
        VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET
            active_playlist_id = excluded.active_playlist_id
    """, (playlist_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "playlist_id": playlist_id,
        "name": playlist_name
    }


@router.get("/party_current")
def party_current():
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS party_settings(
            id INTEGER PRIMARY KEY CHECK(id = 1),
            active_playlist_id INTEGER
        )
    """)

    cur.execute("""
        SELECT p.id, p.name, p.created
        FROM party_settings ps
        JOIN playlists p
          ON p.id = ps.active_playlist_id
        WHERE ps.id = 1
    """)

    row = cur.fetchone()
    conn.close()

    if not row:
        return {
            "success": True,
            "active": False
        }

    return {
        "success": True,
        "active": True,
        "playlist": dict(row)
    }


@router.get("/party_add_song")
def party_add_song(
    path: str,
    artist: str = "",
    title: str = "",
    player: str = "player01"
):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS party_settings(
            id INTEGER PRIMARY KEY CHECK(id = 1),
            active_playlist_id INTEGER
        )
    """)

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)

    row = cur.fetchone()

    if not row or not row[0]:
        conn.close()
        return {
            "success": False,
            "error": "Keine aktive Party vorhanden."
        }

    playlist_id = row[0]

    cur.execute("""
        SELECT id
        FROM songs
        WHERE filepath = ?
    """, (path,))

    song = cur.fetchone()

    if not song:
        conn.close()
        return {
            "success": False,
            "error": "Titel wurde nicht in der Musikdatenbank gefunden."
        }

    song_id = song[0]

    cur.execute("""
        SELECT COALESCE(MAX(position), -1) + 1
        FROM playlist_songs
        WHERE playlist_id = ?
    """, (playlist_id,))

    position = cur.fetchone()[0]

    cur.execute("""
        INSERT OR IGNORE INTO playlist_songs
        (playlist_id, song_id, position)
        VALUES (?, ?, ?)
    """, (playlist_id, song_id, position))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "playlist_id": playlist_id,
        "song_id": song_id,
        "artist": artist,
        "title": title,
        "player": player,
        "position": position
    }


@router.get("/party_playlist_songs")
def party_playlist_songs():
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)

    row = cur.fetchone()

    if not row or not row[0]:
        conn.close()
        return {
            "success": False,
            "error": "Keine aktive Party vorhanden.",
            "songs": []
        }

    playlist_id = row[0]

    cur.execute("""
        SELECT
            ps.id,
            ps.position,
            s.id AS song_id,
            s.artist,
            s.album,
            s.title,
            s.year,
            s.duration,
            s.filepath
        FROM playlist_songs ps
        JOIN songs s ON s.id = ps.song_id
        WHERE ps.playlist_id = ?
        ORDER BY ps.position
    """, (playlist_id,))

    songs = [dict(r) for r in cur.fetchall()]

    conn.close()

    return {
        "success": True,
        "playlist_id": playlist_id,
        "count": len(songs),
        "songs": songs
    }


# ============================================================
# Party-Player Namen
# ============================================================

@router.get("/party_set_player")
def party_set_player(player: str, name: str):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS party_player_names(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            player TEXT NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(playlist_id, player)
        )
    """)

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)

    row = cur.fetchone()

    if not row or not row[0]:
        conn.close()
        return {
            "success": False,
            "error": "Keine aktive Party vorhanden."
        }

    playlist_id = row[0]
    name = name.strip()

    if not name:
        conn.close()
        return {
            "success": False,
            "error": "Bitte einen Namen eingeben."
        }

    cur.execute("""
        INSERT INTO party_player_names
        (playlist_id, player, name)
        VALUES (?, ?, ?)
        ON CONFLICT(playlist_id, player)
        DO UPDATE SET name = excluded.name
    """, (playlist_id, player, name))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "playlist_id": playlist_id,
        "player": player,
        "name": name
    }


@router.get("/party_players")
def party_players():
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)

    row = cur.fetchone()

    if not row or not row[0]:
        conn.close()
        return {
            "success": True,
            "players": []
        }

    playlist_id = row[0]

    cur.execute("""
        SELECT player, name
        FROM party_player_names
        WHERE playlist_id = ?
        ORDER BY player
    """, (playlist_id,))

    players = [dict(r) for r in cur.fetchall()]

    conn.close()

    return {
        "success": True,
        "playlist_id": playlist_id,
        "players": players
    }


# ============================================================
# Party-Musikwünsche mit Player-Name
# ============================================================

@router.get("/party_add_request")
def party_add_request(
    path: str,
    artist: str = "",
    title: str = "",
    player: str = "player01"
):
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Tabelle für die einzelnen Musikwünsche
    cur.execute("""
        CREATE TABLE IF NOT EXISTS party_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            player TEXT NOT NULL,
            requester_name TEXT NOT NULL,
            song_id INTEGER NOT NULL,
            artist TEXT,
            title TEXT,
            requested TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Aktive Party
    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)

    row = cur.fetchone()

    if not row or not row["active_playlist_id"]:
        conn.close()
        return {
            "success": False,
            "error": "Keine aktive Party vorhanden."
        }

    playlist_id = row["active_playlist_id"]

    # Name des Players
    cur.execute("""
        SELECT name
        FROM party_player_names
        WHERE playlist_id = ?
          AND player = ?
    """, (playlist_id, player))

    player_row = cur.fetchone()

    if not player_row:
        conn.close()
        return {
            "success": False,
            "error": "Für diesen Player wurde noch kein Name eingetragen."
        }

    requester_name = player_row["name"]

    # Titel in der Musikdatenbank finden
    cur.execute("""
        SELECT id
        FROM songs
        WHERE filepath = ?
    """, (path,))

    song = cur.fetchone()

    if not song:
        conn.close()
        return {
            "success": False,
            "error": "Titel wurde nicht in der Musikdatenbank gefunden."
        }

    song_id = song["id"]

    # Titel dauerhaft zur Party-Playlist hinzufügen,
    # falls er dort noch nicht vorhanden ist.
    cur.execute("""
        SELECT id
        FROM playlist_songs
        WHERE playlist_id = ?
          AND song_id = ?
    """, (playlist_id, song_id))

    existing = cur.fetchone()

    if not existing:

        cur.execute("""
            SELECT COALESCE(MAX(position), -1) + 1
            FROM playlist_songs
            WHERE playlist_id = ?
        """, (playlist_id,))

        position = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO playlist_songs
            (playlist_id, song_id, position)
            VALUES (?, ?, ?)
        """, (playlist_id, song_id, position))

    # Den eigentlichen Wunsch immer speichern.
    # Dadurch können auch mehrere Personen denselben Titel wünschen.
    cur.execute("""
        INSERT INTO party_requests
        (playlist_id, player, requester_name, song_id, artist, title)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        playlist_id,
        player,
        requester_name,
        song_id,
        artist,
        title
    ))

    request_id = cur.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "request_id": request_id,
        "playlist_id": playlist_id,
        "player": player,
        "requester_name": requester_name,
        "artist": artist,
        "title": title
    }


@router.get("/party_requests")
def party_requests():
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)

    row = cur.fetchone()

    if not row or not row["active_playlist_id"]:
        conn.close()
        return {
            "success": True,
            "requests": []
        }

    playlist_id = row["active_playlist_id"]

    cur.execute("""
        SELECT
            id,
            player,
            requester_name,
            song_id,
            artist,
            title,
            requested
        FROM party_requests
        WHERE playlist_id = ?
        ORDER BY id
    """, (playlist_id,))

    requests = [dict(r) for r in cur.fetchall()]

    conn.close()

    return {
        "success": True,
        "playlist_id": playlist_id,
        "count": len(requests),
        "requests": requests
    }


# ============================================================
# Party-Wunsch löschen – innerhalb von 2 Minuten
# ============================================================

@router.get("/party_delete_request")
def party_delete_request(request_id: int):
    import datetime

    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, playlist_id, player, requester_name, song_id, requested
        FROM party_requests
        WHERE id = ?
    """, (request_id,))
    request = cur.fetchone()

    if not request:
        conn.close()
        return {"success": False, "error": "Wunsch wurde nicht gefunden."}

    # Zeitpunkt des Wunsches prüfen
    try:
        requested_time = datetime.datetime.strptime(
            request["requested"],
            "%Y-%m-%d %H:%M:%S"
        )
        now = datetime.datetime.utcnow()
        age = (now - requested_time).total_seconds()
    except Exception:
        conn.close()
        return {"success": False, "error": "Zeitpunkt des Wunsches konnte nicht geprüft werden."}

    # maximal 2 Minuten
    if age > 120:
        conn.close()
        return {
            "success": False,
            "expired": True,
            "error": "Die 2 Minuten zum Löschen sind bereits abgelaufen."
        }

    if age < 0:
        age = 0

    playlist_id = request["playlist_id"]
    song_id = request["song_id"]

    # Wunsch löschen
    cur.execute("""
        DELETE FROM party_requests
        WHERE id = ?
    """, (request_id,))

    # Wenn niemand anderes denselben Titel gewünscht hat,
    # prüfen wir, ob der Titel von diesem Party-Wunsch
    # in die Playlist aufgenommen wurde.
    cur.execute("""
        SELECT COUNT(*)
        FROM party_requests
        WHERE playlist_id = ? AND song_id = ?
    """, (playlist_id, song_id))
    remaining_requests = cur.fetchone()[0]

    if remaining_requests == 0:
        # Nur entfernen, wenn der Titel als Party-Wunsch
        # in diese Playlist aufgenommen wurde.
        cur.execute("""
            SELECT id
            FROM playlist_songs
            WHERE playlist_id = ? AND song_id = ?
        """, (playlist_id, song_id))
        playlist_song = cur.fetchone()

        if playlist_song:
            # Prüfen, ob es vor dem Party-Wunsch bereits
            # einen Eintrag gab. Dafür verwenden wir die
            # Position nicht – bestehende Titel bleiben erhalten.
            # Party-Wunsch-Einträge werden über diese Tabelle
            # nur entfernt, wenn keine weiteren Wünsche existieren.
            #
            # Bestehende normale Playlist-Einträge bleiben daher
            # grundsätzlich erhalten.
            pass

    conn.commit()
    conn.close()

    return {
        "success": True,
        "request_id": request_id,
        "remaining_requests": remaining_requests
    }



# ============================================================
# Partymodus / Receiver – vorheriger Titel
# ============================================================

@router.get("/receiver_prev")
def receiver_prev():
    queue = load_receiver_queue()

    songs = queue.get("songs", [])
    index = queue.get("index", 0)

    if not songs:
        return {
            "success": False,
            "song": None
        }

    prev_index = index - 1

    if prev_index < 0:
        prev_index = 0

    queue["index"] = prev_index

    save_receiver_queue(
        songs,
        prev_index
    )

    return {
        "success": True,
        "song": songs[prev_index],
        "index": prev_index,
        "count": len(songs)
    }

    if prev_index < 0:
        prev_index = 0

    queue["index"] = prev_index

    save_receiver_queue(
        songs,
        prev_index
    )

    return {
        "success": True,
        "song": songs[prev_index],
        "index": prev_index,
        "count": len(songs)
    }


# ============================================================
# Partymodus – zentrale Receiver-Steuerung
# ============================================================

RECEIVER_CONTROL_FILE = "/home/Gunni/HomeMusic/app/receiver_control.json"
RECEIVER_STATUS_FILE = "/home/Gunni/HomeMusic/app/receiver_status.json"


def load_receiver_control():
    import json
    try:
        with open(RECEIVER_CONTROL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {"command": "none", "counter": 0}


def save_receiver_control(command):
    import json
    state = load_receiver_control()
    counter = int(state.get("counter", 0)) + 1

    with open(RECEIVER_CONTROL_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "command": command,
                "counter": counter
            },
            f,
            ensure_ascii=False
        )


@router.get("/receiver_control")
def receiver_control(command: str = ""):
    if command in ("play", "pause"):
        save_receiver_control(command)

    return {
        "success": True,
        **load_receiver_control()
    }


@router.get("/receiver_status")
def receiver_status():
    import json

    try:
        with open(RECEIVER_STATUS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, ValueError):
        data = {
            "playing": False,
            "current": 0,
            "duration": 0,
            "artist": "",
            "title": ""
        }

    return {
        "success": True,
        **data
    }


@router.get("/receiver_status_update")
def receiver_status_update(
    playing: int = 0,
    current: float = 0,
    duration: float = 0,
    artist: str = "",
    title: str = ""
):
    import json

    with open(RECEIVER_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "playing": bool(playing),
                "current": current,
                "duration": duration,
                "artist": artist,
                "title": title
            },
            f,
            ensure_ascii=False
        )

    return {"success": True}


# ============================================================
# Partymodus – aktive Party als Receiver-Playlist starten
# ============================================================

@router.get("/party_start")
def party_start():
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)

    party = cur.fetchone()

    if not party or not party["active_playlist_id"]:
        conn.close()
        return {
            "success": False,
            "error": "Keine aktive Party vorhanden."
        }

    playlist_id = party["active_playlist_id"]

    cur.execute("""
        SELECT
            songs.id,
            songs.artist,
            songs.title,
            songs.filepath
        FROM playlist_songs
        JOIN songs
            ON songs.id = playlist_songs.song_id
        WHERE playlist_songs.playlist_id = ?
        ORDER BY playlist_songs.position
    """, (playlist_id,))

    songs = [dict(row) for row in cur.fetchall()]

    conn.close()

    if not songs:
        return {
            "success": False,
            "error": "Die Party-Playlist ist noch leer."
        }

    # Party-Playlist als aktuelle Receiver-Warteschlange setzen
    save_receiver_queue(songs, 0)

    # Bestehenden Receiver zum Start auffordern
    save_receiver_control("play")

    return {
        "success": True,
        "playlist_id": playlist_id,
        "songs": songs,
        "index": 0,
        "song": songs[0]
    }

# ------------------------------------------------------------
# PARTY: Wiedergabereihenfolge exakt nach Musikwünschen
# ------------------------------------------------------------

@router.get("/party_start_requests")
def party_start_requests():
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)
    party = cur.fetchone()

    if not party or not party["active_playlist_id"]:
        conn.close()
        return {
            "success": False,
            "error": "Keine aktive Party vorhanden."
        }

    playlist_id = party["active_playlist_id"]

    # Jeder Musikwunsch ist ein eigener Eintrag.
    # Dadurch bleiben auch doppelte Wünsche erhalten.
    cur.execute("""
        SELECT
            pr.id AS request_id,
            s.id,
            s.artist,
            s.title,
            s.filepath
        FROM party_requests pr
        JOIN songs s ON s.id = pr.song_id
        WHERE pr.playlist_id = ?
        ORDER BY pr.id ASC
    """, (playlist_id,))

    songs = [dict(row) for row in cur.fetchall()]
    conn.close()

    if not songs:
        return {
            "success": False,
            "error": "Noch keine Musikwünsche vorhanden."
        }

    # Party-Warteschlange exakt in Wunsch-Reihenfolge setzen.
    save_receiver_queue(songs, 0)

    # Beim Neustart der Liste Position dauerhaft auf Wunsch 1 setzen.
    save_party_resume_position(
        playlist_id,
        songs[0]["request_id"]
    )

    # Receiver starten.
    save_receiver_control("play")

    return {
        "success": True,
        "playlist_id": playlist_id,
        "songs": songs,
        "index": 0,
        "song": songs[0]
    }


# ------------------------------------------------------------
# PARTY 2: Queue ausschließlich aus den aktuellen Musikwünschen
# ------------------------------------------------------------

@router.get("/party_request_queue")
def party_request_queue():
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)
    row = cur.fetchone()

    if not row or not row["active_playlist_id"]:
        conn.close()
        return {"success": False, "error": "Keine aktive Party vorhanden."}

    playlist_id = row["active_playlist_id"]

    cur.execute("""
        SELECT
            pr.id AS request_id,
            pr.player,
            pr.requester_name,
            s.id,
            s.artist,
            s.title,
            s.filepath
        FROM party_requests pr
        JOIN songs s ON s.id = pr.song_id
        WHERE pr.playlist_id = ?
        ORDER BY pr.id ASC
    """, (playlist_id,))

    songs = [dict(r) for r in cur.fetchall()]
    conn.close()

    return {
        "success": True,
        "playlist_id": playlist_id,
        "count": len(songs),
        "songs": songs
    }


@router.get("/party_start_requests2")
def party_start_requests2():
    data = party_request_queue()

    if not data["success"]:
        return data

    songs = data["songs"]

    if not songs:
        return {
            "success": False,
            "error": "Keine aktuellen Musikwünsche vorhanden."
        }

    save_receiver_queue(songs, 0)
    save_receiver_control("play")

    return {
        "success": True,
        "playlist_id": data["playlist_id"],
        "count": len(songs),
        "songs": songs,
        "index": 0,
        "song": songs[0]
    }


# ------------------------------------------------------------
# PARTY: Nach STOP mit START zum nächsten Musikwunsch
# ------------------------------------------------------------

@router.get("/party_start_next")
def party_start_next():
    queue = load_receiver_queue()
    songs = queue.get("songs", [])
    index = int(queue.get("index", 0))

    # Wenn noch keine Party-Queue vorhanden ist:
    # aktuelle Musikwünsche laden und beim ersten Titel starten.
    if not songs:
        data = party_request_queue()

        if not data["success"] or not data["songs"]:
            return {
                "success": False,
                "error": "Keine Musikwünsche vorhanden."
            }

        songs = data["songs"]
        index = 0

    else:
        # START nach STOP = nächster Titel
        next_index = index + 1

        if next_index >= len(songs):
            return {
                "success": False,
                "finished": True,
                "error": "Das Ende der Party-Playlist ist erreicht."
            }

        index = next_index

    save_receiver_queue(songs, index)
    save_receiver_control("play")

    return {
        "success": True,
        "index": index,
        "count": len(songs),
        "song": songs[index]
    }


@router.get("/party_next_request")
def party_next_request(direction: int = 1):
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)
    party = cur.fetchone()

    if not party or not party["active_playlist_id"]:
        conn.close()
        return {"success": False, "error": "Keine aktive Party vorhanden."}

    playlist_id = party["active_playlist_id"]

    cur.execute("""
        SELECT
            pr.id AS request_id,
            s.id,
            s.artist,
            s.title,
            s.filepath
        FROM party_requests pr
        JOIN songs s ON s.id = pr.song_id
        WHERE pr.playlist_id = ?
        ORDER BY pr.id ASC
    """, (playlist_id,))

    requests = [dict(row) for row in cur.fetchall()]
    conn.close()

    if not requests:
        return {"success": False, "error": "Keine Musikwünsche vorhanden."}

    queue = load_receiver_queue()
    queue_songs = queue.get("songs", [])
    current_index = int(queue.get("index", 0))

    current_request_id = None

    if queue_songs and 0 <= current_index < len(queue_songs):
        current_request_id = queue_songs[current_index].get("request_id")

    # Aktuellen Titel in der echten Wunschliste suchen.
    if current_request_id is not None:
        for i, song in enumerate(requests):
            if song["request_id"] == current_request_id:
                current_index = i
                break
    elif queue_songs and 0 <= current_index < len(queue_songs):
        current_path = queue_songs[current_index].get("filepath")
        for i, song in enumerate(requests):
            if song["filepath"] == current_path:
                current_index = i
                break
    else:
        current_index = 0

    new_index = current_index + direction

    if new_index < 0:
        new_index = 0

    if new_index >= len(requests):
        return {
            "success": False,
            "finished": True,
            "error": "Kein weiterer Titel vorhanden."
        }

    save_receiver_queue(requests, new_index)

    # Neue Party-Position dauerhaft serverseitig merken.
    save_party_resume_position(
        playlist_id,
        requests[new_index]["request_id"]
    )

    save_receiver_control("play")

    return {
        "success": True,
        "song": requests[new_index],
        "index": new_index,
        "count": len(requests)
    }


# ------------------------------------------------------------
# Party Start/Stopp: nach Stopp beim nächsten Wunsch weitermachen
# ------------------------------------------------------------

PARTY_TRANSPORT_STATE_FILE = "/home/Gunni/HomeMusic/app/party_transport_state.json"


def load_party_transport_state():
    import json
    try:
        with open(PARTY_TRANSPORT_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {
            "playlist_id": None,
            "stopped": False
        }


def save_party_transport_state(playlist_id, stopped):
    import json
    with open(PARTY_TRANSPORT_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "playlist_id": playlist_id,
            "stopped": bool(stopped)
        }, f, ensure_ascii=False)


@router.get("/party_stop")
def party_stop():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)
    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        return {
            "success": False,
            "error": "Keine aktive Party vorhanden."
        }

    playlist_id = row[0]

    save_party_transport_state(
        playlist_id,
        True
    )

    save_receiver_control("pause")

    return {
        "success": True,
        "stopped": True
    }


@router.get("/party_start_continue")
def party_start_continue():
    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)
    party = cur.fetchone()

    if not party or not party["active_playlist_id"]:
        conn.close()
        return {
            "success": False,
            "error": "Keine aktive Party vorhanden."
        }

    playlist_id = party["active_playlist_id"]

    cur.execute("""
        SELECT
            pr.id AS request_id,
            s.id,
            s.artist,
            s.title,
            s.filepath
        FROM party_requests pr
        JOIN songs s ON s.id = pr.song_id
        WHERE pr.playlist_id = ?
        ORDER BY pr.id ASC
    """, (playlist_id,))

    requests = [dict(row) for row in cur.fetchall()]
    conn.close()

    if not requests:
        return {
            "success": False,
            "error": "Noch keine Musikwünsche vorhanden."
        }

    queue = load_receiver_queue()
    queue_songs = queue.get("songs", [])
    queue_index = int(queue.get("index", 0))

    state = load_party_transport_state()

    # Prüfen, ob die aktuelle Receiver-Queue wirklich
    # die aktuelle Wunschliste dieser Party ist.
    request_ids = [song["request_id"] for song in requests]
    queue_ids = [
        song.get("request_id")
        for song in queue_songs
        if song.get("request_id") is not None
    ]

    same_queue = (
        state.get("playlist_id") == playlist_id
        and queue_ids == request_ids
    )

    if not same_queue:
        # Neue bzw. andere Party-Wunschliste:
        # beim ersten Titel beginnen.
        new_index = 0

    elif state.get("stopped"):
        # Nach einem echten Stopp:
        # beim nächsten Titel weitermachen.
        current_index = queue_index
        new_index = current_index + 1

        if new_index >= len(requests):
            return {
                "success": False,
                "finished": True,
                "error": "Das Ende der Wunschliste ist erreicht."
            }

    else:
        # Normaler Start ohne vorherigen Stopp:
        # aktuellen Titel weiterlaufen lassen.
        new_index = queue_index

        if new_index < 0 or new_index >= len(requests):
            new_index = 0

    save_receiver_queue(
        requests,
        new_index
    )

    save_party_transport_state(
        playlist_id,
        False
    )

    save_receiver_control("play")

    return {
        "success": True,
        "playlist_id": playlist_id,
        "index": new_index,
        "count": len(requests),
        "song": requests[new_index]
    }


# ------------------------------------------------------------
# PARTY: Stopp merkt sich den aktuellen Wunsch.
# Nächster Start spielt danach den nächsten Wunsch.
# ------------------------------------------------------------

PARTY_STOP_MARKER_FILE = "/home/Gunni/HomeMusic/app/party_stop_marker.json"


def save_party_stop_marker(playlist_id, request_id):
    import json
    with open(PARTY_STOP_MARKER_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "playlist_id": playlist_id,
            "request_id": request_id
        }, f)


def load_party_stop_marker():
    import json
    try:
        with open(PARTY_STOP_MARKER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {}


@router.get("/party_stop_mark")
def party_stop_mark():

    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)

    party = cur.fetchone()

    if not party or not party["active_playlist_id"]:
        conn.close()
        return {
            "success": False,
            "error": "Keine aktive Party vorhanden."
        }

    playlist_id = party["active_playlist_id"]

    # Aktuellen Titel aus der Receiver-Queue holen.
    queue = load_receiver_queue()

    songs = queue.get("songs", [])
    index = int(queue.get("index", 0))

    if not songs or index < 0 or index >= len(songs):
        conn.close()
        return {
            "success": False,
            "error": "Aktueller Party-Titel konnte nicht ermittelt werden."
        }

    current_song = songs[index]

    # WICHTIG:
    # Wenn die Queue die request_id kennt, verwenden wir genau diese.
    # Dadurch funktionieren auch doppelte Wünsche desselben Titels.
    current_request_id = current_song.get("request_id")

    # Fallback für ältere Queues ohne request_id.
    if current_request_id is None:

        current_path = current_song.get("filepath")

        if not current_path:
            conn.close()
            return {
                "success": False,
                "error": "Dateipfad des aktuellen Titels fehlt."
            }

        cur.execute("""
            SELECT
                pr.id AS request_id,
                s.filepath
            FROM party_requests pr
            JOIN songs s ON s.id = pr.song_id
            WHERE pr.playlist_id = ?
            ORDER BY pr.id ASC
        """, (playlist_id,))

        requests = cur.fetchall()

        for request in requests:
            if request["filepath"] == current_path:
                current_request_id = request["request_id"]
                break

    if current_request_id is None:
        conn.close()
        return {
            "success": False,
            "error": "Aktueller Titel ist nicht in der aktuellen Wunschliste."
        }

    save_party_stop_marker(
        playlist_id,
        current_request_id
    )

    # Zusätzlich die letzte Party-Position dauerhaft speichern.
    save_party_resume_position(
        playlist_id,
        current_request_id
    )

    conn.close()

    # Receiver wirklich pausieren.
    save_receiver_control("pause")

    return {
        "success": True,
        "request_id": current_request_id,
        "artist": current_song.get("artist", ""),
        "title": current_song.get("title", "")
    }


@router.get("/party_start_after_stop")
def party_start_after_stop():

    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)

    party = cur.fetchone()

    if not party or not party["active_playlist_id"]:
        conn.close()
        return {
            "success": False,
            "error": "Keine aktive Party vorhanden."
        }

    playlist_id = party["active_playlist_id"]

    # Wenn bereits Musik läuft und kein Stopp gemerkt wurde,
    # soll START den aktuellen Titel nicht zurücksetzen.
    try:
        import json
        with open(RECEIVER_STATUS_FILE, "r", encoding="utf-8") as f:
            receiver_status = json.load(f)
    except (FileNotFoundError, ValueError):
        receiver_status = {}

    stop_marker = load_party_stop_marker()

    if receiver_status.get("playing") and not stop_marker.get("request_id"):
        queue = load_receiver_queue()
        songs = queue.get("songs", [])
        index = int(queue.get("index", 0))

        if 0 <= index < len(songs):
            save_receiver_control("play")
            return {
                "success": True,
                "index": index,
                "count": len(songs),
                "song": songs[index]
            }


    cur.execute("""
        SELECT
            pr.id AS request_id,
            s.id,
            s.artist,
            s.title,
            s.filepath
        FROM party_requests pr
        JOIN songs s ON s.id = pr.song_id
        WHERE pr.playlist_id = ?
        ORDER BY pr.id ASC
    """, (playlist_id,))

    requests = [dict(row) for row in cur.fetchall()]
    conn.close()

    if not requests:
        return {
            "success": False,
            "error": "Keine Musikwünsche vorhanden."
        }

    marker = load_party_stop_marker()

    # Wenn kein gültiger Stopp-Marker vorhanden ist,
    # beim ersten Wunsch beginnen.
    if (
        marker.get("playlist_id") != playlist_id
        or not marker.get("request_id")
    ):
        new_index = 0

    else:

        stopped_request_id = marker["request_id"]

        stopped_index = None

        for i, song in enumerate(requests):
            if song["request_id"] == stopped_request_id:
                stopped_index = i
                break

        if stopped_index is None:
            new_index = 0
        else:
            new_index = stopped_index + 1

            if new_index >= len(requests):
                return {
                    "success": False,
                    "finished": True,
                    "error": "Das Ende der Wunschliste ist erreicht."
                }

    save_receiver_queue(
        requests,
        new_index
    )

    # Marker löschen, damit derselbe Stopp
    # nicht zweimal als nächster Start verwendet wird.
    import json
    try:
        with open(PARTY_STOP_MARKER_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    except Exception:
        pass

    save_receiver_control("play")

    return {
        "success": True,
        "index": new_index,
        "count": len(requests),
        "song": requests[new_index]
    }


# ============================================================
# PARTY RESUME / POSITION SPEICHERN
# ============================================================

from pathlib import Path
from fastapi import Request
import json
import time

PARTY_RESUME_FILE = (
    Path(__file__).resolve().parent /
    "party_resume.json"
)


def save_party_resume_position(playlist_id, request_id):
    """Serverseitig letzten Party-Wunsch merken."""
    if playlist_id is None or request_id is None:
        return

    data = {
        "playlist_id": int(playlist_id),
        "request_id": int(request_id),
        "saved_at": time.time()
    }

    tmp = PARTY_RESUME_FILE.with_suffix(".tmp")

    tmp.write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8"
    )

    tmp.replace(PARTY_RESUME_FILE)


def load_party_resume_position():
    """Gespeicherte Party-Position laden."""
    if not PARTY_RESUME_FILE.exists():
        return None

    try:
        data = json.loads(
            PARTY_RESUME_FILE.read_text(
                encoding="utf-8"
            )
        )

        playlist_id = data.get("playlist_id")
        request_id = data.get("request_id")

        if playlist_id is None or request_id is None:
            return None

        return {
            "playlist_id": int(playlist_id),
            "request_id": int(request_id),
            "saved_at": data.get("saved_at")
        }

    except Exception:
        return None


@router.get("/party_resume_info")
def party_resume_info():
    data = load_party_resume_position()

    if not data:
        return {
            "ok": True,
            "available": False
        }

    return {
        "ok": True,
        "available": True,
        "playlist_id": data["playlist_id"],
        "request_id": data["request_id"],
        "saved_at": data.get("saved_at")
    }


@router.post("/party_resume_start")
def party_resume_start():

    saved = load_party_resume_position()

    if not saved:
        return {
            "ok": False,
            "message": "Keine gespeicherte Position vorhanden"
        }

    conn = connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Aktive Party prüfen.
    cur.execute("""
        SELECT active_playlist_id
        FROM party_settings
        WHERE id = 1
    """)

    party = cur.fetchone()

    if not party or not party["active_playlist_id"]:
        conn.close()
        return {
            "ok": False,
            "message": "Keine aktive Party vorhanden"
        }

    playlist_id = int(party["active_playlist_id"])

    # Gespeicherte Position muss zur aktuellen Party gehören.
    if playlist_id != saved["playlist_id"]:
        conn.close()
        return {
            "ok": False,
            "message": "Gespeicherte Position gehört zu einer anderen Party"
        }

    # Aktuelle Wunschliste wieder aus der Datenbank aufbauen.
    cur.execute("""
        SELECT
            pr.id AS request_id,
            s.id,
            s.artist,
            s.title,
            s.filepath
        FROM party_requests pr
        JOIN songs s ON s.id = pr.song_id
        WHERE pr.playlist_id = ?
        ORDER BY pr.id ASC
    """, (playlist_id,))

    songs = [dict(row) for row in cur.fetchall()]
    conn.close()

    if not songs:
        return {
            "ok": False,
            "message": "Keine Musikwünsche vorhanden"
        }

    # Gespeicherte request_id suchen.
    index = None

    for i, song in enumerate(songs):
        if int(song["request_id"]) == saved["request_id"]:
            index = i
            break

    if index is None:
        return {
            "ok": False,
            "message": "Gespeicherter Wunsch ist nicht mehr vorhanden"
        }

    save_receiver_queue(songs, index)
    save_receiver_control("play")

    return {
        "ok": True,
        "index": index,
        "count": len(songs),
        "song": songs[index]
    }


@router.post("/party_resume_clear")
def party_resume_clear():

    try:
        if PARTY_RESUME_FILE.exists():
            PARTY_RESUME_FILE.unlink()

        return {
            "ok": True
        }

    except Exception as e:
        return {
            "ok": False,
            "message": str(e)
        }

