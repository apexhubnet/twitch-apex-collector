import os
import sys
import requests
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import logging
import time
import heapq

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger()

# Проверка загрузки .env
logger.debug("Loading environment variables...")
load_dotenv()
logger.debug(f"DB_HOST: {os.getenv('DB_HOST')}")
logger.debug(f"DB_NAME: {os.getenv('DB_NAME')}")

def get_access_token():
    try:
        logger.debug("Requesting access token from Twitch...")
        payload = {
            'client_id': os.getenv('CLIENT_ID'),
            'client_secret': os.getenv('CLIENT_SECRET'),
            'grant_type': 'client_credentials'
        }
        response = requests.post("https://id.twitch.tv/oauth2/token", params=payload, timeout=10)
        response.raise_for_status()
        
        access_token = response.json().get('access_token')
        logger.debug(f"Access token received: {access_token[:10]}...")
        return access_token
    except Exception as e:
        logger.exception("Failed to get access token")
        return None

def get_game_id(access_token):
    try:
        logger.debug("Getting game ID for Apex Legends...")
        headers = {
            'Client-ID': os.getenv('CLIENT_ID'),
            'Authorization': f'Bearer {access_token}'
        }
        params = {'query': "Apex Legends"}
        response = requests.get(
            "https://api.twitch.tv/helix/search/categories",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json().get('data', [])
        logger.debug(f"Received {len(data)} games in search results")
        
        for game in data:
            if game['name'].lower() == "apex legends":
                game_id = game['id']
                logger.info(f"Found Apex Legends game ID: {game_id}")
                return game_id
        
        logger.error("Apex Legends not found in search results")
        return None
    except Exception as e:
        logger.exception("Failed to get game ID")
        return None

def get_all_streams(game_id, access_token):
    all_streams = []
    cursor = None
    max_requests = 20  # Максимум 2000 стримов (20 страниц по 100)
    request_count = 0
    
    while request_count < max_requests:
        try:
            headers = {
                'Client-ID': os.getenv('CLIENT_ID'),
                'Authorization': f'Bearer {access_token}'
            }
            params = {
                'game_id': game_id,
                'first': 100,  # Максимальное количество на страницу
                'after': cursor
            }
            
            response = requests.get(
                "https://api.twitch.tv/helix/streams",
                headers=headers,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            streams = data.get('data', [])
            pagination = data.get('pagination', {})
            
            all_streams.extend(streams)
            logger.info(f"Page {request_count+1}: Got {len(streams)} streams. Total: {len(all_streams)}")
            
            # Проверяем наличие следующей страницы
            if 'cursor' in pagination:
                cursor = pagination['cursor']
            else:
                break
                
            request_count += 1
            
            # Соблюдаем лимиты API
            if request_count % 10 == 0:
                time.sleep(1)  # Краткая пауза после 10 запросов
                
        except Exception as e:
            logger.exception(f"Error getting streams page {request_count+1}")
            break
            
    return all_streams

def save_to_db(total_viewers, game_id, top_channels):
    try:
        logger.debug("Connecting to database...")
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=3306
        )
        logger.debug("Database connection established")
        
        cursor = conn.cursor()
        
        # Вставляем основную статистику
        cursor.execute(
            "INSERT INTO apex_popularity (total_viewers, game_id) VALUES (%s, %s)",
            (total_viewers, game_id)
        )
        snapshot_id = cursor.lastrowid
        logger.debug(f"Inserted apex_popularity record ID: {snapshot_id}")
        
        # Вставляем топ каналов с дополнительными данными
        channel_records = []
        for channel in top_channels:
            # Преобразуем время начала стрима в формат MySQL
            started_at = datetime.fromisoformat(channel['started_at'].replace('Z', '+00:00'))
            channel_records.append((
                snapshot_id,
                channel['name'],
                channel['login'],
                channel['viewer_count'],
                channel['user_name'],
                channel['title'],
                started_at,
                channel['language'],
                channel['thumbnail_url']
            ))
        
        cursor.executemany(
            "INSERT INTO top_channels (snapshot_id, channel_name, user_login, viewer_count, user_name, title, started_at, language, thumbnail_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            channel_records
        )
        
        conn.commit()
        logger.info(f"Successfully saved data! Snapshot ID: {snapshot_id}")
        return True
    except mysql.connector.Error as err:
        logger.error(f"MySQL Error: {err}")
        logger.error(f"Error Code: {err.errno}")
        logger.error(f"SQLSTATE: {err.sqlstate}")
        logger.error(f"Message: {err.msg}")
        return False
    except Exception as e:
        logger.exception("General database error")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            logger.debug("Database connection closed")

def main():
    logger.info("===== STARTING APEX LEGENDS DATA COLLECTION =====")
    
    # Проверка критических переменных
    required_vars = ['CLIENT_ID', 'CLIENT_SECRET', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    access_token = get_access_token()
    if not access_token:
        logger.error("Access token not available. Aborting.")
        return
    
    game_id = get_game_id(access_token)
    if not game_id:
        logger.error("Game ID not available. Aborting.")
        return
    
    # Получаем ВСЕ стримы с пагинацией
    streams = get_all_streams(game_id, access_token)
    logger.info(f"Total streams found: {len(streams)}")
    
    if not streams:
        logger.warning("No active streams found. Saving empty dataset.")
        total_viewers = 0
        top_channels_data = []
    else:
        total_viewers = sum(stream['viewer_count'] for stream in streams)
        logger.info(f"Total viewers: {total_viewers}")
        
        # Топ-10 каналов (используем heapq для эффективности)
        top_channels = heapq.nlargest(
            10, 
            streams, 
            key=lambda x: x['viewer_count']
        )
        # Формируем данные для сохранения
        top_channels_data = [
            {
                'name': stream['user_name'],
                'login': stream['user_login'],
                'viewer_count': stream['viewer_count'],
                'user_name': stream['user_name'],
                'title': stream['title'],
                'started_at': stream['started_at'],
                'language': stream['language'],
                'thumbnail_url': stream['thumbnail_url']
            }
            for stream in top_channels
        ]
        logger.info(f"Top channel: {top_channels_data[0]['name']} ({top_channels_data[0]['login']}) with {top_channels_data[0]['viewer_count']} viewers")
        logger.debug(f"Sample data: Title='{top_channels_data[0]['title']}', Started at={top_channels_data[0]['started_at']}")
    
    if not save_to_db(total_viewers, game_id, top_channels_data):
        logger.error("Failed to save data to database")

if __name__ == "__main__":
    main()