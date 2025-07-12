#!/bin/bash

# Создаем .env файл
cat > /app/.env <<EOF
CLIENT_ID=${CLIENT_ID}
CLIENT_SECRET=${CLIENT_SECRET}
DB_HOST=${DB_HOST}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
EOF

# Проверка переменных окружения
echo "===== ENVIRONMENT VARIABLES ====="
echo "CLIENT_ID: ${CLIENT_ID:0:4}..."  # Показываем только первые 4 символа
echo "CLIENT_SECRET: ${CLIENT_SECRET:0:4}..."
echo "DB_HOST: $DB_HOST"
echo "DB_NAME: $DB_NAME"
echo "================================"

# Запуск cron
echo "Starting cron service..."
cron -f