
# 📊 youtube-insight-2025

> Анализ трендов на YouTube для бизнеса: находите популярные темы, создавайте востребованный контент и эффективно продвигайте продукцию или услуги.

---

## 🎯 Основные возможности

<details>
<summary>📈 Анализ трендов</summary>

- Инструменты мониторинга: YouTube Trends, Analytics 🔍
- Google Trends: сезонность, долгосрочные тренды 📅
- Сторонние сервисы: VidIQ, TubeBuddy, Social Blade 💡
</details>

<details>
<summary>🤝 Инфлюенсер-маркетинг</summary>

- Поиск и фильтрация каналов по ключевым словам и подписчикам 🎥
- Извлечение контактов: email, соцссылки 📧
- Сохранение данных в PostgreSQL, кеширование processed_ids.txt 🗄️
</details>

<details>
<summary>🛠 Video Processing Toolkit</summary>

- Загрузка видео: yt-dlp ⬇️
- Нарезка: MoviePy + FFmpeg ✂️
- Анализ аудио: Librosa 🎵
- Генерация шортсов/превью: GPT + DeepSeek 🤖
</details>

<details>
<summary>💬 Анализ комментариев</summary>

- Очистка и лемматизация текста 🧹
- Векторизация: SentenceTransformer 🔢
- Кластеризация: K-Means + t-SNE 📊
- Метрики качества: Silhouette, Calinski-Harabasz, Davies-Bouldin ✅
</details>

<details>
<summary>📊 Анализ конкурентов</summary>

- Сбор метрик: просмотры, лайки, комментарии 👍
- Рейтинг успешности: соотношение вовлеченности к просмотрам 🏆
- Рекомендации по форматам и стратегиям 🎬
</details>

---

## 🚀 Установка и запуск

```bash
# Клонировать репозиторий
git clone https://github.com/your-org/youtube-insight-2025.git
cd youtube-insight-2025

# Установить зависимости
pip install -r requirements.txt
````

> Файл `requirements.txt` содержит:

```
yt-dlp
moviepy
librosa
numpy
soundfile
requests
youtube-transcript-api
ollama-cli
psycopg2-binary
google-api-python-client
python-dotenv
```

---

## 📚 Использование

```bash
# Анализ трендов и генерация отчётов
python main.py --analysis trends --output report.pdf

# Обработка видео и создание шортсов
python video_processor.py https://www.youtube.com/watch?v=VIDEO_ID
```

---

## ⚙️ Структура проекта

```
./
├── main.py                     # Точка входа анализа трендов
├── video_processor.py          # Загрузка, анализ и нарезка видео
├── comments_clustering.py      # Кластеризация комментариев
├── preview_service.py          # Генерация превью
├── extract_batch.py            # Пакетная обработка транскриптов
├── service.py                  # Транскрипции видео
├── deepseek_integration.py     # Оценка популярности аудио
├── gpt_service.py              # Генерация с помощью Ollama/GPT
├── requirements.txt            # Зависимости
└── README.md                   # Описание проекта
```

---

## 🔗 Контакты и обратная связь

* 📧 Email: `hello@you-insight.com`
* 💬 Telegram: [@you\_insight\_bot](https://t.me/you_insight_bot)
* 🌐 Сайт: [you-insight.com](https://you-insight.com)
* 💼 LinkedIn: [Your Company](https://linkedin.com/company/you-insight)

---

*Спасибо за использование youtube-insight-2025!* 🙏

```

