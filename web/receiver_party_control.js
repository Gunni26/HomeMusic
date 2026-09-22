(function () {

    let lastCounter = 0;

    const player = document.getElementById("streamPlayer");

    if (!player) {
        console.error("HomeMusic: streamPlayer nicht gefunden");
        return;
    }

    async function checkPartyControl() {

        try {
            const response = await fetch(
                "/receiver_control?t=" + Date.now(),
                { cache: "no-store" }
            );

            const data = await response.json();

            if (!data.success) return;

            if (data.counter === lastCounter) return;

            lastCounter = data.counter;

            if (data.command === "play") {
                try {
                    await player.play();
                } catch (error) {
                    console.error("Party Start:", error);
                }
            }

            if (data.command === "pause") {
                player.pause();
            }

        } catch (error) {
            console.error("Party-Steuerung:", error);
        }
    }


    async function sendReceiverStatus() {

        try {

            const artist =
                document.getElementById("songArtist");

            const title =
                document.getElementById("songTitle");

            const params = new URLSearchParams();

            params.set(
                "playing",
                player.paused ? "0" : "1"
            );

            params.set(
                "current",
                Number.isFinite(player.currentTime)
                    ? player.currentTime
                    : 0
            );

            params.set(
                "duration",
                Number.isFinite(player.duration)
                    ? player.duration
                    : 0
            );

            params.set(
                "artist",
                artist ? artist.textContent : ""
            );

            params.set(
                "title",
                title ? title.textContent : ""
            );

            await fetch(
                "/receiver_status_update?" +
                params.toString(),
                { cache: "no-store" }
            );

        } catch (error) {
            console.error("Receiver Status:", error);
        }
    }


    setInterval(checkPartyControl, 300);
    setInterval(sendReceiverStatus, 500);

    checkPartyControl();
    sendReceiverStatus();

})();
