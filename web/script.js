let timer = null;
let selectedRow = 0;
let currentSongs = [];

document.addEventListener("DOMContentLoaded", () => {

    loadReceiverVolume();

    const search = document.getElementById("search");

    search.addEventListener("input", () => {

        clearTimeout(timer);
        timer = setTimeout(searchMusic, 250);

    });

    document.querySelectorAll("input[name='searchmode']").forEach(radio => {

        radio.addEventListener("change", searchMusic);

    });

    document.addEventListener("keydown", handleKeys);

});


async function searchMusic() {

    const text = document.getElementById("search").value.trim();

    const mode = document.querySelector(
        "input[name='searchmode']:checked"
    ).value;

    const count = document.getElementById("count");

    if (text === "") {

        currentSongs = [];
        count.innerHTML = "0 Treffer";
        document.getElementById("results").innerHTML = "";
        return;

    }

    count.innerHTML = "🔍 Suche...";

    const response = await fetch(
        "/search?q=" +
        encodeURIComponent(text) +
        "&mode=" +
        encodeURIComponent(mode)
    );

    currentSongs = await response.json();

    count.innerHTML = "🎵 " + currentSongs.length + " Treffer";

    let html = "";

    currentSongs.forEach((song, index) => {

        html += `
        <tr
            class="${index === 0 ? "selected" : ""}"
            onclick="playSong(
                '${encodeURIComponent(song.filepath)}',
                '${(song.artist || "").replace(/'/g, "\\'")}',
                '${(song.title || "").replace(/'/g, "\\'")}'
            )">

            <td>${song.artist || "-"}</td>
            <td>${song.album || "-"}</td>
            <td>${song.title || "-"}</td>
            <td>${song.year || "-"}</td>

            <td>
                <button
                    type="button"
                    onclick="event.stopPropagation(); addToPlaylist(${index})">
                    ＋
                </button>
            </td>

        </tr>
        `;

    });

    document.getElementById("results").innerHTML = html;

    selectedRow = 0;

}


async function importMusic() {

    const button = document.getElementById("importButton");
    const status = document.getElementById("importStatus");

    button.disabled = true;
    button.textContent = "⏳ Musik wird eingelesen...";
    status.textContent = "Bitte warten...";

    try {

        const response = await fetch("/import");

        const data = await response.json();

        if (!data.success) {

            status.textContent = "❌ Fehler beim Einlesen.";
            console.error(data.error);
            return;

        }

        const output = data.output || "";

        const importedMatch = output.match(
            /Neu importiert\s*:\s*(\d+)/
        );

        const errorMatch = output.match(
            /Fehler\s*:\s*(\d+)/
        );

        const imported = importedMatch
            ? importedMatch[1]
            : "0";

        const errors = errorMatch
            ? errorMatch[1]
            : "0";

        if (errors !== "0") {

            status.textContent =
                "⚠️ " + imported +
                " neue Titel importiert – " +
                errors + " Fehler";

        } else {

            status.textContent =
                "✅ " + imported +
                " neue Titel importiert";

        }

        // Falls gerade gesucht wird, Suche erneut ausführen
        if (document.getElementById("search").value.trim() !== "") {
            await searchMusic();
        }

    } catch (error) {

        console.error(error);

        status.textContent =
            "❌ Verbindung zum HomeMusic-Server fehlgeschlagen.";

    } finally {

        button.disabled = false;
        button.textContent = "🔄 Neue Musik einlesen";

    }

}



function setReceiverVolume(value) {

    fetch(
        "/set_volume?value=" +
        encodeURIComponent(Number(value) / 100)
    )
    .catch(error => {
        console.error(
            "Lautstärke konnte nicht gesetzt werden:",
            error
        );
    });
}


async function loadReceiverVolume() {

    try {
        const response = await fetch("/volume?t=" + Date.now());
        const data = await response.json();

        if (data.success) {
            const slider =
                document.getElementById("receiverVolume");

            if (slider) {
                slider.value =
                    Math.round(data.volume * 100);
            }
        }

    } catch (error) {
        console.error(
            "Empfänger-Lautstärke konnte nicht gelesen werden:",
            error
        );
    }
}

