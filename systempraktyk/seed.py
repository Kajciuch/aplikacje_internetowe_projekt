"""
Inicjalizacja bazy danych + dane demonstracyjne.

Uruchomienie (w aktywnym venv):
    python seed.py

Dane uczelni:
    Akademia Nauk Stosowanych w Elblągu
    Instytut Informatyki Stosowanej im. K. Brzeskiego, kierunek: Informatyka

Konta demo (hasło dla wszystkich: praktyki123):
    21310@student.ans-elblag.pl       — Kaja Thiel (student)
    21342@student.ans-elblag.pl       — Maciej Lewandowski (student)
    21389@student.ans-elblag.pl       — Aleksandra Sobczak (student)
    jan.nowak@ans-elblag.pl           — dr Jan Nowak (opiekun uczelniany)
    anna.kowalczyk@ans-elblag.pl      — dr inż. Anna Kowalczyk (opiekun uczelniany)
    p.zielinski@gevernova.com         — mgr inż. Piotr Zieliński (opiekun GE Vernova)
    t.wojcik@opegieka.pl              — mgr Tomasz Wójcik (opiekun OPEGIEKA)
    m.kowalski@tbmeca.pl              — inż. Marek Kowalski (opiekun TBmeca)
    dziekanat@ans-elblag.pl           — Maria Wiśniewska (dziekanat / admin)
"""

from app import create_app
from database import init_db, execute, query_one
import models
import forms_meta as meta

app = create_app()
HASLO_DEMO = "praktyki123"


def seed_efekty():
    """Wypełnia tabelę efektów (13 z forms_meta)."""
    from database import get_db
    db = get_db()
    for i, (kod, opis) in enumerate(meta.EFEKTY, start=1):
        db.execute("INSERT OR IGNORE INTO efekty (id, kod, opis) VALUES (?, ?, ?)",
                   (i, kod, opis))
    db.commit()
    print(f"  ✓ {len(meta.EFEKTY)} efektów uczenia się")


def seed_uzytkownicy():
    """Tworzy konta dla wszystkich ról — wystarczy do pełnego demo systemu."""
    konta = [
        # studenci (e-mail = indeks @student.ans-elblag.pl)
        ("21310@student.ans-elblag.pl", "Kaja",       "Thiel",       "student",            "21310"),
        ("21342@student.ans-elblag.pl", "Maciej",     "Lewandowski", "student",            "21342"),
        ("21389@student.ans-elblag.pl", "Aleksandra", "Sobczak",     "student",            "21389"),
        # opiekunowie uczelniani (e-mail @ans-elblag.pl)
        ("jan.nowak@ans-elblag.pl",      "Jan",  "Nowak",      "opiekun_uczelniany", None),
        ("anna.kowalczyk@ans-elblag.pl", "Anna", "Kowalczyk",  "opiekun_uczelniany", None),
        # opiekunowie zakładowi (e-mail w domenie firmy)
        ("p.zielinski@gevernova.com", "Piotr",  "Zieliński", "opiekun_zakladowy", None),
        ("t.wojcik@opegieka.pl",      "Tomasz", "Wójcik",    "opiekun_zakladowy", None),
        ("m.kowalski@tbmeca.pl",      "Marek",  "Kowalski",  "opiekun_zakladowy", None),
        # dziekanat
        ("dziekanat@ans-elblag.pl", "Maria", "Wiśniewska", "dziekanat", None),
    ]
    ids = {}
    for email, imie, nazwisko, rola, album in konta:
        u = models.get_user_by_email(email)
        if u:
            uid = u.id
        else:
            uid = models.create_user(email=email, imie=imie, nazwisko=nazwisko,
                                     rola=rola, haslo=HASLO_DEMO, nr_albumu=album)
            print(f"  ✓ {imie} {nazwisko} ({rola})")
        # zapamiętujemy id pod kluczem e-mail (do późniejszego mapowania)
        ids[email] = uid
    return ids


