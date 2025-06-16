FROM python:3.10-slim

# Cache buster: 2025-06-16-1113
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:8080 & python3 bot.py"]
