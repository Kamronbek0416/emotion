const form = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const resultDiv = document.getElementById('result');
const outputImage = document.getElementById('outputImage');

let lastResult = null; // Для хранения данных анализа

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const file = fileInput.files[0];
    if (!file) {
        resultDiv.textContent = 'Пожалуйста, выберите файл перед анализом.';
        return;
    }
    const formData = new FormData();
    formData.append('image', file);

    document.getElementById('spinner').classList.remove('d-none');
    resultDiv.textContent = 'Обработка изображения...';

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData,
        });
        const data = await response.json();
        if (data.error) {
            resultDiv.textContent = `Ошибка: ${data.error}`;
            document.getElementById('spinner').classList.add('d-none');
            return;
        }

        if (data.results && data.results.length > 0) {
            let resultHTML = '<h2 style="text-align: center; margin-bottom: 20px;">Распознанные эмоции:</h2>';
            data.results.forEach((result, index) => {
                resultHTML += `<div style="margin-top: 10px;"><div><strong>Лицо ${index + 1}:</strong></div>`;
                resultHTML += `<div style="margin-left: 15px;">Доминирующая эмоция: ${result.dominant_emotion} (${result.confidence.toFixed(2)}%)<br>`;
                for (const [emotion, probability] of Object.entries(result.emotions)) {
                    resultHTML += `${emotion}: ${probability.toFixed(2)}%<br>`;
                }
                resultHTML += '</div></div><br>';
            });
            resultHTML += '<button id="saveButton" class="btn btn-success mt-3">Сохранить результат</button>';
            resultDiv.innerHTML = resultHTML;

            lastResult = data; // Сохраняем данные для последующего использования (включая file_path)

            document.getElementById('saveButton').addEventListener('click', async () => {
                try {
                    const saveResponse = await fetch('/save_result', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(lastResult),
                    });
                    const saveData = await saveResponse.json();
                    if (saveData.success) {
                        resultDiv.innerHTML += '<p class="text-success">Результат сохранен!</p>';
                    } else {
                        resultDiv.innerHTML += '<p class="text-danger">Ошибка при сохранении.</p>';
                    }
                } catch (error) {
                    resultDiv.innerHTML += `<p class="text-danger">Ошибка: ${error.message}</p>`;
                }
            });
        } else {
            resultDiv.textContent = 'Лица не обнаружены на изображении.';
        }

        document.getElementById('spinner').classList.add('d-none');

        if (data.result_image_url) {
            outputImage.src = data.result_image_url;
            outputImage.style.maxWidth = '500px';
            outputImage.style.height = 'auto';
            outputImage.classList.remove('d-none');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        resultDiv.textContent = `Ошибка анализа: ${error.message}`;
        document.getElementById('spinner').classList.add('d-none');
    }
});