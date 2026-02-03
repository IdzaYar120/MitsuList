# 🎭 MitsuList

![MitsuList Logo](C:/Users/user/.gemini/antigravity/brain/bb849ac9-1b0c-4dc8-8e2d-8786e560b071/mitsulist_logo_concept_1770141340181.png)

**MitsuList** is a vibrant, production-grade anime tracking web application built with **Django**. It features a striking **Vibrant Pop** (Persona 5 inspired) aesthetic, combining sharp geometry, bold typography, and high-contrast visuals.

## ✨ Key Features

- **Dynamic Homepage**: Real-time anime data fetched from the Jikan API (MyAnimeList).
- **Vibrant Pop Design**: Custom CSS layout with skewed containers and a curated red-black-white palette.
- **Smart Caching**: Implemented a backend caching layer to minimize API latency and handle rate limits.
- **Optimized Search**: Seamless AJAX-based search to find your favorite titles instantly.
- **Detail-Rich Views**: Comprehensive anime details including stats, relations, and synopsis.
- **Production-Ready**: Configured for PostgreSQL and environment-based settings.

## 🛠️ Tech Stack

- **Backend**: Django (Python)
- **Database**: PostgreSQL
- **API**: Jikan API v4
- **Frontend**: Vanilla HTML5, CSS3 (Custom Variables), JavaScript (AJAX)
- **Styles**: "Vibrant Pop" Custom System

## 🚀 Quick Start

### 1. Requirements
Ensure you have Python 3.10+ and a running PostgreSQL instance.

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Setup Environment
Create a `.env` file in the root directory (use `.env.template` or copy settings):
```env
SECRET_KEY=your_key_here
DEBUG=True
DB_NAME=mitsulist_db
DB_USER=postgres
DB_PASS=your_pass
DB_HOST=127.0.0.1
DB_PORT=5433
```

### 4. Database Migrations
```bash
python manage.py migrate
```

### 5. Run Server
```bash
python manage.py runserver
```

## 📐 Architecture
- **DRY Templates**: Uses a central `base.html` for layout consistency.
- **Helper Views**: Centralized API fetching with safe throttling.
- **Secure Config**: All sensitive keys are handled via environment variables.

---

*Made with ❤️ for Anime fans.*
