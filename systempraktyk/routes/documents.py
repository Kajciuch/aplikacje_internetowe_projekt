"""
Trasy dokumentów (formularzy): edycja, podgląd, workflow i eksport PDF.

Uprawnienia:
- autor (student lub opiekun zakładowy dla "efekty") edytuje, gdy status = Draft/Rejected,
- opiekunowie i dziekanat recenzują (zmieniają status, wystawiają ocenę),
- dziekanat (administrator) ma dostęp do wszystkiego.
"""

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, abort, send_file)

import models
import forms_meta as meta
import pdf_utils
from auth import login_required, current_user

dok_bp = Blueprint("dok", __name__)


# ----------------------------------------------------------------------------
#  Pomocnicze: uprawnienia
# ----------------------------------------------------------------------------
def _dostep(prakt, u):
    """Czy użytkownik może oglądać praktykę/dokumenty tej praktyki?"""
    if u.rola == "dziekanat":
        return True
    return u.id in (prakt["student_id"], prakt["opiekun_uczelniany_id"],
                    prakt["opiekun_zakladowy_id"])


def _moze_edytowac(dok, u):
    if u.rola == "dziekanat":
        return True
    autor_rola = meta.DOKUMENTY[dok["typ"]]["autor"]
    # edycja tylko przez właściwą rolę i tylko w stanie roboczym
    return u.rola == autor_rola and dok["status"] in ("Draft", "Rejected")


def _moze_recenzowac(dok, prakt, u):
    if u.rola == "dziekanat":
        return True
    if u.rola not in meta.ROLE_RECENZUJACE:
        return False
    return u.id in (prakt["opiekun_uczelniany_id"], prakt["opiekun_zakladowy_id"])


# ----------------------------------------------------------------------------
#  Parsowanie formularzy → słownik danych (per typ dokumentu)
# ----------------------------------------------------------------------------
def _parsuj(typ, form):
    if typ == "karta":
        return {"ocena_opisowa": form.get("ocena_opisowa", "").strip(),
                "uwagi": form.get("uwagi", "").strip()}

    if typ == "program":
        prace = {kod: form.get(f"praca_{kod}", "").strip() for kod, _ in meta.EFEKTY}
        dzialy = form.getlist("harm_dzial[]")
        dni = form.getlist("harm_dni[]")
        harmonogram = [{"dzial": d.strip(), "dni": n.strip()}
                       for d, n in zip(dzialy, dni) if d.strip() or n.strip()]
        return {"prace_efekty": prace, "harmonogram": harmonogram}

    if typ == "dziennik":
        dni = form.getlist("wpis_dzien[]")
        daty = form.getlist("wpis_data[]")
        opisy = form.getlist("wpis_opis[]")
        efekty = form.getlist("wpis_efekty[]")
        wpisy = []
        for dz, dt, op, ef in zip(dni, daty, opisy, efekty):
            if op.strip() or dt.strip():
                wpisy.append({"dzien": dz.strip(), "data": dt.strip(),
                              "opis": op.strip(), "efekty": ef.strip()})
        return {"wpisy": wpisy}

    if typ == "efekty":
        potw = {kod: form.get(f"efekt_{kod}", "") for kod, _ in meta.EFEKTY
                if form.get(f"efekt_{kod}")}
        return {"liczba_godzin": form.get("liczba_godzin", "").strip(),
                "potwierdzenia": potw,
                "opinia_uczelniana": form.get("opinia_uczelniana", "").strip()}

    if typ == "sprawozdanie":
        return {"charakterystyka": form.get("charakterystyka", "").strip(),
                "opis_prac": form.get("opis_prac", "").strip(),
                "samoocena": form.get("samoocena", "").strip()}

    if typ == "ankieta":
        odp = {str(i): form.get(f"pyt_{i}", "") for i in range(1, len(meta.ANKIETA_PYTANIA) + 1)
               if form.get(f"pyt_{i}")}
        return {"odpowiedzi": odp, "uwagi": form.get("uwagi", "").strip(),
                "metryczka": {"rok": form.get("m_rok", ""), "kierunek": "Informatyka",
                              "forma": form.get("m_forma", ""), "semestr": form.get("m_semestr", ""),
                              "godziny": form.get("m_godziny", "")}}

    return {}


def _waliduj(typ, dane):
    if typ == "dziennik":
        return models.waliduj_dziennik(dane)
    if typ == "efekty":
        return models.waliduj_efekty(dane)
    return []


# ----------------------------------------------------------------------------
#  Widok praktyki (lista jej dokumentów)
# ----------------------------------------------------------------------------
@dok_bp.route("/praktyka/<int:pid>")
@login_required
def praktyka(pid):
    prakt = models.get_praktyka(pid)
    if not prakt:
        abort(404)
    u = current_user()
    if not _dostep(prakt, u):
        abort(403)

    dokumenty = {d["typ"]: d for d in models.dokumenty_praktyki(pid)}
    return render_template("praktyka.html", prakt=prakt, dokumenty=dokumenty,
                           DOK=meta.DOKUMENTY, KOLEJ=meta.DOKUMENTY_KOLEJNOSC,
                           STATUS_PL=meta.STATUS_PL, u=u)


# Utworzenie (jeśli trzeba) i przejście do dokumentu danego typu.
@dok_bp.route("/praktyka/<int:pid>/formularz/<typ>")
@login_required
def otworz_formularz(pid, typ):
    if typ not in meta.DOKUMENTY:
        abort(404)
    prakt = models.get_praktyka(pid)
    if not prakt or not _dostep(prakt, current_user()):
        abort(403)
    dok_id = models.utworz_lub_pobierz_dokument(pid, typ, current_user().id)
    return redirect(url_for("dok.podglad", dok_id=dok_id))


