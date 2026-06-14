"""
Trasy główne: strona startowa, pulpit (dashboard) zależny od roli, profil,
podstrony informacyjne (kontakt, regulamin, zasady).
"""

from flask import Blueprint, render_template, redirect, url_for

import models
import forms_meta as meta
from auth import login_required, current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    """Strona główna — krótkie powitanie i opis aplikacji."""
    return render_template("strona_glowna.html", u=current_user())


@main_bp.route("/praktyki")
@main_bp.route("/dashboard")  # zachowujemy stary adres dla kompatybilności
@login_required
def dashboard():
    u = current_user()

    if u.rola == "student":
        praktyki = models.praktyki_studenta(u.id)
        widok = []
        for p in praktyki:
            dokumenty = models.dokumenty_praktyki(p["id"])
            stan = {d["typ"]: d for d in dokumenty}
            widok.append({"praktyka": p, "stan": stan})
        return render_template("dashboard_student.html", praktyki=widok,
                               DOK=meta.DOKUMENTY, KOLEJ=meta.DOKUMENTY_KOLEJNOSC,
                               STATUS_PL=meta.STATUS_PL)

    if u.rola in ("opiekun_uczelniany", "opiekun_zakladowy"):
        praktyki = models.praktyki_opiekuna(u.id)
        do_recenzji = []
        for p in praktyki:
            for d in models.dokumenty_praktyki(p["id"]):
                if d["status"] in ("Submitted", "Under Review"):
                    do_recenzji.append({"dok": d, "praktyka": p})
        return render_template("dashboard_opiekun.html", praktyki=praktyki,
                               do_recenzji=do_recenzji, DOK=meta.DOKUMENTY,
                               STATUS_PL=meta.STATUS_PL)

    # dziekanat (administrator)
    praktyki = models.wszystkie_praktyki()
    uzytkownicy = models.lista_uzytkownikow()
    statystyki = {
        "praktyki": len(praktyki),
        "studenci": sum(1 for x in uzytkownicy if x["rola"] == "student"),
        "opiekunowie": sum(1 for x in uzytkownicy if x["rola"].startswith("opiekun")),
    }
    return render_template("dashboard_dziekanat.html", praktyki=praktyki,
                           uzytkownicy=uzytkownicy, statystyki=statystyki,
                           ROLE_PL=meta.ROLE_NAZWY, STATUS_PL=meta.STATUS_PL)


@main_bp.route("/profil")
@login_required
def profil():
    return render_template("profil.html", u=current_user())


@main_bp.route("/kontakt")
@login_required
def kontakt():
    return render_template("kontakt.html")


@main_bp.route("/regulamin")
@login_required
def regulamin():
    return render_template("regulamin.html")


@main_bp.route("/zasady")
@login_required
def zasady():
    return render_template("zasady.html")
