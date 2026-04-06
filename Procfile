web: daphne mitsulist.asgi:application --port $PORT --bind 0.0.0.0
worker: celery -A mitsulist worker --loglevel=info
