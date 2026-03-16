# Minecraft Server Manager Bot

Минималистичный Telegram-бот для управления Minecraft серверами на VPS.

## Особенности

- ⚙️ Полное управление Minecraft серверами через Telegram
- ▶️ Поддержка Paper, Vanilla и Spigot серверов
- ⏹️ Запуск/остановка/перезагрузка серверов
- 🗑️ Управление портами и удаление серверов
- 📄 Просмотр логов серверов
- 🔐 SQLite база данных пользователей
- 🐳 Docker поддержка с Java (OpenJDK 17+)
- 💾 Максимум 5 серверов одновременно

## Структура проекта

```
minecraft-hosting-bot/
├── bot.py              # Telegram логика и обработчики
├── server_manager.py   # Управление серверами
├── config.py           # Конфигурация и переменные окружения
├── utils.py            # Вспомогательные функции
├── servers.json        # Конфигурация серверов
├── users.db            # SQLite база пользователей
├── .env                # Переменные окружения
├── Dockerfile          # Docker контейнер для бота
├── requirements.txt    # Python зависимости
├── README.md           # Этот файл
└── servers/            # Директория с серверами
```

## Требования

### Локально

- Python 3.11+
- Java (OpenJDK 17+)
- pip
- Linux VPS

### Docker

- Docker
- Docker Compose (опционально)

## Установка и запуск

### Вариант 1: Локально (Linux)

1. **Клонируйте репозиторий или скопируйте файлы:**

```bash
cd minecraft-hosting-bot
```

2. **Установите зависимости:**

```bash
pip install -r requirements.txt
```

3. **Установите Java (если не установлена):**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install openjdk-17-jre-headless

# CentOS/RHEL
sudo yum install java-17-openjdk
```

4. **Настройте .env файл:**

```bash
# Отредактируйте .env и добавьте ваш Telegram Bot Token
nano .env
```

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
MAX_SERVERS=5
SERVER_RAM_MIN=1G
SERVER_RAM_MAX=2G
```

5. **Запустите бота:**

```bash
python bot.py
```

### Вариант 2: Docker

1. **Соберите Docker образ:**

```bash
docker build -t mc-bot .
```

2. **Запустите контейнер:**

```bash
docker run -d \
  --name mc-bot \
  --env-file .env \
  -v $(pwd)/servers:/app/servers \
  -v $(pwd)/users.db:/app/users.db \
  -v $(pwd)/servers.json:/app/servers.json \
  mc-bot
```

3. **Проверьте логи:**

```bash
docker logs -f mc-bot
```

## Получение Telegram Bot Token

