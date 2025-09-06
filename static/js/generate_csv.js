// ---- вспомогалки ----
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function humanSize(bytes) {
    if (!bytes && bytes !== 0) return '—';
    const units = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ'];
    let i = 0, val = bytes;
    while (val >= 1024 && i < units.length - 1) {
        val /= 1024;
        i++;
    }
    return (Math.round(val * 10) / 10) + ' ' + units[i];
}

function parseFilenameFromCD(cdHeader) {
    if (!cdHeader) return null;
    const m = cdHeader.match(/filename\*?=([^;]+)/i);
    if (!m) return null;
    let v = m[1].trim();
    // RFC5987 filename*=
    if (v.startsWith("UTF-8''")) {
        try {
            return decodeURIComponent(v.substring(7));
        } catch {
            return v.substring(7);
        }
    }
    return v.replace(/^"+|"+$/g, '');
}

// ---- UI логика ----
document.addEventListener('DOMContentLoaded', function () {
    const $sortable = $('#sortable').sortable({placeholder: 'ui-state-highlight'}).disableSelection();
    const fieldMap = new Map(); // value -> <li>

    // добавление/удаление элементов в sortable при клике по чекбоксу
    $('.field-checkbox').on('change', function () {
        const value = this.dataset.value;
        if (this.checked) {
            if (!fieldMap.has(value)) {
                const li = document.createElement('li');
                li.className = 'sortable-item';
                li.dataset.field = value;
                li.innerHTML = `
              <span>${value}</span>
              <button type="button" class="remove-item btn btn-sm text-danger" title="Убрать">
                <i class="bi bi-x-lg"></i>
              </button>`;
                li.querySelector('.remove-item').addEventListener('click', () => {
                    li.remove();
                    fieldMap.delete(value);
                    // снять чекбокс
                    const cb = document.querySelector('.field-checkbox[data-value="' + CSS.escape(value) + '"]');
                    if (cb) cb.checked = false;
                });
                $sortable.append(li);
                fieldMap.set(value, li);
            }
        } else {
            const li = fieldMap.get(value);
            if (li) {
                li.remove();
                fieldMap.delete(value);
            }
        }
    });

    // сабмит через fetch с Blob-скачиванием
    const form = document.getElementById('csvForm');
form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const fields = Array.from(document.querySelectorAll('#sortable .sortable-item'))
        .map(li => li.dataset.field);
    if (!fields.length) {
        alert('Выберите хотя бы одно поле и добавьте его в список.');
        return;
    }
    const numEl = document.getElementById('num_records');
    const num = Math.max(1, Math.min(parseInt(numEl.value || '1', 10), 10000000));
    numEl.value = num;

    const progressModal = new bootstrap.Modal(document.getElementById('progressModal'));
    const resultModal = new bootstrap.Modal(document.getElementById('resultModal'));
    progressModal.show();

    try {
        const fd = new FormData();
        fd.append('num_records', String(num));
        fields.forEach(f => fd.append('fields', f));

        const csrftoken = getCookie('csrftoken');
        const resp = await fetch(window.location.href, {
            method: 'POST',
            body: fd,
            headers: {'X-CSRFToken': csrftoken},
            credentials: 'same-origin',
        });

        if (!resp.ok) {
            const text = await resp.text();
            throw new Error(text || resp.statusText);
        }

        const blob = await resp.blob();
        const cd = resp.headers.get('Content-Disposition');
        const fname = parseFilenameFromCD(cd) || 'fake_data.csv';

        // Скачивание
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fname;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

        // Показ результата
        document.getElementById('resFileName').textContent = fname;
        document.getElementById('resRows').textContent = num.toLocaleString('ru-RU');
        document.getElementById('resCols').textContent = fields.length;
        document.getElementById('resSize').textContent = humanSize(blob.size);
        resultModal.show();

    } catch (err) {
        alert('Не удалось сформировать файл: ' + (err?.message || err));
    } finally {
        progressModal.hide();  // ← Гарантированно закроется
    }
});
});