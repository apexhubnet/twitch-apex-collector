# Twitch Apex Legends Statistics Collector 🔥

Сервис для автоматического сбора статистики по стримам Apex Legends на Twitch. Каждые 10 минут система собирает данные о:
- Общем количестве зрителей
- Топ-10 популярных каналах
- Детальной информации о каждом топ-стримере

## 📦 Структура проекта
```
├── Dockerfile            # Конфигурация контейнера
├── entrypoint.sh         # Скрипт инициализации
├── twitch_apex_stats.py  # Основная логика
└── .env.example          # Шаблон конфигурации
```

## 🌟 Основные возможности
- **Автоматический сбор данных** - обновление каждые 10 минут через cron
- **Подробная статистика** - зрители, время начала стрима, язык, превью
- **Безопасное хранение** - все чувствительные данные защищены
- **Устойчивость к ошибкам** - продвинутая обработка исключений
- **Эффективная работа** - оптимизированные запросы к Twitch API

## 📋 Требования
1. **Twitch Developer Account**
   - Зарегистрируйтесь на [dev.twitch.tv](https://dev.twitch.tv/)
   - Создайте приложение для получения `CLIENT_ID` и `CLIENT_SECRET`

2. **База данных MySQL**
   - Версия 5.7+
   - Доступ с хоста, где запущен сервис

## ⚠️ Требования к базе данных

Структура таблицы:
```
CREATE TABLE apex_popularity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_viewers INT NOT NULL,
    game_id VARCHAR(255) NOT NULL
);

CREATE TABLE top_channels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_id INT NOT NULL,
    channel_name VARCHAR(255) NOT NULL,
    user_login VARCHAR(255) NOT NULL,
    viewer_count INT NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    started_at DATETIME NOT NULL,
    language VARCHAR(50) NOT NULL,
    thumbnail_url TEXT NOT NULL,
    FOREIGN KEY (snapshot_id) REFERENCES apex_popularity(id)
);
```
## 💡 Особенности реализации
1. **Эффективный сбор данных**:
   - Пагинация для получения всех стримов
   - Использование heapq для быстрого поиска топ-каналов
   - Оптимальное использование квоты API

2. **Надежное хранение**:
   - Две связанные таблицы в БД
   - Детальная информация о каждом стриме
   - Автоматическая метка времени

3. **Обработка ошибок**:
   - Многоуровневая проверка переменных
   - Подробное логирование исключений
   - Повторные попытки при сбоях API

4. **Безопасность**:
   - Маскирование чувствительных данных в логах
   - Шифрование соединений с Twitch API
   - Изоляция данных в Docker-контейнере