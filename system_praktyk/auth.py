"""
Autoryzacja i logowanie.

Zawiera:
- current_user()  – zwraca zalogowanego użytkownika (lub None),
- @login_required – wymaga zalogowania,
- @role_required  – wymaga konkretnej roli,
- blueprint `auth_bp` z trasami /login, /logout oraz logowaniem Microsoft (OAuth2).

Logowanie Microsoft jest WYŁĄCZONE, dopóki w .env nie ustawisz MS_CLIENT_ID
i MS_CLIENT_SECRET (patrz README → sekcja OAuth).
"""

import secrets
import urllib.parse
from functools import wraps

import requests
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, g, current_app, abort)

import models

auth_bp = Blueprint("auth", __name__)


# ----------------------------------------------------------------------------
#  Bieżący użytkownik + dekoratory
# ----------------------------------------------------------------------------
def current_user():
    """Zwraca zalogowanego użytkownika (cache w `g`) albo None."""
    if "user" not in g:
        uid = session.get("user_id")
        g.user = models.get_user(uid) if uid else None
    return g.user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            flash("Zaloguj się, aby uzyskać dostęp.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def role_required(*role):
    """Wymaga, by zalogowany użytkownik miał jedną z podanych ról."""
    def dekorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            u = current_user()
            if u is None:
                return redirect(url_for("auth.login", next=request.path))
            if u.rola not in role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return dekorator


def init_auth(app):
    """Udostępnia current_user() i flagę OAuth we wszystkich szablonach."""
    @app.context_processor
    def wstrzyknij_uzytkownika():
        return {
            "current_user": current_user(),
            "microsoft_login_enabled": app.config_object.MICROSOFT_LOGIN_ENABLED,
            "impersonator_active": bool(session.get("impersonator_id")),
        }


# ----------------------------------------------------------------------------
#  Logowanie lokalne (e-mail + hasło)
# ----------------------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "")
        haslo = request.form.get("haslo", "")
        user = models.get_user_by_email(email)
        if user and user.sprawdz_haslo(haslo):
            session.clear()
            session["user_id"] = user.id
            flash(f"Witaj, {user.imie}!", "success")
            nast = request.args.get("next")
            return redirect(nast or url_for("main.dashboard"))
        flash("Błędny e-mail lub hasło.", "error")

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Wylogowano.", "success")
    return redirect(url_for("auth.login"))


# ----------------------------------------------------------------------------
#  Logowanie Microsoft (OAuth2) — aktywne tylko z konfiguracją w .env
#  Dokumentacja: https://learn.microsoft.com/azure/active-directory/develop/
# ----------------------------------------------------------------------------
def _ms_authority(cfg):
    return f"https://login.microsoftonline.com/{cfg.MS_TENANT_ID}"


@auth_bp.route("/auth/microsoft")
def microsoft_login():
    cfg = current_app.config_object
    if not cfg.MICROSOFT_LOGIN_ENABLED:
        flash("Logowanie Microsoft nie jest skonfigurowane (uzupełnij .env).", "warning")
        return redirect(url_for("auth.login"))

    # Token 'state' chroni przed CSRF w przepływie OAuth.
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state
    params = {
        "client_id": cfg.MS_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": cfg.MS_REDIRECT_URI,
        "response_mode": "query",
        "scope": "openid email profile User.Read",
        "state": state,
    }
    url = f"{_ms_authority(cfg)}/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}"
    return redirect(url)


@auth_bp.route("/auth/microsoft/callback")
def microsoft_callback():
    cfg = current_app.config_object
    if not cfg.MICROSOFT_LOGIN_ENABLED:
        abort(404)

    # Weryfikacja stanu (ochrona CSRF).
    if request.args.get("state") != session.pop("oauth_state", None):
        flash("Nieprawidłowy stan logowania OAuth.", "error")
        return redirect(url_for("auth.login"))

    code = request.args.get("code")
    if not code:
        flash("Logowanie Microsoft nie powiodło się.", "error")
        return redirect(url_for("auth.login"))

    # Wymiana kodu na token dostępu.
    token_resp = requests.post(
        f"{_ms_authority(cfg)}/oauth2/v2.0/token",
        data={
            "client_id": cfg.MS_CLIENT_ID,
            "client_secret": cfg.MS_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": cfg.MS_REDIRECT_URI,
            "scope": "openid email profile User.Read",
        },
        timeout=10,
    )
    token = token_resp.json().get("access_token")
    if not token:
        flash("Nie udało się uzyskać tokenu Microsoft.", "error")
        return redirect(url_for("auth.login"))

    # Pobranie profilu użytkownika z Microsoft Graph.
    profil = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    ).json()

    email = (profil.get("mail") or profil.get("userPrincipalName") or "").lower()
    if not email:
        flash("Konto Microsoft nie udostępniło adresu e-mail.", "error")
        return redirect(url_for("auth.login"))

    # Logika pierwszego logowania: jeśli użytkownika nie ma, zakładamy konto
    # studenta (domyślna rola — administrator może ją później zmienić).
    user = models.get_user_by_email(email)
    if user is None:
        models.create_user(
            email=email,
            imie=profil.get("givenName", ""),
            nazwisko=profil.get("surname", ""),
            rola="student",
            oauth_provider="microsoft",
            oauth_sub=profil.get("id"),
        )
        user = models.get_user_by_email(email)

    session.clear()
    session["user_id"] = user.id
    flash(f"Zalogowano przez Microsoft. Witaj, {user.imie}!", "success")
    return redirect(url_for("main.dashboard"))
