import random
import re

from faker import Faker

# Регулярное выражение для валидации имён колонок
IDENT_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Все возможные "маркеры" для генерации данных
ALL_CHOICES = [
    "ФИО", "Фамилия", "Имя", "Отчество", "Логин", "Дата рождения", "Возраст", "Пол",
    "Страна", "Город", "Адрес", "Почтовый индекс", "Email", "Телефон", "Широта", "Долгота", "Число с запятой",
    "Компания", "Категория продукта", "Должность", "Отдел",
    "Валюта", "Символ валюты", "Кредитная карта", "IBAN",
    "Случайный текст (до 100 букв)", "Заголовок", "Цвет", "Рейтинг (1-5)", "Цена",
    "Пароль", "IP-адрес", "Домен", "URL", "URI",
    "UUID", "Число (большое)", "Число (маленькое)", "True/False", "Случайный хэш", "JSON-объект",
    "Дата", "Время", "Дата и время", "Временная зона", "Дата в прошлом", "Дата в будущем",
    "Профессия", "Животное", "Еда", "Язык программирования", "Устройство", "Социальная сеть",
    "Статус", "Файл", "MIME-тип", "Паспорт", "ИНН", "СНИЛС", "Автомобильный номер", "Номер счёта",
    "Номер рейса", "Погода", "Метрика", "Оценка (1-10)", "Комментарий", "Тег", "Навык", "Уровень",
    "Название курса", "Формат файла", "Код страны", "Код региона", "Почтовый ящик", "Номер отделения",
    "Тип документа", "Номер договора", "Название проекта", "Команда", "Роль в команде"
]

# === СОПОСТАВЛЕНИЕ ТИПОВ PostgreSQL → ДОПУСТИМЫЕ ЗНАЧЕНИЯ ===
# Ключи — точные строки из information_schema.columns.data_type
choices_list = {
    # 📝 Текстовые типы — поддерживают все форматы
    "text": ALL_CHOICES,
    "character varying": ALL_CHOICES,
    "character": ALL_CHOICES,
    "char": ["Пол"],  # Только короткие значения

    # 🔢 Числовые типы
    "smallint": ["Число (маленькое)", "Возраст", "Рейтинг (1-5)", "Оценка (1-10)"],
    "integer": ["Число (маленькое)", "Возраст", "Рейтинг (1-5)", "Оценка (1-10)"],
    "bigint": ["Число (большое)", "ИНН"],  # ❌ СНИЛС и Номер счёта — НЕТ! Это строки!
    "numeric": ["Цена", "Широта", "Долгота", "Метрика", "Число с запятой"],
    "real": ["Число с запятой", "Метрика"],
    "double precision": ["Число с запятой", "Широта", "Долгота", "Метрика"],

    # 🔀 Логический
    "boolean": ["True/False", "Статус активности"],

    # 📅 Дата/время
    "date": ["Дата", "Дата рождения", "Дата в прошлом", "Дата в будущем"],
    "time without time zone": ["Время"],
    "time": ["Время"],
    "timestamp without time zone": ["Дата и время", "Дата в прошлом", "Дата в будущем"],
    "timestamp with time zone": ["Дата и время", "Дата в прошлом", "Дата в будущем", "Временная зона"],

    # 🧩 Специальные типы
    "uuid": ["UUID"],
    "jsonb": ["JSON-объект"],
    "bytea": ["Файл"],

    # ⚠️ Явно разрешаем строки для форматированных данных
    # Эти типы будут выбираться при VARCHAR/TEXT
}

# === Поддерживаемые типы (для справки или валидации) ===
ALLOWED_TYPES = {
    "SMALLINT": "SMALLINT",
    "INTEGER": "INTEGER",
    "BIGINT": "BIGINT",
    "SERIAL": "SERIAL",
    "BIGSERIAL": "BIGSERIAL",
    "REAL": "REAL",
    "DOUBLE PRECISION": "DOUBLE PRECISION",
    "FLOAT": "DOUBLE PRECISION",
    "NUMERIC": "NUMERIC",
    "BOOLEAN": "BOOLEAN",
    "CHAR(1)": "CHAR(1)",
    "VARCHAR(255)": "VARCHAR(255)",
    "TEXT": "TEXT",
    "DATE": "DATE",
    "TIME": "TIME",
    "TIMESTAMP": "TIMESTAMP",
    "TIMESTAMPTZ": "TIMESTAMPTZ",
    "UUID": "UUID",
    "JSONB": "JSONB",
    "BYTEA": "BYTEA",
}


