"""
Logika danych — funkcje operujące na bazie + lekkie klasy Pythona do
przetwarzania danych (wymóg etapu 2: "wykorzystanie klas Python").

Tu trzyma się reguły domenowe: walidacja e-maila, walidacja workflow,
zliczanie dni dziennika, sprawdzanie kompletności efektów (13) itd.
"""

import re
import json
from werkzeug.security import generate_password_hash, check_password_hash

from database import query_all, query_one, execute
import forms_meta as meta


# ----------------------------------------------------------------------------
#  Walidacja
# ----------------------------------------------------------------------------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Domeny e-mailowe uczelni — pilnowane przy zakładaniu kont.
DOMENA_STUDENT = "@student.ans-elblag.pl"
DOMENA_PRACOWNIK = "@ans-elblag.pl"


def poprawny_email(email: str) -> bool:
    """Prosta, ale skuteczna walidacja adresu e-mail."""
    return bool(email and EMAIL_RE.match(email.strip()))


def waliduj_email_dla_roli(email: str, rola: str) -> str | None:
    """
    Sprawdza, czy adres e-mail pasuje do roli zgodnie z zasadami ANS:
      - student            → @student.ans-elblag.pl
      - opiekun_uczelniany → @ans-elblag.pl
      - dziekanat          → @ans-elblag.pl
      - opiekun_zakladowy  → dowolna domena ZEWNĘTRZNA
                             (nie @ans-elblag.pl ani @student.ans-elblag.pl)

    Zwraca komunikat błędu (po polsku) lub None, jeśli email jest poprawny.
    """
    if not poprawny_email(email):
        return "Nieprawidłowy format adresu e-mail."

    email = email.strip().lower()

    if rola == "student":
        if not email.endswith(DOMENA_STUDENT):
            return (f"Konta studenckie muszą mieć adres w domenie "
                    f"{DOMENA_STUDENT} (np. 21310{DOMENA_STUDENT}).")
    elif rola in ("opiekun_uczelniany", "dziekanat"):
        if not email.endswith(DOMENA_PRACOWNIK):
            return (f"Konta pracownicze muszą mieć adres w domenie "
                    f"{DOMENA_PRACOWNIK}.")
        # Pracownik nie może używać puli studenckiej
        if email.endswith(DOMENA_STUDENT):
            return f"Adres {DOMENA_STUDENT} jest zarezerwowany dla studentów."
    elif rola == "opiekun_zakladowy":
        if email.endswith(DOMENA_PRACOWNIK) or email.endswith(DOMENA_STUDENT):
            return ("Opiekun zakładowy powinien używać adresu z domeny "
                    "swojej firmy, a nie z domeny uczelni.")
    return None


# ----------------------------------------------------------------------------
#  Klasa pomocnicza: użytkownik (opakowuje wiersz z bazy)
# ----------------------------------------------------------------------------
class User:
    def __init__(self, row):
        self.id = row["id"]
        self.email = row["email"]
        self.imie = row["imie"]
        self.nazwisko = row["nazwisko"]
        self.rola = row["rola"]
        self.nr_albumu = row["nr_albumu"]
        self.pierwszy_login = bool(row["pierwszy_login"])
        self._haslo_hash = row["haslo_hash"]

    @property
    def pelne_imie(self):
        return f"{self.imie} {self.nazwisko}"

    @property
    def rola_pl(self):
        return meta.ROLE_NAZWY.get(self.rola, self.rola)

    def sprawdz_haslo(self, haslo: str) -> bool:
        return bool(self._haslo_hash) and check_password_hash(self._haslo_hash, haslo)

    def jest_recenzentem(self) -> bool:
        return self.rola in meta.ROLE_RECENZUJACE


# ----------------------------------------------------------------------------
#  Użytkownicy
# ----------------------------------------------------------------------------
def get_user(user_id):
    row = query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return User(row) if row else None


