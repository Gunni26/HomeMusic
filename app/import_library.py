import time

from database import connect, init_database
from scan_library import scan_library
from tag_reader import read_tags


def import_library():
    init_database()

    conn = connect()
    cur = conn.cursor()

    print("\nHomeMusic – schneller Musikimport")
    print("-" * 40)

    start = time.time()

    # Alle bereits bekannten Dateien aus der Datenbank holen
    cur.execute("SELECT filepath FROM songs")
    existing_files = {row[0] for row in cur.fetchall()}

    # Musikordner durchsuchen
    files = scan_library()

    total = len(files)
    imported = 0
    skipped = 0
    errors = 0

    print(f"{total} Musikdateien gefunden.")
    print(f"{len(existing_files)} bereits in der Datenbank.")
    print()

    for number, file in enumerate(files, start=1):

        filepath = str(file)

        # Bereits bekannte Datei sofort überspringen
        if filepath in existing_files:
            skipped += 1
            continue

        print(f"[NEU {number}/{total}] {file.name}")

        try:
            tags = read_tags(file)

            if tags is None:
                errors += 1
                print("  Fehler: Tags konnten nicht gelesen werden.")
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
                existing_files.add(filepath)
            else:
                skipped += 1

        except Exception as e:
            errors += 1
            print(f"  Fehler: {e}")

    conn.commit()
    conn.close()

    duration = round(time.time() - start, 1)

    print("\n" + "-" * 40)
    print("Import abgeschlossen")
    print()
    print(f"Gefunden     : {total}")
    print(f"Neu importiert: {imported}")
    print(f"Übersprungen : {skipped}")
    print(f"Fehler       : {errors}")
    print(f"Dauer        : {duration} Sekunden")


if __name__ == "__main__":
    import_library()
