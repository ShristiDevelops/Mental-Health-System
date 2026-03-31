let lastState = "";

const video = document.getElementById("video");
const liveScore = document.getElementById("liveScore");
const downloadBtn = document.getElementById("downloadBtn");

let currentScore = 0;
let cameraStarted = false;

// Start webcam
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
    } catch (err) {
        alert("Camera access denied!");
    }
}

startCamera();

// Wait until video loads
video.addEventListener("loadeddata", () => {

    if (cameraStarted) return;
    cameraStarted = true;

    const faceMesh = new FaceMesh({
        locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
        }
    });

    faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });

    faceMesh.onResults(results => {

        if (results.multiFaceLandmarks.length > 0) {

            const landmarks = results.multiFaceLandmarks[0];

            const top = landmarks[13];
            const bottom = landmarks[14];
            const left = landmarks[61];
            const right = landmarks[291];

            const mouthHeight = Math.abs(bottom.y - top.y);
            const mouthWidth = Math.abs(right.x - left.x);

            const mar = mouthHeight / mouthWidth;

            // 🎯 Smooth Detection Logic
            let isSmiling = mar > 0.07;

            if (isSmiling && lastState !== "smile") {
                currentScore++;
                lastState = "smile";
            }

            if (!isSmiling) {
                lastState = "neutral";
            }

            liveScore.innerText =
                (isSmiling ? "😊 Smiling" : "😐 Not Smiling") +
                " | Score: " + currentScore;

        } else {
            liveScore.innerText = "No Face Detected 😶";
        }
    });

    const camera = new Camera(video, {
        onFrame: async () => {
            await faceMesh.send({ image: video });
        },
        width: 640,
        height: 480
    });

    camera.start();
});


// Capture Photo
function capturePhoto() {

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.drawImage(video, 0, 0);

    const imageData = canvas.toDataURL("image/png");

    fetch("/save_image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            image: imageData,
            score: currentScore
        })
    })
    .then(() => {
        // Send score in URL
        window.location.href = "/result?score=" + currentScore;
    });
}
