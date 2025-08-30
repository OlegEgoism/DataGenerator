document.addEventListener("DOMContentLoaded", function () {
    function setupPasswordToggle(toggleId, passwordId) {
        const toggleButton = document.querySelector(`#${toggleId}`);
        const passwordField = document.querySelector(`#${passwordId}`);
        const icon = toggleButton ? toggleButton.querySelector("i") : null;

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

// Вход
    setupPasswordToggle("togglePassword", "id_password");
// Регистрация
    setupPasswordToggle("togglePassword1", "id_password1");
    setupPasswordToggle("togglePassword2", "id_password2");
// Создание проекта
    setupPasswordToggle("toggleDbPassword", "id_db_password");
// Редактирование проекта
    setupPasswordToggle("toggleDbPasswordEdit", "id_db_password");
});