def seed_firmy():
    """3 firmy z Elbląga, w których realnie odbywają się praktyki informatyczne."""
    firmy = [
        ("GE Vernova Polska Sp. z o.o.", "ul. Stoczniowa 2, 82-300 Elbląg", "5783025981"),
        ("OPEGIEKA Sp. z o.o.",          "al. Tysiąclecia 11, 82-300 Elbląg", "5780017175"),
        ("TBmeca Sp. z o.o.",            "ul. Mazurska 16, 82-300 Elbląg",   "5782948320"),
    ]
    ids = {}
    for nazwa, adres, nip in firmy:
        row = query_one("SELECT id FROM firmy WHERE nazwa = ?", (nazwa,))
        if row:
            fid = row["id"]
        else:
            fid = execute("INSERT INTO firmy (nazwa, adres, nip) VALUES (?, ?, ?)",
                          (nazwa, adres, nip))
            print(f"  ✓ firma: {nazwa}")
        ids[nazwa] = fid
    return ids


def seed_praktyka_kai(uids, fids):
    """
    Główna demonstracyjna praktyka: Kaja Thiel w GE Vernova.
    Kompletna, z dokumentami w różnych stanach workflow — żeby od razu po
    seedzie było co oglądać.
    """
    student_id = uids["21310@student.ans-elblag.pl"]
    istn = query_one("SELECT id FROM praktyki WHERE student_id = ?", (student_id,))
    if istn:
        return istn["id"]

    pid = models.create_praktyka(
        student_id,
        specjalnosc=meta.SPECJALIZACJE[0],   # Projektowanie baz danych i oprogramowanie użytkowe
        rok_akademicki="2024/2025",
        data_od="2025-07-01",
        data_do="2025-12-15",
        opiekun_uczelniany_id=uids["jan.nowak@ans-elblag.pl"],
        opiekun_zakladowy_id=uids["p.zielinski@gevernova.com"],
        firma_id=fids["GE Vernova Polska Sp. z o.o."],
        porozumienie_nr="P/2025/042",
    )
    print(f"  ✓ praktyka: Kaja Thiel → GE Vernova (id={pid})")

    # Dokumenty praktyki w różnych stanach
    # 1) Karta — szkic
    dok1 = models.utworz_lub_pobierz_dokument(pid, "karta", student_id)
    models.zapisz_dane_dokumentu(dok1, {"ocena_opisowa": "", "uwagi": ""})

    # 2) Program i harmonogram — złożony do recenzji
    dok2 = models.utworz_lub_pobierz_dokument(pid, "program", student_id)
    models.zapisz_dane_dokumentu(dok2, {
        "prace_efekty": {
            "01": "Wdrożenie warstwy danych aplikacji SCADA zgodnie ze standardami IEC.",
            "02": "Użycie PostgreSQL, Pythona, Dockera, GitLab CI/CD.",
            "03": "Zapoznanie z licencjami open source oraz wymaganiami kontraktowymi.",
            "04": "Szkolenie BHP, praca w środowisku biurowym i hali produkcyjnej.",
            "05": "Czytanie dokumentacji w języku angielskim (PostgreSQL, FastAPI).",
            "06": "Optymalizacja zapytań SQL, indeksy, partycjonowanie.",
            "07": "Pisanie dokumentacji modułów i schematu bazy.",
            "08": "Identyfikacja wąskiego gardła w pobieraniu danych pomiarowych.",
            "09": "Implementacja walidacji wg norm IEC 61850.",
            "10": "Praca w 8-osobowym zespole Scrum (sprinty 2-tygodniowe).",
            "11": "Code review, ochrona danych klienta, NDA.",
            "12": "Spotkania z product ownerem, prezentacje retrospektyw.",
            "13": "Migracja z PostgreSQL 14 na 16 w trakcie praktyki.",
        },
        "harmonogram": [
            {"dzial": "Onboarding i szkolenia BHP",              "dni": "10"},
            {"dzial": "Zespół Data Platform — backend i SQL",    "dni": "60"},
            {"dzial": "Zespół Data Platform — testy i wdrożenie","dni": "30"},
            {"dzial": "Dokumentacja i prezentacja końcowa",      "dni": "20"},
        ],
    })
    models.zmien_status(dok2, "Submitted", student_id, "Złożenie programu praktyki.")

    # 3) Dziennik — szkic z pierwszymi wpisami
    dok3 = models.utworz_lub_pobierz_dokument(pid, "dziennik", student_id)
    models.zapisz_dane_dokumentu(dok3, {
        "wpisy": [
            {"dzien": "1", "data": "2025-07-01", "opis": "Szkolenie BHP, zapoznanie ze strukturą firmy.", "efekty": "03, 04"},
            {"dzien": "2", "data": "2025-07-02", "opis": "Konfiguracja środowiska deweloperskiego (Docker, VS Code, dostępy do GitLab).", "efekty": "02, 04"},
            {"dzien": "3", "data": "2025-07-03", "opis": "Wprowadzenie do projektu Data Platform, przegląd schematu bazy.", "efekty": "07, 10"},
        ],
    })

    # 4) Sprawozdanie — zatwierdzone z oceną 5
    dok4 = models.utworz_lub_pobierz_dokument(pid, "sprawozdanie", student_id)
    models.zapisz_dane_dokumentu(dok4, {
        "charakterystyka": (
            "GE Vernova Polska Sp. z o.o. to dawna część koncernu GE działająca w sektorze "
            "energetyki, z oddziałem w Elblągu skupiającym się na systemach SCADA i "
            "platformach danych dla sieci elektroenergetycznych. Praktykę odbyłam w "
            "dziale Data Platform liczącym 8 osób (architekt, 4 deweloperów, 2 inżynierów "
            "QA, project manager)."
        ),
        "opis_prac": (
            "W trakcie 120 dni roboczych uczestniczyłam w pracach zespołu nad platformą "
            "agregującą dane pomiarowe ze stacji elektroenergetycznych. Do moich zadań "
            "należała: optymalizacja zapytań SQL (skrócenie czasu raportu z 12 s do 1.4 s "
            "dzięki indeksom partycjonowanym), migracja schematu z PostgreSQL 14 na 16, "
            "pisanie testów integracyjnych w pytest, dokumentacja modułu importu CSV w "
            "Markdown, code review pull-requestów koleżanek z zespołu."
        ),
        "samoocena": (
            "Osiągnęłam wszystkie 13 efektów uczenia się przewidzianych programem "
            "praktyki. Najwięcej nauczyłam się przy efektach 06 (technologie bazodanowe), "
            "08 (identyfikacja problemów) i 10 (praca w zespole Scrum). Praktyka utwierdziła "
            "mnie w przekonaniu, że specjalność „Projektowanie baz danych i oprogramowanie "
            "użytkowe” odpowiada moim zainteresowaniom zawodowym."
        ),
    })
    models.zmien_status(dok4, "Submitted",    student_id,                          "Złożenie sprawozdania.")
    models.zmien_status(dok4, "Under Review", uids["jan.nowak@ans-elblag.pl"],    "Rozpoczęcie recenzji.")
    models.zmien_status(dok4, "Approved",     uids["jan.nowak@ans-elblag.pl"],    "Sprawozdanie kompletne, opisy konkretne.", ocena="5")

    print("  ✓ dokumenty Kai (karta, program, dziennik, sprawozdanie) w różnych stanach")
    return pid


