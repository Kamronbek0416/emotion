let videoStream;
let intervalId;

async function startRealTime() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoStream = stream;
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const realTimeResult = document.getElementById('realTimeResult');

        video.srcObject = stream;
        video.classList.remove('hidden');

        if (intervalId) clearInterval(intervalId);

        intervalId = setInterval(() => {
            const ctx = canvas.getContext('2d');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            canvas.toBlob(blob => {
                const formData = new FormData();
                formData.append('image', blob, 'frame.jpg');

                fetch('/analyze_realtime', { method: 'POST', body: formData })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            realTimeResult.innerText = `Ошибка: ${data.error}`;
                            realTimeResult.style.color = '#E74C3C';
                        } else if (data.results && data.results.length > 0) {
                            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                            data.results.forEach(result => {
                                const { region, dominant_emotion, confidence } = result;

                                const x = region.x;
                                const y = region.y;
                                const w = region.w;
                                const h = region.h;

                                const emotionColors = {
                                    happy: "#F1C40F",
                                    sad: "#3498DB",
                                    angry: "#E74C3C",
                                    surprise: "#9B59B6",
                                    neutral: "#2ECC71",
                                    fear: "#E67E22",
                                    disgust: "#95A5A6"
                                };

                                const boxColor = emotionColors[dominant_emotion] || "#FFFFFF";

                                ctx.strokeStyle = boxColor;
                                ctx.lineWidth = 2;
                                ctx.strokeRect(x, y, w, h);

                                ctx.fillStyle = boxColor;
                                ctx.font = '16px Arial';
                                ctx.fillText(`${dominant_emotion} (${confidence.toFixed(2)}%)`, x, y - 5);
                            });

                            realTimeResult.innerText = data.results.map(result =>
                                `${result.dominant_emotion} (${result.confidence.toFixed(2)}%)`
                            ).join(', ');
                            realTimeResult.style.color = '#27AE60';
                        } else {
                            realTimeResult.innerText = 'Лица не обнаружены.';
                            realTimeResult.style.color = '#E74C3C';
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка:', error);
                        realTimeResult.innerText = `Ошибка анализа: ${error.message}`;
                        realTimeResult.style.color = '#E74C3C';
                    });
            }, 'image/jpeg');
        }, 2000);
    } catch (error) {
        console.error("Ошибка реального времени:", error);
        const realTimeResult = document.getElementById('realTimeResult');
        realTimeResult.innerText = "Ошибка доступа к камере";
        realTimeResult.style.color = "#E74C3C";
    }
}

function stopRealTime() {
    const video = document.getElementById('video');
    const realTimeResult = document.getElementById('realTimeResult');

    if (videoStream) {
        const tracks = videoStream.getTracks();
        tracks.forEach(track => track.stop());
        videoStream = null;
    }
    video.classList.add('hidden');
    realTimeResult.innerText = 'Анализ остановлен.';
    realTimeResult.style.color = '#34495E';

    if (intervalId) clearInterval(intervalId);
}