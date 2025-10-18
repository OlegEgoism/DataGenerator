(function () {
    let idx = 0;
    const columnsWrap = document.getElementById('columns');
    const addBtn = document.getElementById('addColumn');
    const isClickHouse = window.APP_ENGINE === 'clickhouse';

    function rowTemplate(i, isCH = false) {
        // Поле "Комментарий" только для PostgreSQL
        const commentBlock = isCH ? '' : `
      <div class="col-md-3">
        <label class="form-label mb-1"><strong>Комментарий</strong></label>
        <input type="text" class="form-control"
               name="column_comment_${i}" placeholder="Описание столбца">
      </div>
    `;

        const typeCol = isCH ? 'col-md-4' : 'col-md-3';
        const uniqueCol = isCH ? 'col-md-2' : 'col-md-1';
        const deleteCol = isCH ? 'col-md-2' : 'col-md-1';

        // Типы данных: адаптированы под СУБД
        const typeOptions = isCH ? `
          <option value="INTEGER">Целое (INTEGER)</option>
          <option value="BIGINT">Большое целое (BIGINT)</option>
          <option value="BOOLEAN">Логический (BOOLEAN)</option>
          <option value="VARCHAR(255)">Строка (VARCHAR(255))</option>
          <option value="TEXT">Текст (TEXT)</option>
          <option value="DATE">Дата (DATE)</option>
          <option value="TIMESTAMP">Дата/время (TIMESTAMP)</option>
          <option value="FLOAT">Float (FLOAT)</option>
          <option value="DOUBLE PRECISION">Double (DOUBLE PRECISION)</option>
        ` : `
          <option value="SMALLINT">Малое целое (SMALLINT)</option>
          <option value="INTEGER">Целое (INTEGER)</option>
          <option value="BIGINT">Большое целое (BIGINT)</option>
          <option value="SERIAL">Автоинкремент (SERIAL)</option>
          <option value="BIGSERIAL">Автоинкремент большой (BIGSERIAL)</option>
          <option value="REAL">Real (REAL)</option>
          <option value="DOUBLE PRECISION">Double (DOUBLE PRECISION)</option>
          <option value="FLOAT">Float (синоним DOUBLE PRECISION)</option>
          <option value="NUMERIC">Числовой (NUMERIC)</option>
          <option value="BOOLEAN">Логический (BOOLEAN)</option>
          <option value="CHAR(1)">Фикс. строка (CHAR(1))</option>
          <option value="VARCHAR(255)">Строка (VARCHAR(255))</option>
          <option value="TEXT">Текст (TEXT)</option>
          <option value="DATE">Дата (DATE)</option>
          <option value="TIME">Время (TIME)</option>
          <option value="TIMESTAMP">Дата/время (TIMESTAMP)</option>
          <option value="TIMESTAMPTZ">Дата/время c TZ (TIMESTAMPTZ)</option>
          <option value="UUID">UUID</option>
          <option value="JSONB">JSONB</option>
          <option value="BYTEA">Двоичные данные (BYTEA)</option>
        `;

        return `
        <div class="row g-2 align-items-start column-row border rounded p-2">
          <input type="hidden" name="row_indices[]" value="${i}">

          <div class="col-md-3">
            <label class="form-label mb-1"><strong>Столбец</strong></label>
            <input type="text" class="form-control"
                   name="column_name_${i}" required
                   pattern="^[a-zA-Z_][a-zA-Z0-9_]*$" maxlength="63"
                   placeholder="Название">
          </div>

          <div class="${typeCol}">
            <label class="form-label mb-1"><strong>Тип</strong></label>
            <select class="form-select" name="column_type_${i}">
              ${typeOptions}
            </select>
          </div>

          ${commentBlock}
          ${isCH ? '' : `
          <div class="${uniqueCol}">
            <label class="form-label mb-1"><strong>Уник</strong></label>
            <div class="form-check pt-1">
              <input class="form-check-input" type="checkbox" name="column_unique_${i}" ${isCH ? 'disabled title="UNIQUE не поддерживается в ClickHouse"' : ''}>
            </div>
          </div>
          `}

          <div class="${deleteCol}">
            <label class="form-label mb-1"><strong>Удалить</strong></label>
            <div class="text-end">
              <button type="button" class="btn btn-outline-danger remove-column" title="Удалить столбец">
                <i class="bi bi-x-lg"></i>
              </button>
            </div>
          </div>
        </div>`;
    }

    function addRow(prefill = {}) {
        const i = idx++;
        const wrapper = document.createElement('div');
        wrapper.innerHTML = rowTemplate(i, isClickHouse);
        const rowEl = wrapper.firstElementChild;

        if (prefill.name) rowEl.querySelector(`[name="column_name_${i}"]`).value = prefill.name;
        if (prefill.type) rowEl.querySelector(`[name="column_type_${i}"]`).value = prefill.type;
        if (!isClickHouse && prefill.comment) rowEl.querySelector(`[name="column_comment_${i}"]`).value = prefill.comment;
        if (prefill.unique && !isClickHouse) rowEl.querySelector(`[name="column_unique_${i}"]`).checked = true;

        rowEl.querySelector('.remove-column').addEventListener('click', () => rowEl.remove());
        columnsWrap.appendChild(rowEl);
    }

    const form = document.getElementById('createTableForm');
    if (form) {
        form.addEventListener('submit', function (e) {
            const names = Array.from(form.querySelectorAll('[name^="column_name_"]'))
                .map(inp => (inp.value || '').trim().toLowerCase())
                .filter(Boolean);

            const duplicates = names.filter((n, i) => names.indexOf(n) !== i);
            if (duplicates.length) {
                e.preventDefault();
                alert(`Дублирующиеся имена столбцов: ${[...new Set(duplicates)].join(', ')}.`);
                return false;
            }
        });
    }

    if (addBtn) addBtn.addEventListener('click', () => addRow());

    addRow();
    addRow();
})();