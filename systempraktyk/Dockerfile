# Wieloetapowy obraz dla System Obsługi Praktyk
FROM python:3.12-slim AS base

WORKDIR /app

# Zależności systemowe (waitress jako serwer WSGI produkcyjny)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Najpierw same wymagania (lepszy cache warstw)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt waitress==3.0.0

# Reszta projektu
COPY . .

ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Inicjalizacja bazy przy pierwszym starcie + uruchomienie serwera
EXPOSE 5000
CMD ["sh", "-c", "python seed.py && waitress-serve --listen=0.0.0.0:5000 app:app"]
