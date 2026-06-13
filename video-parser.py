import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

url = "https://it-lms.tusur.ru/course/resources.php?id=41"
headers = {
    'User-Agent': os.getenv("USER-AGENT"),
    'Cookie': os.getenv("COOKIE")
}


# 1. Выносим логику обработки ОДНОГО тега в функцию
def process_and_download_video(tag):
    print("="*20)
    page_url = tag.get('href')
    full_page_url = urljoin(url, page_url)

    response = requests.get(full_page_url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    video_tag = soup.find('video')
    title = soup.find('h2').find('span')
    title_text = title.text.strip().replace('/', '-').replace(':', '-') if title else 'Видео_без_названия'

    # TODO Сделать путь Videos/*.mp4
    file_path = f'{title_text}.mp4'

    if Path(file_path).exists():
        print(f"Файл {title_text} пропущен")
        return

    if video_tag:
        source_tag = video_tag.find('source')  # Ищем source, как вы и решили
        if source_tag and source_tag.get('src'):
            video_url = urljoin(full_page_url, source_tag.get('src'))
            print(f"Начинаю скачивание: {title_text}...")

            # Скачиваем с увеличенным чанком
            resp = requests.get(video_url, headers=headers, stream=True)
            if resp.status_code == 200:
                with open(file_path, 'wb') as file:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):  # 1 МБ
                        if chunk:
                            file.write(chunk)
                print(f"✅ {title_text} успешно сохранён!")
            else:
                print(f"❌ Ошибка скачивания {title_text}. Статус: {resp.status_code}")
            return  # Выходим из функции при успехе

    print(f"⚠️ Файл видео не найден на странице: {title_text}")


# 2. Основной блок запуска
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'lxml')
tags = soup.select('a[href*="/videofile/"]')

# 3. Запускаем многопоточность (например, 5 потоков одновременно)
print(f"Найдено ссылок: {len(tags)}. Начинаем многопоточное скачивание...")

with ThreadPoolExecutor(max_workers=5) as executor:
    # Метод map автоматически раскидает все ваши 'tags' по 5 потокам
    executor.map(process_and_download_video, tags)

print("Все загрузки завершены!")