1. Откройте Telegram и найдите бота [BotFather](https://t.me/botfather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания нового бота
4. Скопируйте полученный токен в `.env` файл

## Интерфейс бота

### Главное меню

```
⚙️ Minecraft Server Manager

Servers: 2
Running: 1

[ Servers ]
[ Create Server ]
```

### Меню серверов

```
Servers

▶️ server_1
⏹️ server_2

[ server_1 ]
[ server_2 ]
[ Back ]
```

### Меню сервера

```
Server: server_1
Status: ▶️ running
Port: 25565
Type: Paper

[ Stop ]
[ Restart ]
[ Logs ]
[ Delete ]
[ Back ]
```

## Команды

- `/start` - Открыть главное меню и зарегистрироваться

## Функции

### Create Server

1. Выбираете тип сервера (Paper, Vanilla, Spigot)
2. Бот автоматически:
   - Создает директорию `servers/server_X`
   - Скачивает последнюю версию сервера JAR
   - Создает `eula.txt` с `eula=true`
   - Создает `server.properties` с базовыми настройками
   - Запускает сервер с параметрами: `java -Xms{RAM_MIN} -Xmx{RAM_MAX} -jar server.jar nogui`
   - Выводит IP VPS и порт сервера

### Server Management

- **Start** - Запустить остановленный сервер
- **Stop** - Остановить работающий сервер
- **Restart** - Перезагрузить сервер
- **Logs** - Показать последние 20 строк логов
- **Delete** - Удалить сервер и все его данные
- **Back** - Вернуться в меню серверов

## Конфигурация

### .env файл

```env
BOT_TOKEN=your_telegram_bot_token    # Ваш Bot Token
MAX_SERVERS=5                         # Максимум серверов
SERVER_RAM_MIN=1G                     # Минимальная RAM для сервера
SERVER_RAM_MAX=2G                     # Максимальная RAM для сервера
```

### servers.json

Автоматически генерируется при создании сервера. Пример:

```json
{
  "server_1": {
    "name": "server_1",
    "type": "paper",
    "path": "/app/servers/server_1",
    "jar": "/app/servers/server_1/server.jar",
    "pid": 12345,
    "status": "running",
    "port": 25565,
    "ram_min": "1G",
    "ram_max": "2G",
    "created_at": "1234567890"
  }
}
```

## Основные параметры сервера

- **name** - Имя сервера
- **type** - Тип (paper/vanilla/spigot)
- **path** - Полный путь к директории сервера
- **jar** - Путь к JAR файлу
- **pid** - ID процесса (если запущен)
- **status** - Статус (running/stopped)
- **port** - Порт сервера
- **ram_min** - Минимальная выделяемая RAM
- **ram_max** - Максимальная выделяемая RAM

## Типы серверов

### Paper

- Последняя стабильная версия от PaperMC
- Оптимизирован для производительности
- Совместим со всеми плагинами Spigot

### Vanilla

- Официальный Minecraft сервер от Mojang
- Без модификаций и плагинов
- Стандартная производительность

### Spigot

- Популярная платформа для плагинов
- Поддерживает большинство плагинов на Bukkit API
- Требует компиляции (использует Paper как альтернатива)

## Обработка ошибок

Бот автоматически:
- Проверяет, запущен ли процесс
- Обновляет статус, если сервер упал
- Обрабатывает сетевые ошибки при скачивании
- Логирует все операции в консоль

## Логирование

Все операции логируются с временными метками:

```
2026-03-16 10:30:45,123 - __main__ - INFO - User 123456789 registered
2026-03-16 10:30:50,456 - server_manager - INFO - Server server_1 started with PID 12345
```

## Зависимости

```
python-telegram-bot>=21.0.0  # Telegram Bot API
python-dotenv>=1.0.0         # Загрузка .env переменных
requests>=2.31.0             # HTTP запросы для скачивания
```

## Ограничения

- Максимум **5 серверов** одновременно
- Минимум **1GB** RAM на сервер
- Максимум **2GB** RAM на сервер (настраивается в .env)
- Требует Linux VPS

## Использование Dockerfile

### Обязательные переменные

```bash
docker run ... \
  -e BOT_TOKEN=your_token \
  mc-bot
```

### Рекомендуемые параметры

```bash
docker run -d \
  --name mc-bot \
  --restart unless-stopped \
  --env-file .env \
  -v /path/to/servers:/app/servers \
  -v /path/to/users.db:/app/users.db \
  -v /path/to/servers.json:/app/servers.json \
  mc-bot
```

## Проблемы и решения

### Бот не запускается

1. Проверьте, установлена ли Python 3.11+
2. Убедитесь, что BOT_TOKEN задан в .env
3. Проверьте наличие всех зависимостей: `pip install -r requirements.txt`

### Не скачивается сервер JAR

1. Проверьте интернет соединение
2. Убедитесь, что официальные источники доступны
3. Проверьте логи для деталей ошибки

### Не достаточно прав на запуск Java

1. Убедитесь, что установлена Java 17+
2. Проверьте права доступа к директории `servers`
3. Используйте `sudo` если необходимо (только в тестовых целях)

### Сервер не останавливается

1. Бот автоматически отправляет сигнал TERM
2. Если это не сработает, используется KILL
3. Проверьте наличие процесса: `ps aux | grep java`

## Безопасность

- ⚠️ Никогда не публикуйте ваш BOT_TOKEN
- 🔒 Используйте надежный пароль на VPS
- 📝 Регулярно проверяйте логи
- 🔐 Используйте роли пользователей (admin/user)

## Структура базы данных (SQLite)

### users таблица

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    registration_date TEXT,
    role TEXT DEFAULT 'user'
);
```

Пример:
```
user_id: 123456789
username: john_doe
registration_date: 2026-03-16T10:30:45.123456
role: admin
```

## Загрузка на VPS

1. **SSH подключение:**

```bash
ssh user@your_vps_ip
```

2. **Клонируйте проект:**

```bash
git clone <repo_url> minecraft-hosting-bot
cd minecraft-hosting-bot
```

3. **Установите зависимости:**

```bash
pip3 install -r requirements.txt
```

4. **Настройте .env:**

```bash
nano .env
```

5. **Запустите бота в фоне (используя systemd):**

```bash
# Создайте сервис файл
sudo nano /etc/systemd/system/mc-bot.service
```

```ini
[Unit]
Description=Minecraft Server Manager Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/minecraft-hosting-bot
ExecStart=/usr/bin/python3 /home/your_username/minecraft-hosting-bot/bot.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

6. **Запустите сервис:**

```bash
sudo systemctl enable mc-bot
sudo systemctl start mc-bot
sudo systemctl status mc-bot
```

## Мониторинг

### Просмотр логов в реальном времени

```bash
sudo journalctl -u mc-bot -f
```

### Проверка работающих процессов Java

```bash
ps aux | grep java
```

### Проверка занятых портов

```bash
netstat -tlnp | grep java
```

## Разработка

### Добавление новой команды

Отредактируйте `bot.py` и добавьте обработчик:

```python
async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Ваш код здесь
    pass

app.add_handler(CommandHandler('command_name', new_command))
```

### Добавление нового типа сервера

1. Отредактируйте `config.py` - добавьте в `SERVER_TYPES`
2. Отредактируйте `server_manager.py` - добавьте метод загрузки
3. Отредактируйте `bot.py` - добавьте обработчик кнопки

## Лицензия

MIT License

## Автор

Создано как инструмент для управления Minecraft серверами на VPS.

## Поддержка

Если у вас есть вопросы или проблемы:

1. Проверьте логи: `python bot.py` (локально) или `docker logs mc-bot`
2. Убедитесь, что все зависимости установлены
3. Проверьте конфигурацию в `.env`
4. Просмотрите примеры в README

## Версия

v1.0.0 - Март 2026

## Изменения

### v1.0.0

- ✅ Полная поддержка создания серверов
- ✅ Управление серверами (start/stop/restart)
- ✅ Просмотр логов
- ✅ SQLite база пользователей
- ✅ Docker поддержка
- ✅ Минималистичный интерфейс с inline клавиатурой