def get_user_by_email(email):
    row = query_one("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    return User(row) if row else None


def create_user(email, imie, nazwisko, rola, haslo=None, nr_albumu=None,
                oauth_provider=None, oauth_sub=None):
    haslo_hash = generate_password_hash(haslo) if haslo else None
    return execute(
        """INSERT INTO users (email, haslo_hash, imie, nazwisko, rola, nr_albumu,
                              oauth_provider, oauth_sub)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (email.strip().lower(), haslo_hash, imie, nazwisko, rola, nr_albumu,
         oauth_provider, oauth_sub),
    )


def lista_studentow():
    rows = query_all("SELECT * FROM users WHERE rola = 'student' ORDER BY nazwisko, imie")
    return [User(r) for r in rows]


def lista_uzytkownikow():
    return query_all("SELECT * FROM users ORDER BY rola, nazwisko, imie")


# ----------------------------------------------------------------------------
#  Praktyki
# ----------------------------------------------------------------------------
def get_praktyka(praktyka_id):
    return query_one(
        """SELECT p.*,
                  s.imie  AS student_imie,  s.nazwisko AS student_nazwisko, s.nr_albumu,
                  ou.imie AS ou_imie, ou.nazwisko AS ou_nazwisko,
                  oz.imie AS oz_imie, oz.nazwisko AS oz_nazwisko,
                  f.nazwa AS firma_nazwa, f.adres AS firma_adres
           FROM praktyki p
           JOIN users s        ON s.id = p.student_id
           LEFT JOIN users ou  ON ou.id = p.opiekun_uczelniany_id
           LEFT JOIN users oz  ON oz.id = p.opiekun_zakladowy_id
           LEFT JOIN firmy f   ON f.id = p.firma_id
           WHERE p.id = ?""",
        (praktyka_id,),
    )


def praktyki_studenta(student_id):
    return query_all(
        """SELECT p.*, f.nazwa AS firma_nazwa
           FROM praktyki p LEFT JOIN firmy f ON f.id = p.firma_id
           WHERE p.student_id = ? ORDER BY p.utworzono DESC""",
        (student_id,),
    )


def praktyki_opiekuna(opiekun_id):
    """Praktyki, w których dany użytkownik jest opiekunem (uczelnianym lub zakładowym)."""
    return query_all(
        """SELECT p.*, s.imie AS student_imie, s.nazwisko AS student_nazwisko,
                  s.nr_albumu, f.nazwa AS firma_nazwa
           FROM praktyki p
           JOIN users s      ON s.id = p.student_id
           LEFT JOIN firmy f ON f.id = p.firma_id
           WHERE p.opiekun_uczelniany_id = ? OR p.opiekun_zakladowy_id = ?
           ORDER BY p.utworzono DESC""",
        (opiekun_id, opiekun_id),
    )


def wszystkie_praktyki():
    return query_all(
        """SELECT p.*, s.imie AS student_imie, s.nazwisko AS student_nazwisko,
                  s.nr_albumu, f.nazwa AS firma_nazwa
           FROM praktyki p
           JOIN users s      ON s.id = p.student_id
           LEFT JOIN firmy f ON f.id = p.firma_id
           ORDER BY p.utworzono DESC"""
    )


def create_praktyka(student_id, **kwargs):
    pola = ["specjalnosc", "rok_akademicki", "data_od", "data_do",
            "opiekun_uczelniany_id", "opiekun_zakladowy_id", "firma_id",
            "porozumienie_nr"]
    kolumny = ["student_id"] + [p for p in pola if p in kwargs]
    wartosci = [student_id] + [kwargs[p] for p in pola if p in kwargs]
    placeholders = ", ".join("?" for _ in kolumny)
    return execute(
        f"INSERT INTO praktyki ({', '.join(kolumny)}) VALUES ({placeholders})",
        tuple(wartosci),
    )


# ----------------------------------------------------------------------------
#  Dokumenty (formularze)
# ----------------------------------------------------------------------------
def get_dokument(dok_id):
    return query_one(
        """SELECT d.*, p.student_id, p.opiekun_uczelniany_id, p.opiekun_zakladowy_id
           FROM dokumenty d JOIN praktyki p ON p.id = d.praktyka_id
           WHERE d.id = ?""",
        (dok_id,),
    )


def dokumenty_praktyki(praktyka_id):
    return query_all(
        "SELECT * FROM dokumenty WHERE praktyka_id = ? ORDER BY typ",
        (praktyka_id,),
    )


def dokument_danego_typu(praktyka_id, typ):
    """Zwraca dokument danego typu dla praktyki (zakładamy 1 dokument na typ)."""
    return query_one(
        "SELECT * FROM dokumenty WHERE praktyka_id = ? AND typ = ?",
        (praktyka_id, typ),
    )


def utworz_lub_pobierz_dokument(praktyka_id, typ, autor_id):
    """Tworzy pusty dokument danego typu (Draft) albo zwraca istniejący."""
    istn = dokument_danego_typu(praktyka_id, typ)
    if istn:
        return istn["id"]
    return execute(
        "INSERT INTO dokumenty (praktyka_id, typ, autor_id) VALUES (?, ?, ?)",
        (praktyka_id, typ, autor_id),
    )


def zapisz_dane_dokumentu(dok_id, dane: dict):
    execute(
        "UPDATE dokumenty SET dane_json = ?, zaktualizowano = datetime('now') WHERE id = ?",
        (json.dumps(dane, ensure_ascii=False), dok_id),
    )


def dane_dokumentu(dok_row) -> dict:
    """Bezpiecznie parsuje kolumnę dane_json do słownika."""
    try:
        return json.loads(dok_row["dane_json"] or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}


# ----------------------------------------------------------------------------
#  Workflow — zmiana statusu z walidacją i zapisem do logu
# ----------------------------------------------------------------------------
def zmien_status(dok_id, nowy_status, uzytkownik_id, komentarz=None,
                 ocena=None) -> tuple[bool, str]:
    """
    Zmienia status dokumentu, jeśli przejście jest dozwolone.
    Zwraca (sukces, komunikat).
    """
    dok = get_dokument(dok_id)
    if not dok:
        return False, "Dokument nie istnieje."

    obecny = dok["status"]
    if nowy_status not in meta.PRZEJSCIA.get(obecny, []):
        return False, f"Niedozwolone przejście: {obecny} → {nowy_status}."

    execute(
        """UPDATE dokumenty
           SET status = ?, recenzent_id = ?, komentarz_recenzenta = COALESCE(?, komentarz_recenzenta),
               ocena = COALESCE(?, ocena), zaktualizowano = datetime('now')
           WHERE id = ?""",
        (nowy_status, uzytkownik_id, komentarz, ocena, dok_id),
    )
    execute(
        """INSERT INTO workflow_log (dokument_id, status_z, status_na, uzytkownik_id, komentarz)
           VALUES (?, ?, ?, ?, ?)""",
        (dok_id, obecny, nowy_status, uzytkownik_id, komentarz),
    )
    return True, f"Status zmieniony na „{meta.STATUS_PL.get(nowy_status, nowy_status)}”."


def historia_workflow(dok_id):
    return query_all(
        """SELECT w.*, u.imie, u.nazwisko
           FROM workflow_log w LEFT JOIN users u ON u.id = w.uzytkownik_id
           WHERE w.dokument_id = ? ORDER BY w.kiedy""",
        (dok_id,),
    )


# ----------------------------------------------------------------------------
#  Reguły walidacji danych formularzy (etap 7: walidacja SQL/danych)
# ----------------------------------------------------------------------------
def waliduj_dziennik(dane: dict) -> list[str]:
    """Sprawdza dziennik: liczbę dni, kompletność wpisów, poprawność nr efektów."""
    bledy = []
    wpisy = dane.get("wpisy", [])
    if not wpisy:
        bledy.append("Dziennik nie zawiera żadnych wpisów.")
        return bledy

    dozwolone_efekty = {kod for kod, _ in meta.EFEKTY}
    for i, w in enumerate(wpisy, start=1):
        if not w.get("opis", "").strip():
            bledy.append(f"Wpis {i}: brak opisu wykonanych prac.")
        # nr efektów podane jako np. "01, 05" — sprawdzamy poprawność
        for kod in [k.strip().zfill(2) for k in str(w.get("efekty", "")).split(",") if k.strip()]:
            if kod not in dozwolone_efekty:
                bledy.append(f"Wpis {i}: nieznany numer efektu „{kod}” (dozwolone 01–13).")

    if len(wpisy) > 120:
        bledy.append(f"Dziennik ma {len(wpisy)} wpisów — praktyka trwa maksymalnie 120 dni.")
    return bledy


def waliduj_efekty(dane: dict) -> list[str]:
    """Potwierdzenie efektów musi obejmować wszystkie 13 efektów."""
    bledy = []
    potw = dane.get("potwierdzenia", {})
    if len(potw) < len(meta.EFEKTY):
        brak = [kod for kod, _ in meta.EFEKTY if kod not in potw]
        bledy.append(f"Brak rozstrzygnięcia dla efektów: {', '.join(brak)} (wymagane wszystkie 13).")
    return bledy
