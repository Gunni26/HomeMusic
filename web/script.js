let timer = null;
let selectedRow = 0;
let currentSongs = [];

document.addEventListener("DOMContentLoaded", () => {

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
        <tr class="${index === 0 ? "selected" : ""}">

            <td>${song.artist || "-"}</td>
            <td>${song.album || "-"}</td>
            <td>${song.title || "-"}</td>
            <td>${song.year || "-"}</td>

            <td>
                <button onclick="playSong(
'${encodeURIComponent(song.filepath)}',
'${(song.artist || "").replace(/'/g, "\\'")}',
'${(song.title || "").replace(/'/g, "\\'")}'
)">
                    ▶
                </button>
            </td>

        </tr>
        `;

    });

    document.getElementById("results").innerHTML = html;

    selectedRow = 0;

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
            encodeURIComponent(currentSongs[selectedRow].filepath)
        );

        return;

    }

    else if (event.key === "Escape") {

        clearSearch();
        return;

    }

    rows.forEach(row => row.classList.remove("selected"));

    if (rows[selectedRow])
        rows[selectedRow].classList.add("selected");

}



function playSong(path, artist = "", title = "") {

    if (!window.player) {

        window.player = new Audio();

        window.player.addEventListener("timeupdate", updatePlayer);

        window.player.addEventListener("loadedmetadata", updatePlayer);

        window.player.addEventListener("ended", function () {

            document.getElementById("playPauseButton").textContent = "▶";

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
