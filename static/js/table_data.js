document.addEventListener("DOMContentLoaded", function () {
    const pageNumberInput = document.getElementById("pageNumberInput");
    const goToPageButton = document.getElementById("goToPageButton");

    goToPageButton.addEventListener("click", function () {
        const page = pageNumberInput.value;
        const maxPage = parseInt(pageNumberInput.max);
        if (page < 1 || page > maxPage) {
            alert(`Введите номер страницы от 1 до ${maxPage}`);
            return;
        }
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set("page", page);
        window.location.search = urlParams.toString();
    });

    pageNumberInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            goToPageButton.click();
            event.preventDefault();
        }
    });
});