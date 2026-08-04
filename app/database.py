import sqlite3
from pathlib import Path

# Projektverzeichnis bestimmen
BASE_DIR = Path(__file__).resolve().parent.parent

# Datenbankdatei
DB = BASE_DIR / "app" / "database" / "music.db"


def connect():
    DB.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB)


def init_database():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        artist TEXT,
        album TEXT,
        genre TEXT,
        year TEXT,
        track INTEGER,
        duration REAL,
        filename TEXT,
        filepath TEXT UNIQUE,
        filesize INTEGER,
        added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_database()
    print("music.db bereit")

