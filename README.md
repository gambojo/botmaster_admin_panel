# Admin Panel - Standalone Application

Веб-панель администратора как отдельное приложение для управления Telegram ботом через REST API.

## Особенности

- ✅ **Отдельное приложение** - Работает независимо от бота
- ✅ **REST API** - Подключается к боту через REST API
- ✅ **Безопасность** - API ключи для аутентификации
- ✅ **Современный UI** - Темная тема с градиентами
- ✅ **Responsive Design** - Адаптивный дизайн для Desktop и Mobile
- ✅ **Компактный размер** - Уменьшенный масштаб (Desktop: 13px, Mobile: 11px)

## Структура

```
botmaster_admin_panel/         # Корневая директория проекта админ-панели
├── main.py                    # Главный файл приложения, точка входа
├── requirements.txt           # Зависимости Python (библиотеки и версии)
├── config/                    # Директория конфигурационных файлов
│   ├── .env_example           # Пример файла переменных окружения
│   └── config.yml             # Основной конфигурационный файл в YAML формате
├── static/                    # Статические файлы (CSS, JS, изображения)
│   ├── css/                   # Стили CSS
│   │   ├── admin.css          # Основные стили админ-панели
│   │   └── themes/            # Директория тем оформления
│   │       ├── midnight.css   # Тема "Полночь"
│   │       ├── moonlight.css  # Тема "Лунный свет"
│   │       ├── cyber.css      # Тема "Киберпанк"
│   │       ├── ocean.css      # Тема "Океан"
│   │       ├── brown.css      # Тема "Коричневая"
│   │       └── purple.css     # Тема "Фиолетовая"
│   └── js/
│       └── admin.js           # JavaScript логика фронтенда
├── templates/                 # HTML шаблоны Jinja2
│   ├── base.html              # Базовый шаблон (макет)
│   ├── login.html             # Страница авторизации
│   ├── info.html              # Страница информации о системе
│   ├── users.html             # Управление пользователями
│   ├── groups.html            # Управление группами
│   ├── plugins.html           # Управление плагинами
│   ├── modules.html           # Управление модулями
│   ├── referrals.html         # Управление реферальной системой
│   ├── logs.html              # Просмотр логов
│   └── broadcast.html         # Страница рассылки сообщений
└── src/                       # Исходный код Python
    ├── __init__.py            # Инициализация пакета src
    ├── config_manager.py      # Менеджер конфигурации (загрузка настроек)
    ├── logging_config.py      # Настройка логирования
    ├── audit_logger.py        # Логирование действий администратора
    └── handlers/              # Обработчики HTTP запросов (роуты)
        ├── __init__.py        # Инициализация пакета handlers
        ├── base.py            # Базовые обработчики
        ├── auth.py            # Аутентификация и авторизация
        ├── users.py           # API для работы с пользователями
        ├── groups.py          # API для работы с группами
        ├── plugins.py         # API для работы с плагинами
        ├── modules.py         # API для работы с модулями
        ├── referrals.py       # API для работы с реферальной системой
        ├── logs.py            # API для работы с логами
        ├── info.py            # API системной информации
        └── broadcast.py       # API рассылки сообщений
```

## Установка и настройка

### 1. Требования

```bash
pip install -r requirements.txt
```

### 2. Конфигурация

Отредактируйте `config/config.yml`:

```yaml
api:
  url: 'http://localhost:8081'
  key: ""
  host: '0.0.0.0'
  port: 8080
auth:
  basic:
    enable: true
    admin_username: 'admin'
    admin_password: 'admin'
  cors:
    enable: true
    allowed_origins: []
    allowed_methods: []
    allowed_headers: []
logging:
  standard_log:
    level: 'INFO'
    console: true
    file: 'logs/admin_panel.log'
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    max_size: 10485760
  audit_log:
    enable: true
    console: true
    file: 'logs/audit.log'
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    max_size: 10485760
  aiohttp_access_log:
    disable: true
```

#### Параметры конфигурации:

**API настройки:**
- `api.url` - URL Bot API (должен совпадать с портом BotAPI в боте)
- `api.key` - API ключ для аутентификации (получите из логов бота при первом запуске)
- `api.host` - Хост для прослушивания (0.0.0.0 для доступа извне)
- `api.port` - Порт для админ-панели (по умолчанию 8080)