# ----------------------------------------------------------------------------
#  Podgląd dokumentu + historia workflow + akcje
# ----------------------------------------------------------------------------
@dok_bp.route("/dokument/<int:dok_id>")
@login_required
def podglad(dok_id):
    dok = models.get_dokument(dok_id)
    if not dok:
        abort(404)
    prakt = models.get_praktyka(dok["praktyka_id"])
    u = current_user()
    if not _dostep(prakt, u):
        abort(403)

    return render_template("dokument_podglad.html", dok=dok, prakt=prakt,
                           dane=models.dane_dokumentu(dok),
                           historia=models.historia_workflow(dok_id),
                           info=meta.DOKUMENTY[dok["typ"]], EFEKTY=meta.EFEKTY,
                           PYTANIA=meta.ANKIETA_PYTANIA, STATUS_PL=meta.STATUS_PL,
                           PRZEJSCIA=meta.PRZEJSCIA,
                           moze_edytowac=_moze_edytowac(dok, u),
                           moze_recenzowac=_moze_recenzowac(dok, prakt, u))


# ----------------------------------------------------------------------------
#  Edycja formularza
# ----------------------------------------------------------------------------
@dok_bp.route("/dokument/<int:dok_id>/edytuj", methods=["GET", "POST"])
@login_required
def edytuj(dok_id):
    dok = models.get_dokument(dok_id)
    if not dok:
        abort(404)
    prakt = models.get_praktyka(dok["praktyka_id"])
    u = current_user()
    if not _moze_edytowac(dok, u):
        abort(403)

    typ = dok["typ"]
    if request.method == "POST":
        dane = _parsuj(typ, request.form)
        models.zapisz_dane_dokumentu(dok_id, dane)
        bledy = _waliduj(typ, dane)
        if bledy and request.form.get("akcja") == "zloz":
            for b in bledy:
                flash(b, "error")
            flash("Zapisano szkic, ale są błędy — popraw je przed złożeniem.", "warning")
            return redirect(url_for("dok.edytuj", dok_id=dok_id))

        flash("Zapisano zmiany.", "success")
        # Jeśli student kliknął „Zapisz i złóż”, od razu próbujemy złożyć.
        if request.form.get("akcja") == "zloz":
            return redirect(url_for("dok.zloz", dok_id=dok_id))
        return redirect(url_for("dok.podglad", dok_id=dok_id))

    return render_template(f"form_{typ}.html", dok=dok, prakt=prakt,
                           dane=models.dane_dokumentu(dok), info=meta.DOKUMENTY[typ],
                           EFEKTY=meta.EFEKTY, PYTANIA=meta.ANKIETA_PYTANIA,
                           SKALA=meta.ANKIETA_SKALA)


# ----------------------------------------------------------------------------
#  Workflow: złożenie przez studenta
# ----------------------------------------------------------------------------
@dok_bp.route("/dokument/<int:dok_id>/zloz", methods=["POST", "GET"])
@login_required
def zloz(dok_id):
    dok = models.get_dokument(dok_id)
    if not dok:
        abort(404)
    u = current_user()
    autor_rola = meta.DOKUMENTY[dok["typ"]]["autor"]
    if not (u.rola == autor_rola or u.rola == "dziekanat"):
        abort(403)

    # Walidacja przed złożeniem.
    dane = models.dane_dokumentu(dok)
    bledy = _waliduj(dok["typ"], dane)
    if bledy:
        for b in bledy:
            flash(b, "error")
        return redirect(url_for("dok.edytuj", dok_id=dok_id))

    ok, kom = models.zmien_status(dok_id, "Submitted", u.id, "Złożono dokument.")
    flash(kom, "success" if ok else "error")
    return redirect(url_for("dok.podglad", dok_id=dok_id))


# ----------------------------------------------------------------------------
#  Workflow: recenzja (opiekun / dziekanat)
# ----------------------------------------------------------------------------
@dok_bp.route("/dokument/<int:dok_id>/recenzja", methods=["POST"])
@login_required
def recenzja(dok_id):
    dok = models.get_dokument(dok_id)
    if not dok:
        abort(404)
    prakt = models.get_praktyka(dok["praktyka_id"])
    u = current_user()
    if not _moze_recenzowac(dok, prakt, u):
        abort(403)

    nowy_status = request.form.get("status")
    komentarz = request.form.get("komentarz", "").strip()
    ocena = request.form.get("ocena", "").strip() or None

    ok, kom = models.zmien_status(dok_id, nowy_status, u.id, komentarz, ocena)
    flash(kom, "success" if ok else "error")
    return redirect(url_for("dok.podglad", dok_id=dok_id))


# ----------------------------------------------------------------------------
#  Eksport PDF (etap 11)
# ----------------------------------------------------------------------------
@dok_bp.route("/dokument/<int:dok_id>/pdf")
@login_required
def pdf(dok_id):
    dok = models.get_dokument(dok_id)
    if not dok:
        abort(404)
    prakt = models.get_praktyka(dok["praktyka_id"])
    if not _dostep(prakt, current_user()):
        abort(403)

    buf = pdf_utils.generuj_pdf(dok, prakt)
    nazwa = f"{meta.DOKUMENTY[dok['typ']]['nazwa'].replace(' ', '_')}_{dok_id}.pdf"
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=nazwa)
