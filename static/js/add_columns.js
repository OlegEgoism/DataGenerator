(function () {
    let idx = 0;
    const wrap = document.getElementById('newColumnsWrap');
    const addBtn = document.getElementById('addColumnRow');
    const form = document.getElementById('addColumnsForm');

    function rowTemplate(i) {
        return `
        <div class="row g-2 align-items-start border rounded p-2 column-new-row">
          <input type="hidden" name="row_indices[]" value="${i}">

          <div class="col-md-3">
            <label class="form-label mb-1"><strong>Столбец</strong></label>
            <input type="text" class="form-control"
                   name="col_name_${i}" required
                   pattern="^[a-zA-Z_][a-zA-Z0-9_]*$" maxlength="63"
                   placeholder="column_name">
          </div>

          <div class="col-md-4">
            <label class="form-label mb-1"><strong>Тип</strong></label>
            <select class="form-select" name="col_type_${i}">
              <option value="SMALLINT">SMALLINT</option>
              <option value="INTEGER">INTEGER</option>
              <option value="BIGINT">BIGINT</option>

              <option value="SERIAL">SERIAL</option>
              <option value="BIGSERIAL">BIGSERIAL</option>

              <option value="REAL">REAL</option>
              <option value="DOUBLE PRECISION">DOUBLE PRECISION</option>
              <option value="FLOAT">FLOAT</option>
              <option value="NUMERIC">NUMERIC</option>

              <option value="BOOLEAN">BOOLEAN</option>

              <option value="CHAR(1)">CHAR(1)</option>
              <option value="VARCHAR(255)">VARCHAR(255)</option>
              <option value="TEXT">TEXT</option>

              <option value="DATE">DATE</option>
              <option value="TIME">TIME</option>
              <option value="TIMESTAMP">TIMESTAMP</option>
              <option value="TIMESTAMPTZ">TIMESTAMPTZ</option>

              <option value="UUID">UUID</option>
              <option value="JSONB">JSONB</option>
              <option value="BYTEA">BYTEA</option>
            </select>
          </div>

          <div class="col-md-3">
            <label class="form-label mb-1"><strong>Комментарий</strong></label>
            <input type="text" class="form-control"
                   name="col_comment_${i}" placeholder="описание столбца">
          </div>

          <div class="col-md-1">
            <label class="form-label mb-1"><strong>Уник</strong></label>
            <div class="form-check pt-1">
              <input class="form-check-input" type="checkbox" name="col_unique_${i}">
            </div>
          </div>

          <div class="col-md-1">
            <label class="form-label mb-1"><strong>Удалить</strong></label>
            <div class="text-end">
              <button type="button" class="btn btn-outline-danger btn-sm remove-col-row" title="Удалить строку">
                <i class="bi bi-x-lg"></i>
              </button>
            </div>
          </div>
        </div>`;
    }

    function addRow(prefill = {}) {
        const i = idx++;
        const el = document.createElement('div');
        el.innerHTML = rowTemplate(i);
        const row = el.firstElementChild;

        if (prefill.name) row.querySelector(`[name="col_name_${i}"]`).value = prefill.name;
        if (prefill.type) row.querySelector(`[name="col_type_${i}"]`).value = prefill.type;
        if (prefill.comment) row.querySelector(`[name="col_comment_${i}"]`).value = prefill.comment;
        if (prefill.unique) row.querySelector(`[name="col_unique_${i}"]`).checked = !!prefill.unique;

        row.querySelector('.remove-col-row').addEventListener('click', () => row.remove());
        wrap.appendChild(row);
    }

    // Клиентская проверка: уникальные имена столбцов (как на create-странице)
    form.addEventListener('submit', function (e) {
        const names = Array.from(form.querySelectorAll('[name^="col_name_"]'))
            .map(i => (i.value || '').trim().toLowerCase())
            .filter(Boolean);
        const dups = names.filter((n, i) => names.indexOf(n) !== i);
        if (dups.length) {
            e.preventDefault();
            const uniq = [...new Set(dups)];
            alert(`Дублирующиеся имена столбцов: ${uniq.join(', ')}. Имена столбцов должны быть уникальными.`);
            return false;
        }
    });

    // стартовые строки и кнопка «Добавить строку»
    addRow();
    addRow();
    addBtn.addEventListener('click', () => addRow());
})();