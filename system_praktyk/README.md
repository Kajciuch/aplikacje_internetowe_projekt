# System Obsługi Praktyk Zawodowych

> Aplikacja webowa dla studentów kierunku **Informatyka** w Akademii Nauk
> Stosowanych w Elblągu (Instytut Informatyki Stosowanej). Obsługuje całość
> dokumentacji praktyk zawodowych — od programu, przez codzienny dziennik,
> aż po końcowe sprawozdanie i anonimową ankietę. Każdy dokument można
> pobrać w formacie PDF zgodnym z oryginalnymi załącznikami uczelni.

**Projekt zaliczeniowy** dla przedmiotu *Aplikacje Internetowe*.

---

## Spis treści

1. [Funkcjonalności](#funkcjonalności)
2. [Role użytkowników](#role-użytkowników)
3. [Technologie](#technologie)
4. [Szybki start — krok po kroku](#szybki-start--krok-po-kroku)
5. [Konta demonstracyjne](#konta-demonstracyjne)
6. [Struktura katalogów](#struktura-katalogów)
7. [REST API](#rest-api)
8. [Workflow dokumentów](#workflow-dokumentów)
9. [Bezpieczeństwo](#bezpieczeństwo)
10. [Logowanie Microsoft (OAuth2)](#logowanie-microsoft-oauth2)
11. [Uruchomienie w Dockerze](#uruchomienie-w-dockerze)
12. [Mapowanie wymagań projektu](#mapowanie-wymagań-projektu)
13. [Dokumentacja](#dokumentacja)

---

## Funkcjonalności

- **6 wypełnianych na stronie formularzy** (zgodnych z załącznikami uczelni):
  - Karta praktyki zawodowej (zał. 3)
  - Program i harmonogram praktyki (zał. 2a)
  - Dziennik praktyki — do 120 wpisów dziennych z numerami efektów (zał. 6)
  - Potwierdzenie 13 efektów uczenia się (zał. 4)
  - Sprawozdanie końcowe — charakterystyka, opis prac, samoocena (zał. 7)
  - Anonimowy kwestionariusz ankiety (zał. 5)
- **Eksport każdego dokumentu do PDF** z polskimi znakami i podpisami
- **Workflow** `Draft → Submitted → Under Review → Approved/Rejected` z historią zmian
- **Cztery role użytkowników** (student, opiekun uczelniany, opiekun zakładowy, dziekanat) z osobnymi pulpitami i uprawnieniami
- **REST API** (`/api/students`, `/api/internships`, `/api/documents`) z filtrowaniem i paginacją
- **Logowanie**: e-mail + hasło oraz opcjonalnie konto Microsoft (OAuth2)
- **Dynamiczne formularze** — wiersze dziennika i harmonogramu można dodawać/usuwać po stronie klienta z natychmiastową walidacją
- **Walidacja na dwóch warstwach**: po stronie klienta (JS) i serwera (Python)
- **Responsywny układ** — działa na komputerze i komórce

## Role użytkowników

| Rola | Co widzi i co robi |
|---|---|
| **Student** | Lista swoich praktyk, wypełnianie 6 formularzy, eksport do PDF |
| **Opiekun uczelniany** | Lista przypisanych studentów, recenzja programu, sprawozdania, efektów |
| **Opiekun zakładowy** | Lista studentów, recenzja karty i dziennika, potwierdzanie efektów |
| **Dziekanat** | Wszystkie praktyki, użytkownicy, statystyki, tworzenie praktyk przez API |

## Panel administracyjny dziekanatu

Dziekanat ma w pasku bocznym sekcję **Administracja** z trzema widokami:

- **Użytkownicy** (`/admin/uzytkownicy`) — pełna lista kont z możliwością:
  - utworzenia nowego konta (student / opiekun uczelniany / opiekun zakładowy / dziekanat),
  - **„Zaloguj jako…"** — wejście na konto dowolnego użytkownika z banerem nad treścią („Wróć do swojego konta"). Wygodne do testowania widoków, do prezentacji prowadzącemu i do reagowania na zgłoszenia studentów.
- **Firmy** (`/admin/firmy`) — lista zakładów pracy + formularz dodawania nowej firmy (z adresem i NIP-em).
- **Nowa praktyka** (`/admin/praktyki/nowa`) — formularz tworzenia praktyki z dropdownami: student, firma, opiekun uczelniany, opiekun zakładowy, specjalność (3 specjalności kierunku Informatyka na 3. roku), daty, numer porozumienia.

Wszystkie trasy chronione przez `@role_required("dziekanat")` — student lub opiekun dostaje HTTP 403.

## Technologie

- **Python 3.10+** · **Flask 3** · **SQLite**
- **Jinja2** (szablony) · **Werkzeug** (hashowanie haseł, sesje)
- **ReportLab** (generowanie PDF z polskimi znakami — czcionki DejaVu)
- **HTML5 + CSS** (własny system designu) · **vanilla JavaScript** (bez frameworków)
- **Mermaid** (diagramy w `docs/`)
- **Docker** (do wdrożenia)

> **Uwaga**: zamiast biblioteki `Flask-Login` zaimplementowano własny, prostszy odpowiednik (`@login_required`, `@role_required` w `auth.py`) — ta sama semantyka, mniejsza zależność.

---

## Szybki start — krok po kroku

### Wariant A: PyCharm (zalecany dla Windows/Mac)

1. **Sklonuj repozytorium** lub pobierz ZIP i rozpakuj.
2. Otwórz folder projektu w **PyCharm** (`File → Open…`).
3. PyCharm automatycznie zaproponuje utworzenie środowiska wirtualnego — **kliknij „Create venv"**.
4. Otwórz wbudowany terminal w PyCharm (`Alt+F12` / `View → Tool Windows → Terminal`).
5. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```
6. Zainicjalizuj bazę danych i wpisz dane demo:
   ```bash
   python seed.py
   ```
7. Uruchom serwer:
   ```bash
   python app.py
   ```
8. Otwórz w przeglądarce: **<http://localhost:5000>**

### Wariant B: terminal (Linux/Mac/WSL)

```bash
# 1. Utwórz i aktywuj środowisko wirtualne
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows (PowerShell)

# 2. Zainstaluj zależności
pip install -r requirements.txt

# 3. Inicjalizacja bazy + dane demo
python seed.py

# 4. Uruchomienie
python app.py
# Aplikacja słucha na http://localhost:5000
```

## Konta demonstracyjne

Skrypt `seed.py` tworzy 9 kont — studenci, opiekunowie uczelniani, opiekunowie
zakładowi i dziekanat. **Hasło dla wszystkich:** `praktyki123`

### Studenci

| E-mail | Imię i nazwisko | Album | Specjalność |
|---|---|---|---|
| `21310@student.ans-elblag.pl` | **Kaja Thiel** | 21310 | Projektowanie baz danych i oprogramowanie użytkowe |
| `21342@student.ans-elblag.pl` | Maciej Lewandowski | 21342 | Modelowanie 3D w zastosowaniach medycznych |
| `21389@student.ans-elblag.pl` | Aleksandra Sobczak | 21389 | Administracja systemów i sieci komputerowych |

### Opiekunowie uczelniani (ANS Elbląg)

| E-mail | Imię i nazwisko |
|---|---|
| `jan.nowak@ans-elblag.pl` | dr Jan Nowak |
| `anna.kowalczyk@ans-elblag.pl` | dr inż. Anna Kowalczyk |

### Opiekunowie zakładowi

| E-mail | Imię i nazwisko | Firma |
|---|---|---|
| `p.zielinski@gevernova.com` | mgr inż. Piotr Zieliński | GE Vernova Polska |
| `t.wojcik@opegieka.pl` | mgr Tomasz Wójcik | OPEGIEKA |
| `m.kowalski@tbmeca.pl` | inż. Marek Kowalski | TBmeca |

### Dziekanat (administrator)

| E-mail | Imię i nazwisko |
|---|---|
| `dziekanat@ans-elblag.pl` | Maria Wiśniewska |

> **Tip**: zaloguj się jako dziekanat, otwórz **Użytkownicy** i kliknij
> **„Zaloguj jako…"** przy dowolnym koncie — natychmiast zobaczysz system z
> perspektywy tej osoby. Wrócisz do siebie czarnym banerem nad treścią.

### Przykładowa praktyka

W bazie znajduje się gotowa praktyka **Kaja Thiel → GE Vernova Polska**
z dokumentami w różnych stanach workflow (karta — szkic, program — złożony,
dziennik — szkic z 3 wpisami, sprawozdanie — zatwierdzone z oceną 5).

Studenci Maciej i Aleksandra nie mają jeszcze praktyk — zaloguj się jako
dziekanat i utwórz im praktykę, żeby zobaczyć panel administracyjny w akcji.

---

## Struktura katalogów

```
system_praktyk/
├── app.py                      # punkt wejścia (Flask application factory)
├── config.py                   # konfiguracja (development / production, .env)
├── database.py                 # warstwa SQLite (połączenie, schemat, CLI init-db)
├── models.py                   # klasa User + helpery: CRUD, walidacja, workflow
├── auth.py                     # logowanie, sesje, Microsoft OAuth2, dekoratory ról
├── security.py                 # tokeny CSRF
├── forms_meta.py               # metadane formularzy (13 efektów, 14 pytań ankiety, mapowania)
├── pdf_utils.py                # generowanie PDF (ReportLab, czcionki DejaVu)
├── schema.sql                  # DDL bazy danych (6 tabel + indeksy)
├── seed.py                     # inicjalizacja + dane demonstracyjne
├── requirements.txt            # zależności Pythona
├── .env.example                # szablon konfiguracji
├── Dockerfile                  # obraz produkcyjny
├── docker-compose.yml          # uruchomienie jednym poleceniem
│
├── routes/
│   ├── __init__.py
│   ├── main.py                 # /, /dashboard, /profil
│   ├── documents.py            # widoki praktyk i dokumentów (edycja, recenzja, PDF)
│   ├── api.py                  # REST API (/api/*)
│   └── admin.py                # panel dziekanatu (/admin/*) + impersonacja
│
├── templates/                  # szablony Jinja2
│   ├── base.html               # szkielet (sidebar + treść + baner impersonacji)
│   ├── login.html
│   ├── dashboard_*.html        # 3 pulpity (student / opiekun / dziekanat)
│   ├── praktyka.html           # widok praktyki z listą 6 dokumentów
│   ├── dokument_podglad.html   # podgląd dokumentu + recenzja + historia
│   ├── form_*.html             # 6 formularzy edycji
│   ├── profil.html
│   ├── admin/                  # panel dziekanatu (4 szablony)
│   │   ├── uzytkownicy.html
│   │   ├── nowy_uzytkownik.html
│   │   ├── firmy.html
│   │   ├── nowa_firma.html
│   │   └── nowa_praktyka.html
│   └── 400.html, 403.html, 404.html, 500.html
│
├── static/
│   ├── css/style.css           # własny system designu
│   └── js/app.js               # dynamiczne wiersze, walidacja klienta
│
├── fonts/                      # czcionki DejaVu (PDF z polskimi znakami)
│
├── data/                       # przykładowe pliki JSON (etap 9)
│   ├── sample_efekty.json
│   ├── sample_dziennik.json
│   ├── sample_ankieta.json
│   └── sample_praktyka.json
│
└── docs/
    ├── 01-analiza.md           # etap 4: aktorzy, wymagania, user stories
    ├── 02-diagramy.md          # etap 5: 4 diagramy Mermaid
    └── 03-api.md               # etap 9: dokumentacja API
```

---

## REST API

Pełna dokumentacja: [`docs/03-api.md`](docs/03-api.md).

### Najważniejsze endpointy

| Metoda | Endpoint | Opis |
|---|---|---|
| `GET` | `/api/students` | lista studentów |
| `GET` | `/api/students/<id>` | szczegóły + praktyki |
| `GET` | `/api/internships` | praktyki (filtr `?student_id=…`, paginacja `?page=…&per_page=…`) |
| `POST` | `/api/internships` | utworzenie praktyki (rola: dziekanat) |
| `GET` | `/api/documents` | dokumenty (filtry `?praktyka_id=…&status=…&typ=…`) |
| `GET` | `/api/documents/<id>` | szczegóły dokumentu |
| `POST` | `/api/documents` | utworzenie / aktualizacja dokumentu |
| `PUT \| PATCH` | `/api/documents/<id>` | aktualizacja pola `dane` |
| `DELETE` | `/api/documents/<id>` | usunięcie (rola: dziekanat lub autor) |

### Przykład

```bash
# Po zalogowaniu w przeglądarce (sesja w cookies)
curl -b cookies.txt "http://localhost:5000/api/documents?status=Submitted" | jq
```

---

## Workflow dokumentów

```
Draft → Submitted → Under Review → Approved
                                 ↘
                                  Rejected → (powrót do) Draft
```

Pełna historia każdej zmiany statusu zapisywana jest w tabeli `workflow_log`
i wyświetlana jako oś czasu w widoku dokumentu.

Diagramy: [`docs/02-diagramy.md`](docs/02-diagramy.md).

---

## Bezpieczeństwo

| Mechanizm | Implementacja |
|---|---|
| **Hashowanie haseł** | `werkzeug.security.generate_password_hash` (pbkdf2:sha256) |
| **SQL Injection** | wszystkie zapytania z parametrami (`?` placeholders) |
| **XSS** | autoescaping Jinja2 we wszystkich szablonach |
| **CSRF** | token w sesji, weryfikowany przed każdym POST/PUT/PATCH/DELETE |
| **Sesje** | podpisane sekretem z `.env`, w produkcji `SECURE/HTTPONLY/SAMESITE` |
| **OAuth2** | weryfikacja tokenu `state` (anti-replay) |
| **Uprawnienia** | `@login_required` + `@role_required("student", "dziekanat")` |
| **Walidacja** | dwuwarstwowa: klient (JS) + serwer (Python) |

---

## Logowanie Microsoft (OAuth2)

Logowanie e-mailem działa od razu. Logowanie Microsoft jest **opcjonalne** i wymaga rejestracji aplikacji w Azure Portal:

1. <https://portal.azure.com> → **Azure Active Directory → App registrations → New registration**
2. **Nazwa**: System Praktyk. **Konta**: *Accounts in any organizational directory*.
3. **Redirect URI** (typ: *Web*): `http://localhost:5000/auth/microsoft/callback`
4. Po zapisaniu zanotuj **Application (client) ID** oraz **Directory (tenant) ID**.
5. **Certificates & secrets → New client secret** → skopiuj wartość (widoczna tylko raz!).
6. Skopiuj `.env.example` jako `.env` i wpisz wartości:
   ```env
   MS_CLIENT_ID=...
   MS_CLIENT_SECRET=...
   MS_TENANT_ID=...
   ```
7. Zrestartuj aplikację — na stronie logowania pojawi się przycisk **Zaloguj przez Microsoft**.

---

## Uruchomienie w Dockerze

```bash
# Zbudowanie obrazu i uruchomienie
docker compose up --build

# Aplikacja dostępna pod http://localhost:5000
```

Kontener uruchamia produkcyjny serwer WSGI `waitress` i automatycznie inicjalizuje bazę przy starcie. Plik bazy trzymany jest w wolumenie `./data-prod` — przeżywa restart kontenera.

---

## Mapowanie wymagań projektu

Każdy etap z `readme.MD` prowadzącego ma odpowiednik w plikach repozytorium:

| Etap | Wymaganie | Pliki / lokalizacje |
|---:|---|---|
| **1** | Podstawy Flask: `app.py`, `render_template`, `templates/`, venv | `app.py`, `templates/*.html`, `requirements.txt` |
| **2** | Formularze (`request.form`), JSON (`jsonify`), walidacja e-maila, klasy Python | `routes/documents.py` (form handling), `routes/api.py` (jsonify), `models.py:poprawny_email` + `class User` |
| **3** | Trwałość, `request.form.getlist`, dynamiczne tabele JS, zapis dziennika | `database.py` (load/save), `routes/documents.py:_parsuj` (getlist), `static/js/app.js` (dynamic rows), `templates/form_dziennik.html` |
| **4** | Analiza: aktorzy, ≥8 wymagań F., ≥3 user stories, wymagania niefunkcjonalne, workflow | [`docs/01-analiza.md`](docs/01-analiza.md) |
| **5** | Diagramy: sekwencji, stanów, flowchart — w Mermaid + eksport | [`docs/02-diagramy.md`](docs/02-diagramy.md) (4 diagramy Mermaid) |
| **6** | ERD + plik `.sql` z `CREATE TABLE`, `PRIMARY KEY`, `FOREIGN KEY`, `NOT NULL`, `UNIQUE`, opis DBeaver | `schema.sql` (DDL), [`docs/02-diagramy.md`](docs/02-diagramy.md) (ERD). DBeaver: otwórz `praktyki.db` przez **Database → New Connection → SQLite** i wskaż plik. |
| **7** | Tabele (studenci, formularze, firmy, opiekunowie, efekty, harmonogram), walidacja kompletności/120 dni/13 efektów | `schema.sql` (6 tabel), `models.py:waliduj_dziennik` + `waliduj_efekty` |
| **8** | Logowanie Microsoft + callback + `User` + integracja Flask-Login + role + pierwszy login + `.env` | `auth.py` (OAuth2 + dekoratory zastępujące Flask-Login), `models.py:User`, `schema.sql:users` (rola, oauth, pierwszy_login), `.env.example` |
| **9** | REST API: `/api/students`, `/api/internships`, `/api/documents`, GET/POST/PUT/DELETE, JSON, statusy 200/400/404/500, filtrowanie + paginacja, dokumentacja | `routes/api.py`, [`docs/03-api.md`](docs/03-api.md), przykłady curl wewnątrz |
| **10** | Frontend: dashboardy, formularze, fetch/HTML/JS, walidacja klienta, komunikaty | `templates/dashboard_*.html`, `templates/form_*.html`, `static/js/app.js`, `static/css/style.css` |
| **11** | PDF: dziennik, efekty, raport końcowy, ReportLab, szablony, endpoint `/generate-pdf/<id>`, podpisy | `pdf_utils.py` (6 generatorów), endpoint `dok.pdf` w `routes/documents.py` (`/dokument/<id>/pdf`), czcionki w `fonts/` |
| **12** | Bezpieczeństwo (SQLi, XSS, CSRF, sesje), `.env`, development/production, Docker, logowanie błędów | `security.py` (CSRF), `auth.py` (sesje, role), `config.py` (dev/prod), `Dockerfile`, `docker-compose.yml` |

---

## Dokumentacja

- [`docs/01-analiza.md`](docs/01-analiza.md) — aktorzy, wymagania, user stories
- [`docs/02-diagramy.md`](docs/02-diagramy.md) — diagramy Mermaid (sekwencji, stanów, flowchart, ERD)
- [`docs/03-api.md`](docs/03-api.md) — dokumentacja REST API z przykładami `curl`

## Licencja

Projekt na potrzeby akademickie (przedmiot *Aplikacje Internetowe* — ANS Elbląg).
