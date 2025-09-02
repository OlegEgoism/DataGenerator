import random

choices_list = {
    "text": [
        "ФИО", "Фамилия", "Имя", "Отчество", "Логин", "Дата рождения", "Возраст", "Пол",
        "Страна", "Город", "Адрес", "Почтовый индекс", "Email", "Телефон", "Широта", "Долгота", "Число с запятой",
        "Компания", "Категория продукта", "Должность", "Отдел",
        "Валюта", "Символ валюты", "Кредитная карта", "IBAN",
        "Случайный текст (до 100 букв)", "Заголовок", "Цвет", "Рейтинг (1-5)", "Цена",
        "Пароль", "IP-адрес", "Домен", "URL", "URI",
        "UUID", "Число (большое)", "Число (маленькое)", "True/False", "Случайный хэш", "JSON-объект",
        "Дата", "Время", "Дата и время", "Временная зона", "Дата в прошлом", "Дата в будущем"
    ],
    "character varying": [
        'ФИО', 'Фамилия', 'Имя', 'Отчество', 'Логин', 'Пол',
        'Страна', 'Город', 'Адрес', 'Почтовый индекс', 'Email',
        'Телефон', 'Компания', 'Категория продукта', 'Должность',
        'Отдел', 'Валюта', 'Символ валюты', 'Кредитная карта',
        'IBAN', 'Случайный текст (до 100 букв)', 'Заголовок',
        'Цвет', 'Пароль', 'IP-адрес', 'Домен', 'URL', 'URI',
        'UUID', 'Случайный хэш', 'JSON-объект', 'Временная зона'
    ],
    "uuid": ["UUID"],
    "integer": ["Число (большое)"],
    "smallint": ["Число (маленькое)"],
    "bigint": ["Число (большое)"],
    "boolean": ["True/False"],
    "numeric": [
        "Возраст", "Широта", "Долгота",
        "Рейтинг (1-5)", "Цена"
    ],
    "double precision": [
        "Широта", "Долгота", "Число с запятой"
    ],
    "date": [
        "Дата рождения", "Дата", "Время", "Дата и время",
        "Временная зона", "Дата в прошлом", "Дата в будущем"
    ],
    "timestamp with time zone": [
        'Дата', 'Время', 'Дата и время',
        'Дата в прошлом', 'Дата в будущем'
    ],
    "jsonb": ["JSON-объект", ]
}


def generate_fake_value(column_name, selected_value, fake):
    """Генерирует случайное значение в зависимости от выбранного типа данных"""
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
        return fake.date_of_birth(minimum_age=18, maximum_age=90)
    elif selected_value == 'Возраст':
        return fake.random_int(min=18, max=90)
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
        return fake.unique.email()
    elif selected_value == 'Телефон':
        return fake.phone_number()
    elif selected_value == 'Широта':
        return fake.latitude()
    elif selected_value == 'Долгота':
        return fake.longitude()
    elif selected_value == 'Компания':
        return fake.company()
    elif selected_value == 'Категория продукта':
        return fake.word(ext_word_list=['Электроника', 'Книги', 'Одежда', 'Игрушки', 'Мебель', 'Транспорт'])
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
        return fake.text()
    elif selected_value == 'Заголовок':
        return fake.catch_phrase()
    elif selected_value == 'Рейтинг (1-5)':
        return fake.random_int(min=1, max=5)
    elif selected_value == 'Цена':
        return fake.random_number(digits=5)
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
        return fake.random_int(min=1, max=9000000)
    elif selected_value == 'True/False':
        return fake.boolean()
    elif selected_value == 'Случайный хэш':
        return fake.sha256()
    elif selected_value == 'JSON-объект':
        return fake.json()
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
    else:
        return None


