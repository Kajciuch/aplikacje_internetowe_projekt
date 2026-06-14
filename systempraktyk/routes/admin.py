"""
Panel administracyjny dziekanatu.

Pozwala dziekanatowi:
  - tworzyć nowych studentów oraz opiekunów (uczelnianych i zakładowych),
  - dodawać firmy (zakłady pracy),
  - tworzyć praktyki i przypisywać do nich studenta, firmę oraz opiekunów,
  - zalogować się jako dowolny inny użytkownik (impersonacja) — wygodne
    dla testowania widoków z perspektywy studenta lub opiekuna.

Wszystkie trasy chronione `@role_required("dziekanat")`.
"""

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, session, abort)

from auth import login_required, role_required, current_user
from database import query_all, query_one, execute
import models
import forms_meta as meta

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ----------------------------------------------------------------------------
#  Tworzenie użytkownika (student / opiekun)
# ----------------------------------------------------------------------------
@admin_bp.route("/uzytkownicy", methods=["GET"])
@role_required("dziekanat")
def lista_uzytkownikow():
    """Lista wszystkich kont — punkt wejścia do tworzenia i impersonacji."""
    uzytkownicy = models.lista_uzytkownikow()
    return render_template("admin/uzytkownicy.html",
                           uzytkownicy=uzytkownicy,
                           ROLE_PL=meta.ROLE_NAZWY)


