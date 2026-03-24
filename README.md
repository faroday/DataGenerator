# DataGenerator

Desktop-приложение для генерации синтетических данных в базы данных.

## Возможности

- **Подключение к БД**: PostgreSQL, MySQL, SQLite
- **Анализ структуры**: автоматическое определение таблиц, колонок и связей
- **Умное определение паттернов**: анализ существующих данных для генерации похожих
- **Гибкая настройка**: выбор паттерна для каждой колонки через выпадающий список
- **Поддержка FK-связей**: генерация с учётом foreign keys
- **GUI на PyQt6**: интуитивный интерфейс

## Установка

```bash
cd datagenerator
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Запуск

```bash
source venv/bin/activate
python3 main.py
```

## Использование

### 1. Подключение к базе данных

1. Выберите тип БД (SQLite, PostgreSQL, MySQL)
2. Заполните параметры подключения
   - Для SQLite: нажмите "Browse..." или перетащите файл `.sqlite`/`*.db`
3. Нажмите "Connect"

### 2. Выбор таблиц

1. В списке таблиц отметьте галочками нужные таблицы
2. Нажмите "Generate Data"

### 3. Настройка паттернов

В появившемся окне для каждой колонки отображается:
- **Имя колонки** и тип данных
- **Sample значения** из существующих данных
- **Автоопределённый паттерн** (можно изменить)

#### Типы паттернов:

| Паттерн | Описание | Пример |
|---------|---------|--------|
| Auto-detect | Оставить автоматически определённый паттерн | - |
| Faker: name | Полное имя человека | John Smith |
| Faker: first_name | Имя | John |
| Faker: last_name | Фамилия | Smith |
| Faker: email | Email адрес | user@domain.com |
| Faker: phone | Номер телефона | +1-555-0101 |
| Faker: address | Адрес | 123 Main St |
| Faker: city | Город | New York |
| Faker: country | Страна | USA |
| Faker: date | Дата | 2024-01-15 |
| Faker: date_of_birth | Дата рождения | 1990-05-20 |
| Faker: company | Название компании | Acme Corp |
| Faker: job | Должность | Developer |
| Faker: text | Текст (lorem ipsum) | Random paragraph |
| Faker: url | Веб-адрес | https://example.com |
| Faker: uuid | UUID | 550e8400-e29b-41d4-a716-446655440000 |
| Faker: postcode | Почтовый индекс | 12345 |
| Enum | Случайный выбор из существующих значений | pending, shipped |
| Sequence | Автоинкремент (продолжает нумерацию) | 11, 12, 13 |
| Random Integer | Случайное целое число | 42 |
| Random Float | Случайное дробное число | 123.45 |
| Text | Случайная буквенно-цифровая строка | A3bK9mX2 |
| Reference (FK) | Случайный ID из связанной таблицы | 5 |

### 4. Параметры генерации

- **Rows to generate**: количество строк для генерации
- **Delete existing data**: очистить таблицу перед вставкой

Нажмите **OK** для запуска генерации.

## Структура проекта

```
datagenerator/
├── main.py                 # Точка входа
├── config.py               # Конфигурация
├── core/
│   ├── models.py           # Модели данных
│   ├── connection_manager.py # Управление подключениями
│   └── schema_analyzer.py  # Анализ структуры БД
├── generator/
│   ├── pattern_detector.py # Определение паттернов
│   ├── template_engine.py  # Генерация шаблонов
│   └── data_generator.py  # Генерация данных
└── ui/
    ├── main_window.py      # Главное окно
    └── pattern_editor_dialog.py # Диалог редактирования паттернов
```

## Требования

- Python 3.10+
- PyQt6
- SQLAlchemy
- Faker

## Лицензия

MIT
