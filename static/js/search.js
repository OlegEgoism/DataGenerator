document.addEventListener("DOMContentLoaded", function () {
    let searchInput = document.getElementById("searchInput");
    let clearButton = document.getElementById("clearSearch");
    let pageInput = document.getElementById("pageInput");
    let goToPageButton = document.getElementById("goToPageButton");

    function toggleClearButton() {
        clearButton.style.display = searchInput.value.length > 0 ? "inline-block" : "none";
    }

    clearButton.addEventListener("click", function () {
        searchInput.value = "";
        document.querySelector("form").submit();
    });

    toggleClearButton();
    searchInput.addEventListener("input", toggleClearButton);

    // Обработчик кнопки "Перейти"
    goToPageButton.addEventListener("click", function () {
        let page = pageInput.value;
        let maxPage = parseInt(pageInput.max);
        if (page < 1 || page > maxPage) {
            alert(`Введите номер страницы от 1 до ${maxPage}`);
            return;
        }
        let urlParams = new URLSearchParams(window.location.search);
        urlParams.set("page", page);
        window.location.search = urlParams.toString();
    });

    // Переход по Enter
    pageInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            goToPageButton.click();
            event.preventDefault();
        }
    });
});