function showPassword() {
    let passwordField = document.getElementById('password');
    let eyeIcon = document.getElementById('eyeIcon');
    let password = passwordField.getAttribute('data-password');

    if (passwordField.textContent === '******') {
        passwordField.textContent = password;
        eyeIcon.classList.remove('bi-eye');
        eyeIcon.classList.add('bi-eye-slash');
    } else {
        passwordField.textContent = '******';
        eyeIcon.classList.remove('bi-eye-slash');
        eyeIcon.classList.add('bi-eye');
    }
}


function togglePassword() {
    let passwordInput = document.getElementById('id_db_password');
    let toggleIcon = document.getElementById('togglePasswordIcon');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.remove('bi-eye');
        toggleIcon.classList.add('bi-eye-slash');
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.remove('bi-eye-slash');
        toggleIcon.classList.add('bi-eye');
    }
}


$(function () {
    $("#sortable").sortable();
    $("#sortable").disableSelection();

    $(".field-checkbox").on("change", function () {
        const fieldValue = $(this).val();
        const fieldId = $(this).attr("id");

        if ($(this).is(":checked")) {
            const listItem = `
                        <li class="sortable-item" data-value="${fieldValue}">
                            ${fieldValue}
                            <input type="hidden" name="fields" value="${fieldValue}">
                        </li>`;
            $("#sortable").append(listItem);
        } else {
            $(`#sortable li[data-value="${fieldValue}"]`).remove();
        }
    });
});