function playSong(
    path,
    artist = "",
    title = "",
    playlistMode = false
) {

    // Aktuellen Titel für den Netzwerk-Stream setzen
    fetch(
        "/set_current?path=" +
        path +
        "&artist=" +
        encodeURIComponent(artist) +
        "&title=" +
        encodeURIComponent(title)
    )
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error(
                    "Stream-Titel konnte nicht gesetzt werden:",
                    data
                );
            }
        })
        .catch(error => {
            console.error(
                "Stream-Verbindung fehlgeschlagen:",
                error
            );
        });

    if (!playlistMode) {
        fetch(
            "/set_receiver_single?path=" +
            path +
            "&artist=" +
            encodeURIComponent(artist) +
            "&title=" +
            encodeURIComponent(title)
        )
        .catch(error => {
            console.error(
                "Receiver-Titel konnte nicht gesetzt werden:",
                error
            );
        });
    }

    if (!window.player) {

        window.player = new Audio();

        window.player.addEventListener("timeupdate", updatePlayer);

        window.player.addEventListener("loadedmetadata", updatePlayer);

        window.player.addEventListener("ended", function () {

            document.getElementById("playPauseButton").textContent = "▶";

            if (
                activePlaylistIndex >= 0 &&
                activePlaylistIndex <
                activePlaylistSongs.length - 1
            ) {
                playPlaylistSong(
                    activePlaylistIndex + 1,
                    false
                );
            } else {
                activePlaylistIndex = -1;
            }

        });

    }

    window.player.src = "/play?path=" + path;

    window.player.play();

    document.getElementById("playPauseButton").textContent = "⏸";

    document.getElementById("currentSong").textContent =
        "🎵 " + artist + " – " + title;

}


function clearSearch() {

    document.getElementById("search").value = "";
    document.getElementById("results").innerHTML = "";
    document.getElementById("count").innerHTML = "0 Treffer";

    currentSongs = [];
    selectedRow = 0;

    document.getElementById("search").focus();

}


function togglePlay() {

    if (!window.player)
        return;

    if (window.player.paused) {

        window.player.play();

        document.getElementById("playPauseButton").textContent = "⏸";

    } else {

        window.player.pause();

        document.getElementById("playPauseButton").textContent = "▶";

    }

}


function stopPlayer() {

    if (!window.player)
        return;

    window.player.pause();

    window.player.currentTime = 0;

    document.getElementById("playPauseButton").textContent = "▶";

    document.getElementById("progress").value = 0;

    document.getElementById("currentTime").textContent = "00:00";

}


function updatePlayer() {

    if (!window.player)
        return;

    document.getElementById("currentTime").textContent =
        formatTime(window.player.currentTime);

    document.getElementById("duration").textContent =
        formatTime(window.player.duration);

    document.getElementById("progress").max =
        window.player.duration || 0;

    document.getElementById("progress").value =
        window.player.currentTime;

}


function seekPlayer() {

    if (!window.player)
        return;

    window.player.currentTime =
        document.getElementById("progress").value;

}


function formatTime(sec) {

    if (isNaN(sec))
        return "00:00";

    let m = Math.floor(sec / 60);

    let s = Math.floor(sec % 60);

    return m + ":" + String(s).padStart(2, "0");

}


function handleKeys(event) {

    if (currentSongs.length === 0)
        return;

    const rows = document.querySelectorAll("#results tr");

    if (event.key === "ArrowDown") {

        event.preventDefault();

        if (selectedRow < rows.length - 1)
            selectedRow++;

    }

    else if (event.key === "ArrowUp") {

        event.preventDefault();

        if (selectedRow > 0)
            selectedRow--;

    }

    else if (event.key === "Enter") {

        event.preventDefault();

        playSong(
            encodeURIComponent(currentSongs[selectedRow].filepath),
            currentSongs[selectedRow].artist,
            currentSongs[selectedRow].title
        );

        return;

    }

    else if (event.key === "Escape") {

        clearSearch();
        return;

    }

    rows.forEach(row => row.classList.remove("selected"));

    if (rows[selectedRow]) {

        rows[selectedRow].classList.add("selected");

        const container =
            document.getElementById("results-container");

        const row = rows[selectedRow];

        const rowTop = row.offsetTop;
        const rowBottom = rowTop + row.offsetHeight;

        const reserve = row.offsetHeight * 3;

        if (rowTop < container.scrollTop) {

            container.scrollTop = rowTop - reserve;

        }
        else if (
            rowBottom >
            container.scrollTop +
            container.clientHeight -
            reserve
        ) {

            container.scrollTop =
                rowBottom -
                container.clientHeight +
                reserve;

        }

    }

}


// ============================================================
// Playlists
// ============================================================

async function loadPlaylists() {

    try {

        const response = await fetch(
            "/playlists?t=" + Date.now()
        );

        const playlists = await response.json();

        const select =
            document.getElementById("playlistSelect");

        select.innerHTML =
            '<option value="">Playlist auswählen</option>';

        playlists.forEach(playlist => {

            const option =
                document.createElement("option");

            option.value = playlist.id;
            option.textContent = playlist.name;

            select.appendChild(option);
        });

    } catch (error) {

        console.error(
            "Playlists konnten nicht geladen werden:",
            error
        );
    }
}


