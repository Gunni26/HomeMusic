from pathlib import Path
from mutagen import File


def read_tags(filepath):
    path = Path(filepath)

    audio = File(path, easy=True)

    if audio is None:
        return None

    info = {
        "title": path.stem,
        "artist": "",
        "album": "",
        "genre": "",
        "year": "",
        "track": 0,
        "duration": 0,
        "filename": path.name,
        "filepath": str(path),
        "filesize": path.stat().st_size,
    }

    def get_value(key, default=""):
        value = audio.get(key, [default])
        return value[0] if value else default

    info["title"] = get_value("title", path.stem)
    info["artist"] = get_value("artist")
    info["album"] = get_value("album")
    info["genre"] = get_value("genre")
    info["year"] = get_value("date") or get_value("year")

    track = get_value("tracknumber", "0")
    try:
        info["track"] = int(str(track).split("/")[0])
    except ValueError:
        info["track"] = 0

    try:
        info["duration"] = round(audio.info.length, 1)
    except Exception:
        pass

    return info


if __name__ == "__main__":
    TESTFILE = "/srv/dev-disk-by-uuid-68ba41f9-bf43-40cc-ad01-ec7fe4525ad8/Ri4-Daten/DatenAllesAusNasServer/AusNasMusik/Musik 01/1 FC Koeln-Hoehner - Hey Koelle Dubese Jefoehl.mp3"

    tags = read_tags(TESTFILE)

    if tags:
        print("\nGefundene Tags:\n")
        for key, value in tags.items():
            print(f"{key:10}: {value}")
    else:
        print("Datei konnte nicht gelesen werden.")
