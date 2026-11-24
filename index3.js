// Клиентская проверка форм входа / регистрации.
// Сами данные отправляет браузер обычным POST-запросом на Flask (backend.py).
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form.border');
    if (!form) return;

    const password = form.querySelector('input[name="password"]');
    const confirm = form.querySelector('input[name="confirm_password"]');

    form.addEventListener('submit', (e) => {
        if (password && confirm && password.value !== confirm.value) {
            e.preventDefault();
            showMessage('Passwords do not match.');
            confirm.focus();
        }
    });

    function showMessage(text) {
        let box = form.querySelector('.form-message.js-message');
        if (!box) {
            box = document.createElement('p');
            box.className = 'form-message js-message';
            form.querySelector('h1').after(box);
        }
        box.textContent = text;
    }
});