@admin_bp.route("/uzytkownicy/nowy", methods=["GET", "POST"])
@role_required("dziekanat")
def nowy_uzytkownik():
    """Formularz tworzenia nowego konta (dowolnej roli)."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        imie = request.form.get("imie", "").strip()
        nazwisko = request.form.get("nazwisko", "").strip()
        rola = request.form.get("rola", "").strip()
        nr_albumu = request.form.get("nr_albumu", "").strip() or None
        haslo = request.form.get("haslo", "").strip()

        bledy = []
        blad_email = models.waliduj_email_dla_roli(email, rola) if rola in meta.ROLE_NAZWY else "Nieprawidłowa rola."
        if blad_email:
            bledy.append(blad_email)
        if not imie or not nazwisko:
            bledy.append("Imię i nazwisko są wymagane.")
        if rola == "student" and not nr_albumu:
            bledy.append("Numer albumu jest wymagany dla studenta.")
        if not haslo or len(haslo) < 6:
            bledy.append("Hasło musi mieć co najmniej 6 znaków.")
        if not blad_email and models.get_user_by_email(email):
            bledy.append(f"Użytkownik z adresem {email} już istnieje.")

        if bledy:
            for b in bledy:
                flash(b, "error")
        else:
            uid = models.create_user(email=email, imie=imie, nazwisko=nazwisko,
                                     rola=rola, haslo=haslo, nr_albumu=nr_albumu)
            flash(f"Utworzono konto: {imie} {nazwisko} ({meta.ROLE_NAZWY[rola]}).",
                  "success")
            return redirect(url_for("admin.lista_uzytkownikow"))

    return render_template("admin/nowy_uzytkownik.html", ROLE_PL=meta.ROLE_NAZWY)


# ----------------------------------------------------------------------------
#  Firmy (zakłady pracy)
# ----------------------------------------------------------------------------
@admin_bp.route("/firmy", methods=["GET"])
@role_required("dziekanat")
def lista_firm():
    firmy = query_all("SELECT * FROM firmy ORDER BY nazwa")
    return render_template("admin/firmy.html", firmy=firmy)


@admin_bp.route("/firmy/nowa", methods=["GET", "POST"])
@role_required("dziekanat")
def nowa_firma():
    if request.method == "POST":
        nazwa = request.form.get("nazwa", "").strip()
        adres = request.form.get("adres", "").strip()
        nip = request.form.get("nip", "").strip() or None

        if not nazwa:
            flash("Nazwa firmy jest wymagana.", "error")
        else:
            execute("INSERT INTO firmy (nazwa, adres, nip) VALUES (?, ?, ?)",
                    (nazwa, adres, nip))
            flash(f"Dodano firmę: {nazwa}.", "success")
            return redirect(url_for("admin.lista_firm"))

    return render_template("admin/nowa_firma.html")


# ----------------------------------------------------------------------------
#  Praktyki — tworzenie i przydzielanie
# ----------------------------------------------------------------------------
@admin_bp.route("/praktyki/nowa", methods=["GET", "POST"])
@role_required("dziekanat")
def nowa_praktyka():
    studenci = models.lista_studentow()
    opiekunowie_u = query_all("SELECT * FROM users WHERE rola = 'opiekun_uczelniany' ORDER BY nazwisko, imie")
    opiekunowie_z = query_all("SELECT * FROM users WHERE rola = 'opiekun_zakladowy' ORDER BY nazwisko, imie")
    firmy = query_all("SELECT * FROM firmy ORDER BY nazwa")

    if request.method == "POST":
        student_id = request.form.get("student_id", type=int)
        firma_id = request.form.get("firma_id", type=int) or None
        ou_id = request.form.get("opiekun_uczelniany_id", type=int) or None
        oz_id = request.form.get("opiekun_zakladowy_id", type=int) or None
        specjalnosc = request.form.get("specjalnosc", "").strip()
        rok = request.form.get("rok_akademicki", "").strip()
        data_od = request.form.get("data_od", "").strip() or None
        data_do = request.form.get("data_do", "").strip() or None
        porozumienie = request.form.get("porozumienie_nr", "").strip()

        if not student_id or not models.get_user(student_id):
            flash("Wybierz istniejącego studenta.", "error")
        elif specjalnosc and specjalnosc not in meta.SPECJALIZACJE:
            flash("Wybrana specjalność jest nieprawidłowa.", "error")
        else:
            pid = models.create_praktyka(
                student_id,
                specjalnosc=specjalnosc or None,
                rok_akademicki=rok or None,
                data_od=data_od, data_do=data_do,
                opiekun_uczelniany_id=ou_id,
                opiekun_zakladowy_id=oz_id,
                firma_id=firma_id,
                porozumienie_nr=porozumienie or None,
            )
            flash("Utworzono praktykę.", "success")
            return redirect(url_for("dok.praktyka", pid=pid))

    return render_template(
        "admin/nowa_praktyka.html",
        studenci=studenci,
        opiekunowie_u=opiekunowie_u,
        opiekunowie_z=opiekunowie_z,
        firmy=firmy,
        SPECJALIZACJE=meta.SPECJALIZACJE,
    )


# ----------------------------------------------------------------------------
#  Impersonacja — „zaloguj się jako"
# ----------------------------------------------------------------------------
@admin_bp.route("/zaloguj-jako/<int:user_id>", methods=["POST"])
@role_required("dziekanat")
def zaloguj_jako(user_id):
    """
    Dziekanat „wchodzi" na konto innego użytkownika.

    Oryginalne user_id zachowujemy w sesji jako `impersonator_id`, żeby
    móc wrócić bez ponownego logowania. Widok jest w pełni „cudzy" —
    aplikacja czyta `session['user_id']`, więc wszystkie uprawnienia,
    dashboardy i widoki działają tak, jakby zalogowany był ten user.
    """
    cel = models.get_user(user_id)
    if not cel:
        abort(404)

    impersonator = current_user()
    # zapamiętaj kim naprawdę jesteśmy
    session["impersonator_id"] = impersonator.id
    session["user_id"] = cel.id
    flash(f"Zalogowano jako {cel.pelne_imie} ({cel.rola_pl}). "
          "Kliknij \"Wróć do swojego konta\" w pasku górnym, aby zakończyć.",
          "info")
    return redirect(url_for("main.dashboard"))


@admin_bp.route("/zakoncz-impersonacje", methods=["POST"])
@login_required
def zakoncz_impersonacje():
    """Wraca do oryginalnego konta dziekanatu."""
    oryg_id = session.pop("impersonator_id", None)
    if not oryg_id:
        flash("Nie jesteś w trybie impersonacji.", "warning")
        return redirect(url_for("main.dashboard"))
    session["user_id"] = oryg_id
    flash("Wróciłeś/wróciłaś do swojego konta dziekanatu.", "success")
    return redirect(url_for("main.dashboard"))
