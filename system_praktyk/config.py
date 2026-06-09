"""
Konfiguracja aplikacji.

Czyta ustawienia ze zmiennych środowiskowych / pliku .env.
Mamy dwa profile: development (domyślny) i production.
Profil wybiera zmienna FLASK_ENV (np. FLASK_ENV=production).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Wczytujemy plik .env z katalogu projektu (jeśli istnieje).
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class BaseConfig:
    # Klucz do podpisywania sesji/ciasteczek. W produkcji USTAW własny w .env!
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-zmien-mnie")

    # Ścieżka do pliku bazy SQLite.
    DATABASE = os.getenv("DATABASE", str(BASE_DIR / "praktyki.db"))

    # Logowanie przez Microsoft (OAuth2) — aktywne tylko, gdy ustawisz te zmienne.
    MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
    MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")
    MS_TENANT_ID = os.getenv("MS_TENANT_ID", "common")
    MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI", "http://localhost:5000/auth/microsoft/callback")

    @property
    def MICROSOFT_LOGIN_ENABLED(self):
        return bool(self.MS_CLIENT_ID and self.MS_CLIENT_SECRET)


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    # W produkcji ciasteczka tylko po HTTPS i niedostępne z JS (ochrona przed XSS).
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    return ProductionConfig() if env == "production" else DevelopmentConfig()
