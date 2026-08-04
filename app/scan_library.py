from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".m4a",
    ".ogg",
}

MUSIC_PATH = "/srv/dev-disk-by-uuid-68ba41f9-bf43-40cc-ad01-ec7fe4525ad8/Ri4-Daten/DatenAllesAusNasServer/AusNasMusik"


def scan_library():
    music_dir = Path(MUSIC_PATH)

    files = []

    for file in music_dir.rglob("*"):
        if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(file)

    return sorted(files)


if __name__ == "__main__":
    files = scan_library()

    print(f"\n{len(files)} Musikdateien gefunden.\n")

    for file in files[:20]:
        print(file)

    if len(files) > 20:
        print(f"\n... und {len(files)-20} weitere Dateien.")
