# Analiza systemu — System Obsługi Praktyk

> Etap 4 wymagań projektu: aktorzy, wymagania funkcjonalne, user stories,
> wymagania niefunkcjonalne, opis workflow.

## 1. Aktorzy systemu

| Aktor | Opis | Główne czynności |
|---|---|---|
| **Student** | Osoba odbywająca praktykę | Wypełnianie formularzy (karta, program, dziennik, sprawozdanie, ankieta), pobieranie PDF |
| **Opiekun uczelniany** | Pracownik ANS nadzorujący praktykę ze strony uczelni | Recenzja dokumentów, ocena sprawozdania |
| **Opiekun zakładowy** | Pracownik firmy, w której odbywa się praktyka | Potwierdzanie efektów uczenia się, ocena karty praktyki |
| **Dziekanat (administrator)** | Pracownik dziekanatu | Zarządzanie użytkownikami, tworzenie praktyk, nadzór nad całością |

## 2. Wymagania funkcjonalne (≥8)

| # | Wymaganie | Etap |
|---|---|---|
| F-01 | System umożliwia logowanie e-mailem i hasłem oraz przez konto Microsoft (OAuth2) | 8 |
| F-02 | Każdy użytkownik widzi tylko praktyki i dokumenty, do których ma uprawnienia | 8, 12 |
| F-03 | Student może wypełnić 6 formularzy: kartę praktyki, program i harmonogram, dziennik, potwierdzenie efektów, sprawozdanie, ankietę | 2, 3 |
| F-04 | Dziennik praktyki umożliwia dodawanie do 120 wpisów dziennych z opisem prac i numerami efektów (01–13) | 3, 7 |
| F-05 | Harmonogram praktyki sumuje się do 120 dni roboczych (walidacja po stronie klienta i serwera) | 3, 7 |
| F-06 | Dokumenty przechodzą workflow: `Draft → Submitted → Under Review → Approved/Rejected` (z możliwością cofnięcia z Rejected do Draft) | 5 |
| F-07 | Opiekunowie mogą recenzować dokumenty, wystawiać ocenę 2–5 i komentarz | 5 |
| F-08 | Każdy dokument można wyeksportować do PDF zgodnego z oryginalnymi załącznikami uczelni (1–6, 7, 4, 5) | 11 |
| F-09 | REST API udostępnia zasoby `/api/students`, `/api/internships`, `/api/documents` (GET/POST/PUT/DELETE) | 9 |
| F-10 | API obsługuje filtrowanie (np. po studencie, statusie) i paginację | 9 |
| F-11 | Historia zmian statusu dokumentu jest zapisywana i widoczna jako timeline | 5, 7 |
| F-12 | Dziekanat zarządza użytkownikami i może utworzyć nową praktykę | 4 |

## 3. User stories (≥3)

### US-1 — Student wypełnia dziennik
> **Jako** student kierunku informatyka  
> **chcę** móc wypełniać dziennik praktyki w przeglądarce, dodając kolejne dni jeden po drugim,  
> **żeby** nie musieć trzymać go w Wordzie i pamiętać o formatowaniu.

**Kryteria akceptacji:**
- mogę dodać nowy wiersz dziennika jednym kliknięciem
- numer dnia podpowiada się automatycznie
- przy próbie złożenia dziennika z błędnym kodem efektu dostaję komunikat
- po wypełnieniu mogę pobrać dziennik jako PDF zgodny z załącznikiem nr 6

### US-2 — Opiekun zakładowy potwierdza efekty
> **Jako** opiekun zakładowy w firmie ACME  
> **chcę** potwierdzać efekty uczenia się studenta na jednej stronie z 13 efektami,  
> **żeby** szybko uzupełnić załącznik nr 4 i odesłać go zatwierdzony.

**Kryteria akceptacji:**
- widzę listę 13 efektów z pełnymi opisami
- przy każdym efekcie zaznaczam „uzyskał" lub „nie uzyskał"
- mogę zapisać szkic, wrócić później i dokończyć
- przed złożeniem system sprawdza, czy wszystkie 13 efektów ma rozstrzygnięcie

### US-3 — Dziekanat ma przegląd wszystkich praktyk
> **Jako** pracownik dziekanatu  
> **chcę** zobaczyć w jednym miejscu wszystkie praktyki, ich statusy i braki dokumentów,  
> **żeby** szybko zidentyfikować studentów, którzy się spóźniają z dokumentami.

**Kryteria akceptacji:**
- na pulpicie widzę statystyki (liczba praktyk, studentów, opiekunów)
- mogę otworzyć dowolną praktykę i jej dokumenty
- widzę pełną listę użytkowników i ich role

## 4. Wymagania niefunkcjonalne

### Bezpieczeństwo
- Hasła przechowywane jako hash (Werkzeug `pbkdf2:sha256`)
- Zapytania SQL z parametrami → odporność na **SQL Injection**
- Jinja2 z auto-escapingiem → odporność na **XSS**
- Token CSRF w każdym formularzu POST → ochrona przed **CSRF**
- Sesje podpisywane sekretem (`SECRET_KEY` z `.env`)
- W produkcji: `SESSION_COOKIE_SECURE`, `HTTPONLY`, `SAMESITE=Lax`
- OAuth2 z weryfikacją tokenu `state` (anti-replay)

### Wydajność
- Indeksy na często odpytywanych kolumnach (`praktyki.student_id`, `dokumenty.praktyka_id`, `dokumenty.status`)
- Paginacja API (domyślnie 20 rekordów, max 100)
- Połączenie z bazą per żądanie (zamykane w `teardown`)

### Użyteczność
- Responsywny układ (działa na komórce)
- Wyraźne stany dokumentów (kolorowe plakietki statusu)
- Walidacja po stronie klienta + serwera (komunikaty błędów na żywo)
- Polskie etykiety i komunikaty
- Klawiatura + screen reader (semantyczny HTML, `aria-label`, focus states)
- `prefers-reduced-motion` respektowane

### Archiwizacja
- Tabela `workflow_log` przechowuje pełną historię zmian statusu każdego dokumentu
- Pliki PDF generowane na żądanie z aktualnych danych (jedyne źródło prawdy: baza)
- Możliwość rozszerzenia o eksport całej praktyki do ZIP

## 5. Workflow dokumentów

Każdy dokument przechodzi przez następujące stany:

```
Draft → Submitted → Under Review → Approved
                                 ↘
                                  Rejected → (powrót do) Draft
```

- **Draft (Szkic)** — dokument tworzony przez autora, edytowalny
- **Submitted (Złożony)** — student/autor uznał, że dokument jest gotowy
- **Under Review (W recenzji)** — opiekun zaczął recenzję
- **Approved (Zatwierdzony)** — recenzent zatwierdził, stan końcowy
- **Rejected (Odrzucony)** — recenzent odesłał z uwagami, autor wraca do edycji

Mapowanie autor → typ dokumentu:

| Typ dokumentu | Autor (kto wypełnia) | Kto recenzuje |
|---|---|---|
| Karta praktyki | student | opiekun zakładowy + uczelniany |
| Program i harmonogram | student | opiekun uczelniany |
| Dziennik praktyki | student | opiekun zakładowy |
| Potwierdzenie efektów | opiekun zakładowy | opiekun uczelniany |
| Sprawozdanie | student | opiekun uczelniany |
| Ankieta (anonimowa) | student | (brak — anonimowa) |
