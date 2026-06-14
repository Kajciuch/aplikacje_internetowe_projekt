"""
Ochrona przed CSRF (Cross-Site Request Forgery) — etap 12 (bezpieczeństwo).

Flask-WTF nie jest tu dostępne, więc implementujemy lekki mechanizm tokenów:
- przy każdej sesji generujemy losowy token,
- każdy formularz POST musi go odesłać w ukrytym polu,
- przed obsługą POST sprawdzamy zgodność.
"""

import secrets
from flask import session, request, abort


def generate_csrf_token():
    """Zwraca token CSRF dla bieżącej sesji (tworzy go przy pierwszym użyciu)."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def init_csrf(app):
    # Udostępniamy token w szablonach jako {{ csrf_token() }}.
    app.jinja_env.globals["csrf_token"] = generate_csrf_token

    @app.before_request
    def sprawdz_csrf():
        # Sprawdzamy tylko metody zmieniające dane.
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            # Żądania do API (JSON) zwolnione tutaj — API ma własną ochronę/token.
            if request.path.startswith("/api/"):
                return
            token_sesji = session.get("_csrf_token")
            token_formularza = request.form.get("_csrf_token") or request.headers.get("X-CSRFToken")
            if not token_sesji or token_sesji != token_formularza:
                abort(400, description="Nieprawidłowy token CSRF.")
