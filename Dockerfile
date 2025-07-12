FROM python:3.10-slim

# Установка зависимостей
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование файлов
COPY . /app

# Установка Python-зависимостей
RUN pip install --no-cache-dir requests mysql-connector-python python-dotenv

# Настройка cron

RUN echo "*/10 * * * * /usr/local/bin/python3 /app/twitch_apex_stats.py > /proc/1/fd/1 2>&1" | crontab -

# Права на выполнение скриптов
RUN chmod +x /app/entrypoint.sh /app/twitch_apex_stats.py

ENTRYPOINT ["/app/entrypoint.sh"]