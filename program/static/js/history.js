document.querySelectorAll('.delete-btn').forEach(button => {
    button.addEventListener('click', async () => {
        const resultId = button.getAttribute('data-id');
        if (confirm('Вы уверены, что хотите удалить этот результат?')) {
            try {
                const response = await fetch(`/delete_result/${resultId}`, {
                    method: 'POST',
                });
                const data = await response.json();
                if (data.success) {
                    button.closest('.col-lg-6').remove(); // Удаляем карточку из DOM
                } else {
                    alert('Ошибка при удалении: ' + data.error);
                }
            } catch (error) {
                alert('Ошибка: ' + error.message);
            }
        }
    });
});