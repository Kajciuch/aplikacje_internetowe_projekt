"""
REST API (etap 9) — warstwa danych w formacie JSON.

Wszystkie endpointy wymagają zalogowania (sesja). Operacje zmieniające dane
sprawdzają rolę. Zwracamy poprawne statusy HTTP: 200, 201, 400, 401, 403, 404.

Przykłady (curl) — patrz docs/API.md.
"""

import json
from functools import wraps
from flask import Blueprint, jsonify, request, g

import models
import forms_meta as meta
from database import query_all, query_one, execute
from auth import current_user

api_bp = Blueprint("api", __name__, url_prefix="/api")


# --- Pomocnicze --------------------------------------------------------------
def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    # rozwijamy dane_json do obiektu, jeśli obecne
    if "dane_json" in d:
        try:
            d["dane"] = json.loads(d.pop("dane_json") or "{}")
        except (json.JSONDecodeError, TypeError):
            d["dane"] = {}
    return d


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return jsonify({"error": "Wymagane uwierzytelnienie."}), 401
        return view(*args, **kwargs)
    return wrapped


def api_role(*role):
    def dek(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            u = current_user()
            if u is None:
                return jsonify({"error": "Wymagane uwierzytelnienie."}), 401
            if u.rola not in role:
                return jsonify({"error": "Brak uprawnień."}), 403
            return view(*args, **kwargs)
        return wrapped
    return dek


def paginacja():
    """Zwraca (limit, offset) na podstawie ?page= i ?per_page= (rozszerzenie)."""
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except ValueError:
        page, per_page = 1, 20
    return per_page, (page - 1) * per_page, page, per_page


# ============================================================================
#  STUDENCI
# ============================================================================
@api_bp.get("/students")
@api_login_required
def api_students():
    rows = query_all(
        "SELECT id, email, imie, nazwisko, nr_albumu FROM users WHERE rola='student' "
        "ORDER BY nazwisko, imie"
    )
    return jsonify({"count": len(rows), "data": [dict(r) for r in rows]})


@api_bp.get("/students/<int:sid>")
@api_login_required
def api_student(sid):
    row = query_one("SELECT id, email, imie, nazwisko, nr_albumu FROM users "
                    "WHERE id=? AND rola='student'", (sid,))
    if not row:
        return jsonify({"error": "Nie znaleziono studenta."}), 404
    prakt = models.praktyki_studenta(sid)
    out = dict(row)
    out["praktyki"] = [dict(p) for p in prakt]
    return jsonify(out)


# ============================================================================
#  PRAKTYKI (internships)
# ============================================================================
@api_bp.get("/internships")
@api_login_required
def api_internships():
    student_id = request.args.get("student_id", type=int)
    limit, offset, page, per_page = paginacja()

    sql = ("SELECT p.*, s.imie AS student_imie, s.nazwisko AS student_nazwisko "
           "FROM praktyki p JOIN users s ON s.id=p.student_id")
    params = []
    if student_id:
        sql += " WHERE p.student_id=?"
        params.append(student_id)
    sql += " ORDER BY p.utworzono DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    rows = query_all(sql, tuple(params))
    return jsonify({"page": page, "per_page": per_page,
                    "count": len(rows), "data": [dict(r) for r in rows]})


@api_bp.get("/internships/<int:pid>")
@api_login_required
def api_internship(pid):
    row = models.get_praktyka(pid)
    if not row:
        return jsonify({"error": "Nie znaleziono praktyki."}), 404
    out = dict(row)
    out["dokumenty"] = [row_to_dict(d) for d in models.dokumenty_praktyki(pid)]
    return jsonify(out)


@api_bp.post("/internships")
@api_role("dziekanat")
def api_internship_create():
    data = request.get_json(silent=True) or {}
    if not data.get("student_id"):
        return jsonify({"error": "Pole 'student_id' jest wymagane."}), 400
    if not query_one("SELECT 1 FROM users WHERE id=? AND rola='student'",
                     (data["student_id"],)):
        return jsonify({"error": "Wskazany student nie istnieje."}), 400
    pid = models.create_praktyka(
        data["student_id"],
        specjalnosc=data.get("specjalnosc"),
        rok_akademicki=data.get("rok_akademicki"),
        data_od=data.get("data_od"), data_do=data.get("data_do"),
        opiekun_uczelniany_id=data.get("opiekun_uczelniany_id"),
        opiekun_zakladowy_id=data.get("opiekun_zakladowy_id"),
    )
    return jsonify(dict(models.get_praktyka(pid))), 201


# ============================================================================
#  DOKUMENTY (documents)
# ============================================================================
@api_bp.get("/documents")
@api_login_required
def api_documents():
    praktyka_id = request.args.get("praktyka_id", type=int)
    student_id = request.args.get("student_id", type=int)
    status = request.args.get("status")
    typ = request.args.get("typ")
    limit, offset, page, per_page = paginacja()

    sql = ("SELECT d.id, d.praktyka_id, d.typ, d.status, d.ocena, d.zaktualizowano "
           "FROM dokumenty d JOIN praktyki p ON p.id=d.praktyka_id WHERE 1=1")
    params = []
    if praktyka_id:
        sql += " AND d.praktyka_id=?"; params.append(praktyka_id)
    if student_id:
        sql += " AND p.student_id=?"; params.append(student_id)
    if status:
        sql += " AND d.status=?"; params.append(status)
    if typ:
        sql += " AND d.typ=?"; params.append(typ)
    sql += " ORDER BY d.zaktualizowano DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    rows = query_all(sql, tuple(params))
    return jsonify({"page": page, "per_page": per_page,
                    "count": len(rows), "data": [dict(r) for r in rows]})


@api_bp.get("/documents/<int:dok_id>")
@api_login_required
def api_document(dok_id):
    row = models.get_dokument(dok_id)
    if not row:
        return jsonify({"error": "Nie znaleziono dokumentu."}), 404
    return jsonify(row_to_dict(row))


@api_bp.post("/documents")
@api_login_required
def api_document_create():
    data = request.get_json(silent=True) or {}
    typ = data.get("typ")
    praktyka_id = data.get("praktyka_id")
    if typ not in meta.DOKUMENTY:
        return jsonify({"error": f"Nieznany typ dokumentu. Dozwolone: "
                                 f"{list(meta.DOKUMENTY)}"}), 400
    if not praktyka_id or not models.get_praktyka(praktyka_id):
        return jsonify({"error": "Nieprawidłowe 'praktyka_id'."}), 400

    dok_id = models.utworz_lub_pobierz_dokument(praktyka_id, typ, current_user().id)
    if "dane" in data and isinstance(data["dane"], dict):
        models.zapisz_dane_dokumentu(dok_id, data["dane"])
    return jsonify(row_to_dict(models.get_dokument(dok_id))), 201


@api_bp.route("/documents/<int:dok_id>", methods=["PUT", "PATCH"])
@api_login_required
def api_document_update(dok_id):
    dok = models.get_dokument(dok_id)
    if not dok:
        return jsonify({"error": "Nie znaleziono dokumentu."}), 404
    data = request.get_json(silent=True) or {}
    if "dane" not in data or not isinstance(data["dane"], dict):
        return jsonify({"error": "Wymagany obiekt 'dane'."}), 400
    models.zapisz_dane_dokumentu(dok_id, data["dane"])
    return jsonify(row_to_dict(models.get_dokument(dok_id)))


@api_bp.delete("/documents/<int:dok_id>")
@api_role("dziekanat", "student")
def api_document_delete(dok_id):
    dok = models.get_dokument(dok_id)
    if not dok:
        return jsonify({"error": "Nie znaleziono dokumentu."}), 404
    execute("DELETE FROM dokumenty WHERE id=?", (dok_id,))
    return "", 204


# --- Obsługa błędów API w formacie JSON -------------------------------------
@api_bp.errorhandler(404)
def api_404(e):
    return jsonify({"error": "Zasób nie istnieje."}), 404


@api_bp.errorhandler(400)
def api_400(e):
    return jsonify({"error": "Błędne żądanie."}), 400