def main():
    with app.app_context():
        # 1) Inicjalizacja schematu
        init_db()
        print("Baza danych:")
        print(f"  plik: {app.config['DATABASE']}")
        print("  schemat: OK\n")

        print("Wpisuję dane demonstracyjne:")
        seed_efekty()
        uids = seed_uzytkownicy()
        fids = seed_firmy()
        seed_praktyka_kai(uids, fids)

        print("\n✓ Gotowe. Konta demonstracyjne (hasło: " + HASLO_DEMO + "):")
        print("  21310@student.ans-elblag.pl    → Kaja Thiel")
        print("  21342@student.ans-elblag.pl    → Maciej Lewandowski")
        print("  21389@student.ans-elblag.pl    → Aleksandra Sobczak")
        print("  jan.nowak@ans-elblag.pl        → dr Jan Nowak (opiekun uczelniany)")
        print("  anna.kowalczyk@ans-elblag.pl   → dr inż. Anna Kowalczyk")
        print("  p.zielinski@gevernova.com      → mgr inż. Piotr Zieliński (GE Vernova)")
        print("  t.wojcik@opegieka.pl           → mgr Tomasz Wójcik (OPEGIEKA)")
        print("  m.kowalski@tbmeca.pl           → inż. Marek Kowalski (TBmeca)")
        print("  dziekanat@ans-elblag.pl        → Maria Wiśniewska (administrator)")
        print("\n💡 Zaloguj się jako dziekanat, a potem kliknij „Zaloguj jako…”")
        print("   przy dowolnym koncie — zobaczysz system z perspektywy tej osoby.")


if __name__ == "__main__":
    main()
