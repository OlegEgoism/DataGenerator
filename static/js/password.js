document.addEventListener("DOMContentLoaded", function () {
    // Функция для инициализации переключения видимости пароля
    function setupPasswordToggle(toggleId, passwordId) {
        const toggleButton = document.querySelector(`#${toggleId}`);
        const passwordField = document.querySelector(`#${passwordId}`);
        const icon = toggleButton.querySelector("i");

        if (!toggleButton || !passwordField || !icon) {
            console.warn(`Элементы для ${toggleId} не найдены.`);
            return;
        }

        toggleButton.addEventListener("click", function () {
            const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
            passwordField.setAttribute("type", type);

            if (type === "password") {
                icon.classList.remove("bi-eye-slash");
                icon.classList.add("bi-eye");
            } else {
                icon.classList.remove("bi-eye");
                icon.classList.add("bi-eye-slash");
            }
        });
    }

    // Инициализация для всех полей
    setupPasswordToggle("togglePassword", "id_password");   // Вход
    setupPasswordToggle("togglePassword1", "id_password1"); // Пароль
    setupPasswordToggle("togglePassword2", "id_password2"); // Подтверждение
});