def generate_fake_value(column_name, selected_value, fake):
    """
    Генерирует случайное значение в зависимости от выбранного типа данных.
    Возвращает данные, совместимые с PostgreSQL.
    """
    try:
        if selected_value == 'ФИО':
            return fake.name()
        elif selected_value == 'Фамилия':
            return fake.last_name()
        elif selected_value == 'Имя':
            return fake.first_name()
        elif selected_value == 'Отчество':
            return fake.middle_name()
        elif selected_value == 'Логин':
            return fake.user_name()
        elif selected_value == 'Дата рождения':
            return fake.date_of_birth(minimum_age=1, maximum_age=90)
        elif selected_value == 'Возраст':
            return fake.random_int(min=1, max=100)
        elif selected_value == 'Пол':
            return fake.random_element(['Мужской', 'Женский'])
        elif selected_value == 'Страна':
            return fake.country()
        elif selected_value == 'Город':
            return fake.city()
        elif selected_value == 'Адрес':
            return fake.street_address()
        elif selected_value == 'Почтовый индекс':
            return fake.postcode()
        elif selected_value == 'Email':
            return fake.email()
        elif selected_value == 'Телефон':
            return fake.phone_number()
        elif selected_value == 'Широта':
            return fake.latitude()
        elif selected_value == 'Долгота':
            return fake.longitude()
        elif selected_value == 'Компания':
            return fake.company()
        elif selected_value == 'Категория продукта':
            return fake.word(ext_word_list=[
                'Электроника', 'Книги', 'Одежда', 'Игрушки', 'Мебель',
                'Транспорт', 'Косметика', 'Продукты', 'Медицина', 'Спорт'
            ])
        elif selected_value == 'Должность':
            return fake.job()
        elif selected_value == 'Отдел':
            return fake.bs()
        elif selected_value == 'Валюта':
            return fake.currency_name()
        elif selected_value == 'Символ валюты':
            return fake.currency_symbol()
        elif selected_value == 'Кредитная карта':
            return fake.credit_card_number()
        elif selected_value == 'IBAN':
            return fake.iban()
        elif selected_value == 'Случайный текст (до 100 букв)':
            return fake.text(max_nb_chars=100)
        elif selected_value == 'Заголовок':
            return fake.catch_phrase()
        elif selected_value == 'Рейтинг (1-5)':
            return fake.random_int(min=1, max=5)
        elif selected_value == 'Цена':
            return round(random.uniform(10, 10000), 2)
        elif selected_value == 'Цвет':
            return fake.color_name()
        elif selected_value == 'Пароль':
            return fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        elif selected_value == 'IP-адрес':
            return fake.ipv4()
        elif selected_value == 'Домен':
            return fake.domain_name()
        elif selected_value == 'URL':
            return fake.url()
        elif selected_value == 'URI':
            return fake.uri()
        elif selected_value == 'UUID':
            return fake.uuid4()
        elif selected_value == 'Число (большое)':
            # Максимум для BIGINT в PostgreSQL
            return fake.random_int(min=1_000_000, max=9_223_372_036_854_775_807)
        elif selected_value == 'Число (маленькое)':
            return fake.random_int(min=1, max=100)
        elif selected_value == 'True/False':
            return fake.boolean()
        elif selected_value == 'Случайный хэш':
            return fake.sha256()
        elif selected_value == 'JSON-объект':
            return fake.json(indent=2)
        elif selected_value == 'Дата':
            return fake.date()
        elif selected_value == 'Время':
            return fake.time()
        elif selected_value == 'Дата и время':
            return fake.date_time()
        elif selected_value == 'Временная зона':
            return fake.timezone()
        elif selected_value == 'Дата в прошлом':
            return fake.past_date()
        elif selected_value == 'Дата в будущем':
            return fake.future_date()
        elif selected_value == 'Число с запятой':
            return round(random.uniform(0.1, 10000.0), 2)
        elif selected_value == 'Профессия':
            return fake.job()
        elif selected_value == 'Животное':
            return fake.random_element([
                'Собака', 'Кошка', 'Попугай', 'Хомяк', 'Черепаха', 'Змея', 'Кролик', 'Рыба'
            ])
        elif selected_value == 'Еда':
            if hasattr(fake, 'dish'):
                return fake.dish()
            return fake.random_element([
                'Пицца', 'Суши', 'Бургер', 'Паста', 'Салат', 'Суп', 'Картошка', 'Стейк'
            ])
        elif selected_value == 'Язык программирования':
            return fake.random_element([
                'Python', 'JavaScript', 'Java', 'C++', 'Go', 'Rust', 'Ruby', 'PHP', 'Swift', 'Kotlin'
            ])
        elif selected_value == 'Устройство':
            return fake.random_element([
                'Смартфон', 'Ноутбук', 'Планшет', 'Часы', 'Наушники', 'Монитор'
            ])
        elif selected_value == 'Социальная сеть':
            return fake.random_element([
                'VK', 'Telegram', 'Instagram', 'Facebook', 'Twitter', 'LinkedIn', 'TikTok'
            ])
        elif selected_value == 'Статус':
            return fake.random_element(['Активен', 'Неактивен', 'Ожидание', 'Заблокирован', 'В сети'])
        elif selected_value == 'Файл':
            return fake.file_name()
        elif selected_value == 'MIME-тип':
            return fake.mime_type()
        elif selected_value == 'Паспорт':
            series = f"{fake.random_int(10, 99)} {fake.random_int(10, 99)}"
            number = fake.random_number(digits=6, fix_len=True)
            return f"{series} {number}"
        elif selected_value == 'ИНН':
            return str(fake.random_number(digits=12, fix_len=True))
        elif selected_value == 'СНИЛС':
            # Возвращаем строку: XXX-XXX-XXX XX
            n1 = fake.random_number(digits=3, fix_len=True)
            n2 = fake.random_number(digits=3, fix_len=True)
            n3 = fake.random_number(digits=3, fix_len=True)
            n4 = fake.random_number(digits=2, fix_len=True)
            return f"{n1}-{n2}-{n3} {n4}"
        elif selected_value == 'Автомобильный номер':
            letter = fake.random_uppercase_letter()
            digits = fake.random_number(digits=3, fix_len=True)
            region = fake.random_int(1, 99)
            return f"А{letter}{digits}{region}"
        elif selected_value == 'Номер счёта':
            # Всегда строка: 20 цифр
            return ''.join([str(fake.random_digit()) for _ in range(20)])
        elif selected_value == 'Номер рейса':
            airline = fake.lexify('??').upper()
            number = fake.random_number(digits=4)
            return f"{airline}{number}"
        elif selected_value == 'Погода':
            return fake.random_element(['Солнечно', 'Дождь', 'Облачно', 'Снег', 'Туман', 'Гроза'])
        elif selected_value == 'Метрика':
            return round(random.uniform(0.0, 1000.0), 3)
        elif selected_value == 'Оценка (1-10)':
            return fake.random_int(min=1, max=10)
        elif selected_value == 'Комментарий':
            return fake.sentence(nb_words=10)
        elif selected_value == 'Тег':
            return f"#{fake.word()}"
        elif selected_value == 'Навык':
            return fake.job()
        elif selected_value == 'Уровень':
            return fake.random_element(['Начинающий', 'Средний', 'Опытный', 'Эксперт'])
        elif selected_value == 'Название курса':
            return fake.catch_phrase()
        elif selected_value == 'Формат файла':
            return fake.file_extension()
        elif selected_value == 'Код страны':
            return fake.country_code()
        elif selected_value == 'Код региона':
            return fake.random_int(1, 99)
        elif selected_value == 'Почтовый ящик':
            return fake.random_int(1, 999)
        elif selected_value == 'Номер отделения':
            return f"Отдел-{fake.random_int(1, 50)}"
        elif selected_value == 'Тип документа':
            return fake.random_element(['Паспорт', 'Удостоверение', 'Договор', 'Справка', 'Заявление'])
        elif selected_value == 'Номер договора':
            num = fake.random_number(digits=6, fix_len=True)
            return f"ДОГ-{num}"
        elif selected_value == 'Название проекта':
            return fake.bs()
        elif selected_value == 'Команда':
            return f"{fake.company()} Команда"
        elif selected_value == 'Роль в команде':
            return fake.random_element(['Разработчик', 'Тестировщик', 'Аналитик', 'Менеджер', 'Дизайнер'])
        else:
            return fake.text(max_nb_chars=20)

    except Exception as e:
        # На случай непредвиденных ошибок в Faker
        return f"err_{str(e)[:20]}"