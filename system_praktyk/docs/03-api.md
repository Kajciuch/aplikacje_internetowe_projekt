# REST API — dokumentacja

> Etap 9 wymagań projektu: endpointy, metody, walidacja, statusy HTTP,
> filtrowanie, paginacja, przykłady curl.

## Uwierzytelnianie

API używa sesji Flaska (ciasteczka). Zaloguj się przez `/login` w przeglądarce
i przekaż ciasteczko sesji w żądaniach.

W przykładach z curl używamy `-b cookies.txt` (po zalogowaniu zapisać sesję
przez `-c cookies.txt`).

## Format odpowiedzi

Wszystkie odpowiedzi w **JSON**, kodowane UTF-8.

```json
{
  "page": 1,
  "per_page": 20,
  "count": 5,
  "data": [ ... ]
}
```

W przypadku błędów:

```json
{ "error": "Opis błędu po polsku." }
```

## Statusy HTTP

| Kod | Znaczenie |
|---|---|
| 200 | OK — odczyt zakończony sukcesem |
| 201 | Created — zasób utworzony |
| 204 | No Content — zasób usunięty |
| 400 | Bad Request — nieprawidłowe dane wejściowe |
| 401 | Unauthorized — wymagane uwierzytelnienie |
| 403 | Forbidden — brak uprawnień |
| 404 | Not Found — zasób nie istnieje |
| 500 | Internal Server Error — błąd serwera |

## Endpointy

### Studenci

#### `GET /api/students`
Lista wszystkich studentów.

```bash
curl -b cookies.txt http://localhost:5000/api/students
```

Odpowiedź:
```json
{
  "count": 2,
  "data": [
    {"id": 1, "email": "anna.kowalska@ans.edu.pl", "imie": "Anna",
     "nazwisko": "Kowalska", "nr_albumu": "120345"}
  ]
}
```

#### `GET /api/students/<id>`
Szczegóły jednego studenta wraz z jego praktykami.

```bash
curl -b cookies.txt http://localhost:5000/api/students/1
```

### Praktyki

#### `GET /api/internships`
Lista praktyk z paginacją i filtrowaniem.

**Parametry zapytania:**
- `student_id` — pokaż tylko praktyki danego studenta
- `page` — numer strony (domyślnie 1)
- `per_page` — wielkość strony (domyślnie 20, max 100)

```bash
curl -b cookies.txt "http://localhost:5000/api/internships?student_id=1"
curl -b cookies.txt "http://localhost:5000/api/internships?page=1&per_page=10"
```

#### `GET /api/internships/<id>`
Szczegóły praktyki z listą jej dokumentów.

#### `POST /api/internships`
Tworzy nową praktykę (tylko dziekanat).

```bash
curl -b cookies.txt -X POST http://localhost:5000/api/internships \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1, "rok_akademicki": "2024/2025",
       "data_od": "2025-07-01", "data_do": "2025-12-15"}'
```

Zwraca `201 Created` + obiekt utworzonej praktyki.

### Dokumenty

#### `GET /api/documents`
Lista dokumentów z filtrowaniem i paginacją.

**Parametry zapytania:**
- `praktyka_id` — dokumenty danej praktyki
- `student_id` — dokumenty danego studenta (przez join na praktyce)
- `status` — `Draft` / `Submitted` / `Under Review` / `Approved` / `Rejected`
- `typ` — `karta` / `program` / `dziennik` / `efekty` / `sprawozdanie` / `ankieta`
- `page`, `per_page`

```bash
curl -b cookies.txt "http://localhost:5000/api/documents?status=Submitted"
curl -b cookies.txt "http://localhost:5000/api/documents?student_id=1&typ=dziennik"
```

#### `GET /api/documents/<id>`
Szczegóły dokumentu (z polem `dane` rozpakowanym z JSON).

#### `POST /api/documents`
Tworzy lub pobiera dokument danego typu dla praktyki.

```bash
curl -b cookies.txt -X POST http://localhost:5000/api/documents \
  -H "Content-Type: application/json" \
  -d '{"praktyka_id": 1, "typ": "dziennik",
       "dane": {"wpisy": [{"dzien": "1", "data": "2025-07-01",
                            "opis": "BHP", "efekty": "03, 04"}]}}'
```

#### `PUT /api/documents/<id>` lub `PATCH /api/documents/<id>`
Aktualizuje pole `dane` (zawartość formularza).

```bash
curl -b cookies.txt -X PUT http://localhost:5000/api/documents/1 \
  -H "Content-Type: application/json" \
  -d '{"dane": {"wpisy": [...]}}'
```

#### `DELETE /api/documents/<id>`
Usuwa dokument (tylko dziekanat lub student-autor). Zwraca `204 No Content`.

```bash
curl -b cookies.txt -X DELETE http://localhost:5000/api/documents/1
```

## Walidacja danych wejściowych

- `Content-Type` musi być `application/json` dla POST/PUT/PATCH
- Pola wymagane:
  - `POST /api/internships`: `student_id` (i student musi istnieć w bazie)
  - `POST /api/documents`: `praktyka_id`, `typ` (musi być jednym z 6 typów)
  - `PUT /api/documents/<id>`: `dane` (musi być obiektem)

## Przykład pełnego scenariusza

```bash
# 1. Logowanie (zapisanie ciasteczka sesji)
curl -c cookies.txt -X POST http://localhost:5000/login \
  -d "email=dziekanat@ans.edu.pl&haslo=praktyki123&_csrf_token=..." \
  -L  # follow redirect

# 2. Lista studentów
curl -b cookies.txt http://localhost:5000/api/students | jq

# 3. Utworzenie praktyki
curl -b cookies.txt -X POST http://localhost:5000/api/internships \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1, "rok_akademicki": "2024/2025"}' | jq

# 4. Pobranie dokumentów w stanie "Submitted"
curl -b cookies.txt "http://localhost:5000/api/documents?status=Submitted" | jq
```
