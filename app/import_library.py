import sqlite3
import time

from database import connect, init_database
from scan_library import scan_library
from tag_reader import read_tags


def import_library():
    init_database()

    conn = connect()
    cur = conn.cursor()

    files = scan_library()

    total = len(files)
    imported = 0
    skipped = 0
    errors = 0

    start = time.time()

    print(f"\nHomeMusic 0.1.0")
    print("-" * 40)
    print(f"{total} Musikdateien gefunden.\n")

    for number, file in enumerate(files, start=1):

        print(f"[{number}/{total}] {file.name}")

        try:
            tags = read_tags(file)

            if tags is None:
                errors += 1
                continue

            cur.execute(
                """
                INSERT OR IGNORE INTO songs
                (
                    title,
                    artist,
                    album,
                    genre,
                    year,
                    track,
                    duration,
                    filename,
                    filepath,
                    filesize
                )
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    tags["title"],
                    tags["artist"],
                    tags["album"],
                    tags["genre"],
                    tags["year"],
                    tags["track"],
                    tags["duration"],
                    tags["filename"],
                    tags["filepath"],
                    tags["filesize"],
                ),
            )

            if cur.rowcount == 1:
                imported += 1
            else:
                skipped += 1

        except Exception as e:
            errors += 1
            print(f"Fehler: {e}")

    conn.commit()
    conn.close()

    duration = round(time.time() - start, 1)

    print("\n" + "-" * 40)
    print("Import abgeschlossen\n")
    print(f"Gefunden     : {total}")
    print(f"Importiert   : {imported}")
    print(f"Übersprungen : {skipped}")
    print(f"Fehler       : {errors}")
    print(f"Dauer        : {duration} Sekunden")


if __name__ == "__main__":
    import_library()