async function createPlaylist() {

    const input =
        document.getElementById("playlistName");

    const status =
        document.getElementById("playlistStatus");

    const name =
        input.value.trim();

    if (!name) {

        status.textContent =
            "Bitte einen Playlistnamen eingeben.";

        return;
    }

    try {

        const response = await fetch(
            "/playlists?name=" +
            encodeURIComponent(name),
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (!data.success) {

            status.textContent =
                "⚠️ " + data.error;

            return;
        }

        input.value = "";

        status.textContent =
            "✅ Playlist erstellt";

        await loadPlaylists();

        document.getElementById("playlistSelect").value =
            data.id;

    } catch (error) {

        console.error(error);

        status.textContent =
            "❌ Playlist konnte nicht erstellt werden.";
    }
}


async function loadPlaylistSongs() {

    const select =
        document.getElementById("playlistSelect");

    const playlistId =
        select.value;

    if (!playlistId) {
        return;
    }

    try {

        const response = await fetch(
            "/playlists/" +
            playlistId +
            "/songs?t=" +
            Date.now()
        );

        const songs = await response.json();

        console.log(
            "Playlist geladen:",
            songs
        );

        showPlaylistSongs(playlistId);

    } catch (error) {

        console.error(
            "Playlist konnte nicht geladen werden:",
            error
        );
    }
}


// Playlists beim Start laden
document.addEventListener("DOMContentLoaded", () => {

    loadPlaylists();

});


async function addToPlaylist(index) {

    const playlistSelect =
        document.getElementById("playlistSelect");

    const playlistId =
        playlistSelect.value;

    const status =
        document.getElementById("playlistStatus");

    if (!playlistId) {
        status.textContent =
            "Bitte zuerst eine Playlist auswählen.";
        return;
    }

    const song =
        currentSongs[index];

    try {

        const response = await fetch(
            "/playlists/" +
            playlistId +
            "/songs/" +
            song.id,
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (!data.success) {
            status.textContent =
                "⚠️ " + data.error;
            return;
        }

        status.textContent =
            "✅ " + (song.title || "Titel") +
            " zur Playlist hinzugefügt.";

    } catch (error) {

        console.error(error);

        status.textContent =
            "❌ Titel konnte nicht hinzugefügt werden.";
    }
}

async function showPlaylistSongs(playlistId) {
    const box = document.getElementById("playlistSongs");

    if (!playlistId) {
        box.innerHTML = "";
        return;
    }

    const response = await fetch(
        "/playlists/" + playlistId + "/songs?t=" + Date.now()
    );

    const songs = await response.json();

    activePlaylistSongs = songs;
    activePlaylistIndex = -1;

    if (songs.length === 0) {
        box.innerHTML = "<div>Playlist ist leer.</div>";
        return;
    }

    let html = "<div class=\"playlist-title\">Playlist</div>";
    html += "<table><tbody>";

    songs.forEach((song, index) => {
        html += `
        <tr onclick="playPlaylistSong(${index})">
            <td>${song.artist || "-"}</td>
            <td>${song.album || "-"}</td>
            <td>${song.title || "-"}</td>
            <td>${song.year || "-"}</td>
        </tr>`;
    });

    html += "</tbody></table>";

    box.innerHTML = html;
}

/* ============================================================
   Playlist-Wiedergabe
   ============================================================ */

let activePlaylistSongs = [];
let activePlaylistIndex = -1;

function playPlaylistSong(index, setReceiver = true) {

    if (
        index < 0 ||
        index >= activePlaylistSongs.length
    ) {
        activePlaylistIndex = -1;
        return;
    }

    activePlaylistIndex = index;

    const song = activePlaylistSongs[index];

    const playLocal = () => {
        playSong(
            encodeURIComponent(song.filepath),
            song.artist || "",
            song.title || "",
            true
        );
    };

    // Nur beim bewussten Start eines Playlist-Titels
    // die Receiver-Playlist setzen.
    if (!setReceiver) {
        playLocal();
        return;
    }

    const playlistId =
        document.getElementById("playlistSelect").value;

    fetch(
        "/set_receiver_playlist?playlist_id=" +
        encodeURIComponent(playlistId) +
        "&index=" +
        encodeURIComponent(index)
    )
    .then(response => response.json())
    .then(data => {

        if (!data.success) {
            console.error(
                "Receiver-Playlist konnte nicht gesetzt werden:",
                data
            );
            return;
        }

        playLocal();
    })
    .catch(error => {
        console.error(
            "Receiver-Playlist konnte nicht gesetzt werden:",
            error
        );
    });
}

