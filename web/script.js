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
                <button onclick="playSong('${encodeURIComponent(song.filepath)}')">
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



    function playSong(path) {

    const audio = new Audio("/play?path=" + path);
    audio.play();

}


function clearSearch() {

    document.getElementById("search").value = "";
    document.getElementById("results").innerHTML = "";
    document.getElementById("count").innerHTML = "0 Treffer";

    currentSongs = [];
    selectedRow = 0;

    document.getElementById("search").focus();

}
