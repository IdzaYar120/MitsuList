# 🎭 MitsuList

![MitsuList Logo](C:/Users/user/.gemini/antigravity/brain/bb849ac9-1b0c-4dc8-8e2d-8786e560b071/mitsulist_logo_concept_1770141340181.png)

**MitsuList** is a vibrant, production-grade anime tracking web application built with **Django 6.0**. It goes beyond simple list-making, offering a full social ecosystem with real-time notifications, a Persona 5-inspired *"Vibrant Pop"* aesthetic, and intelligent async integrations with the Jikan API.

## ✨ Key Features

- **Dynamic & Async API Engine**: Fetches real-time anime data from the Jikan (MyAnimeList) API using `httpx` and `asyncio`, backed by exponential backoff, connection throttling, custom semaphores, and an automatic fallback UI.
- **Advanced Caching Ecosystem**: 3-layer caching structure (Memory, PostgreSQL Database, and Redis) including a specialized Translation Caching system and Anime Schedules caching to drastically reduce external API load.
- **Social & Community**: 
  - Centralized **Activity Feeds** to see what your friends are watching.
  - **Clubs System**: Create anime clubs and recommend specific titles directly to club members.
  - **Live Chat & Notifications**: Real-time direct messaging and notifications powered by **Django Channels** and WebSockets.
- **Intelligent Global Search**: High-performance Full-Text Search utilizing native **PostgreSQL SearchVector**. Finds results instantly across User Profiles, Reviews, News, and Anime titles simultaneously.
- **Gamification & Customization**: Earn special badges based on activity, customize your profile with different themes (Dark/Light) and varied Accent Colors, and upload avatars via **Cloudinary**.
- **Yearly "Wrapped" Stats**: Automatically analyzes your watched items, episodes, and scores to generate a personalized "Year in Review" breakdown (similar to Spotify Wrapped) with your top genres and time spent.
- **Discord Integration**: OAuth-based Discord login and account syncing.

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Django 6.0
- **Asynchronous Processing**: `asgiref`, `async_to_sync`, `httpx`
- **Real-Time / Tasks**: Django Channels, Celery, Redis
- **Database**: PostgreSQL (with Full-Text Search), `psycopg2-binary`
- **Storage**: Cloudinary API (`django-cloudinary-storage`)
- **Frontend**: Vanilla HTML5/CSS3 (Custom CSS Variables), Vanilla JS (HTMX/AJAX patterns)
- **Deployment**: Gunicorn, Whitenoise (Static), PostgreSQL (Production DB)

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- PostgreSQL Server 
- Redis (For Channels & Celery)

### 2. Installation
```bash
git clone https://github.com/IdzaYar120/MitsuList.git
cd MitsuList
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Setup Environment
Create a `.env` file in the project root:
```env
DEBUG=True
SECRET_KEY=your_secret_key_here
DJANGO_ENV=development

# Database Config
DB_NAME=mitsulist_db
DB_USER=postgres
DB_PASS=your_password
DB_HOST=127.0.0.1
DB_PORT=5432

# Redis & Channels
REDIS_URL=redis://127.0.0.1:6379

# Cloudinary (Optional for Dev, fallback is local)
# CLOUDINARY_URL=cloudinary://...
```

### 4. Database Setup & Initialization
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Running the Application
Since the app features WebSockets, an ASGI server is required. Django's `runserver` directly handles ASGI thanks to `daphne` in installed apps:

```bash
python manage.py runserver
```
*(Alternatively, you can run Celery workers for background functionality: `celery -A mitsulist worker -l info`)*

## 📐 Architecture Highlights

- **Anti-FOUC Theming**: JavaScript checks injected into the Document `HEAD` to cleanly load DB-defined or LocalStorage-defined user themes before the body paints to prevent flashing.
- **Robust Outage Handling**: Global Context Processor that tracks API health flags and warns users natively if the external Anime API becomes rate-limited or fails for 5+ min.
- **DRY & Security-First**: Strict Content Security Policies (`django-csp`), Rate-Limiting rules, localized translations via `deep-translator`, and strictly segregated environments.

---
*Developed by IdzaYar120. Made with ❤️ for Anime fans.*