**Аутентификация:**
- `auth.basic.enable` - Включение/отключение базовой аутентификации
- `auth.basic.admin_username` - Имя пользователя для входа в админ-панель
- `auth.basic.admin_password` - Пароль для входа в админ-панель

**Безопасность:**
- `auth.cors.enable` - Включение/отключение CORS защиты
- `auth.cors.allowed_origins` - Список разрешенных доменов для CORS (пусто = все)
- `auth.cors.allowed_methods` - Разрешенные HTTP методы (пусто = все)
- `auth.cors.allowed_headers` - Разрешенные заголовки (пусто = все)
- `logging.audit_log.enable` - Включение детального логирования действий администратора

**Основное логирование:**
- `logging.standard_log.level` - Уровень детализации логов (DEBUG, INFO, WARNING, ERROR)
- `logging.standard_log.console` - Вывод логов в консоль
- `logging.standard_log.file` - Путь к файлу для сохранения логов
- `logging.standard_log.format` - Формат записей в логах
- `logging.standard_log.max_size` - Максимальный размер файла лога в байтах

**Аудит-логирование:**
- `logging.audit_log.enable` - Включение аудит-логирования
- `logging.audit_log.console` - Вывод аудит-логов в консоль
- `logging.audit_log.file` - Путь к файлу для сохранения аудит-логов
- `logging.audit_log.format` - Формат записей в аудит-логах
- `logging.audit_log.max_size` - Максимальный размер файла аудит-лога в байтах

**Детальные логи доступа:**
- `logging.aiohttp_access_log.disable` - Отключение логов доступа aiohttp (для уменьшения шума)


### 3. Настройка бота

В файле конфигурации бота добавьте секцию `api`:

```yaml
api:
  url: 'http://localhost:8081'
  key: ""
  host: '0.0.0.0'
  port: 8080
```

**Важно:** API ключ должен совпадать в конфигурации бота и админ-панели!

## Запуск
```bash
python main.py
```

Админ-панель будет доступна по адресу: `http://localhost:8080`

## Использование

### Вход в систему
- Откройте браузер и перейдите на `http://localhost:8080`
- Введите логин и пароль из `config/config.yml` или переменных окружения

### Основные функции

#### Auth (Аутентификация)
- Вход в систему
- Проверка прав доступа
- Выход из системы

#### Info (Информация)
- Общая информация о системе
- Статус сервисов
- Мониторинг производительности
- Статистика пользователей

#### Users (Пользователи)
- Просмотр списка пользователей
- Блокировка/разблокировка
- Изменение ролей
- Отправка сообщений

#### Groups (Группы)
- Управление группами пользователей
- Добавление/удаление пользователей

#### Broadcast (Рассылка)
- Массовая отправка сообщений
- Выбор целевой аудитории
- История рассылок

#### Logs (Логи)
- Просмотр системных логов
- Фильтрация по уровню и типу
- Поиск по ключевым словам
- Автообновление

#### Plugins (Плагины)
- Список установленных плагинов
- Управление плагинами

#### Modules (Модули)
- Просмотр списка модулей
- Получение конфигурации модулей
- Включение/отключение модулей

#### Referrals (Реферальная система)
- Просмотр информации о рефералах пользователя
- История транзакций баллов
- Начисление баллов пользователям
- Списание баллов


### Доступные endpoints:
```
GET  /api/statistics                        - Статистика
GET  /api/users                             - Список пользователей
GET  /api/users/{id}                        - Информация о пользователе
POST /api/users/{id}/block                  - Блокировка
POST /api/users/{id}/unblock                - Разблокировка
POST /api/users/{id}/message                - Отправка сообщения
GET  /api/logs                              - Логи
POST /api/broadcast                         - Рассылка
GET  /api/groups                            - Группы
GET  /api/plugins                           - Плагины
GET  /api/modules                           - Список модулей
GET  /api/modules/{module_name}             - Информация о модуле
POST /api/modules/{module_name}/enable      - Включить модуль
POST /api/modules/{module_name}/disable     - Отключить модуль
GET  /api/referrals/{user_id}               - Информация о рефералах
GET  /api/referrals/{user_id}/history       - История транзакций
POST /api/referrals/{user_id}/points/credit - Начислить баллы
POST /api/referrals/{user_id}/points/debit  - Списать баллы
```
