"""
System Obsługi Praktyk — punkt wejścia aplikacji (fabryka aplikacji Flask).

Uruchomienie (development):
    flask --app app run --debug
albo:
    python app.py

Pierwsze uruchomienie wymaga bazy z danymi:
    python seed.py
"""

from flask import Flask, render_template, jsonify, request

from config import get_config
from database import register_db
from security import init_csrf
from auth import auth_bp, init_auth
from routes.main import main_bp
from routes.documents import dok_bp
from routes.api import api_bp
from routes.admin import admin_bp


def create_app():
    app = Flask(__name__)
    cfg = get_config()
    app.config.from_object(cfg)
    app.config_object = cfg          # wygodny dostęp do obiektu konfiguracji

    # Infrastruktura
    register_db(app)                 # baza + komenda `flask init-db`
    init_csrf(app)                   # ochrona CSRF
    init_auth(app)                   # current_user w szablonach

    # Trasy (blueprinty)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(dok_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    _zarejestruj_bledy(app)
    return app


def _zarejestruj_bledy(app):
    """Dedykowane strony błędów (HTML dla stron, JSON dla /api)."""

    def odpowiedz(kod, szablon):
        if request.path.startswith("/api/"):
            return jsonify({"error": szablon}), kod
        return render_template(f"{kod}.html"), kod

    @app.errorhandler(400)
    def err_400(e):
        return odpowiedz(400, "Błędne żądanie.")

    @app.errorhandler(403)
    def err_403(e):
        return odpowiedz(403, "Brak dostępu.")

    @app.errorhandler(404)
    def err_404(e):
        return odpowiedz(404, "Nie znaleziono.")

    @app.errorhandler(500)
    def err_500(e):
        app.logger.exception("Błąd serwera")
        return odpowiedz(500, "Błąd serwera.")


# Instancja używana przez `flask --app app` oraz `python app.py`.
app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", True))
