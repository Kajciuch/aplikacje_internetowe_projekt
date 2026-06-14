# Diagramy systemu — System Obsługi Praktyk

> Etap 5 wymagań projektu: diagram sekwencji, diagram stanów, flowchart, ERD.
> Wszystkie diagramy mają trzy reprezentacje:
> 1. **Kod źródłowy w Mermaid** poniżej — GitHub renderuje automatycznie,
> 2. **Wyeksportowane obrazki PNG** w `docs/diagrams/*.png`,
> 3. **Pliki źródłowe** `.mmd` w `docs/diagrams/` (do wklejenia na <https://mermaid.live>).
>
> Skrypt `docs/diagrams/render.py` regeneruje obrazki PNG za pomocą `graphviz`
> i `matplotlib` (uruchom: `python docs/diagrams/render.py`).

## 1. Diagram sekwencji — proces weryfikacji dokumentu

![Diagram sekwencji](diagrams/01-sekwencja.png)

### Kod źródłowy (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor S as Student
    participant A as Aplikacja Flask
    participant DB as Baza danych
    actor O as Opiekun
    participant PDF as Generator PDF

    S->>A: Wypełnia dziennik praktyki (POST /dokument/.../edytuj)
    A->>A: Walidacja CSRF + walidacja danych
    A->>DB: UPDATE dokumenty SET dane_json=...
    A-->>S: Flash: "Zapisano zmiany"

    S->>A: Klika "Zapisz i złóż do recenzji"
    A->>A: Walidacja kompletności (np. 13 efektów, ≤120 dni)
    A->>DB: UPDATE dokumenty SET status='Submitted'
    A->>DB: INSERT workflow_log
    A-->>S: Flash: "Status: Złożony"

    O->>A: Loguje się, otwiera "Do recenzji"
    A->>DB: SELECT dokumenty WHERE status IN ('Submitted','Under Review')
    A-->>O: Lista dokumentów do recenzji

    O->>A: Otwiera dokument, klika "Pobierz PDF"
    A->>DB: SELECT dokument + dane praktyki
    A->>PDF: generuj_pdf(dok, prakt)
    PDF-->>A: BytesIO z PDF
    A-->>O: Pobieranie pliku PDF

    O->>A: Wystawia ocenę 5, komentarz, status='Approved'
    A->>DB: UPDATE dokumenty + INSERT workflow_log
    A-->>O: Flash: "Status zmieniony na Zatwierdzony"
    A-->>S: (przy następnym wejściu) widzi zatwierdzenie
```

## 2. Diagram stanów — workflow dokumentu

![Diagram stanów](diagrams/02-stany.png)

### Kod źródłowy (Mermaid)

```mermaid
stateDiagram-v2
    [*] --> Draft : utworzenie

    Draft --> Submitted : student klika "Złóż"
    Submitted --> UnderReview : opiekun rozpoczyna recenzję
    Submitted --> Rejected : opiekun odrzuca od razu
    UnderReview --> Approved : opiekun zatwierdza
    UnderReview --> Rejected : opiekun odrzuca
    Rejected --> Draft : autor wraca do poprawek

    Approved --> [*]

    note right of Draft
        Stan edytowalny przez autora.
        Walidacja przy próbie złożenia.
    end note

    note right of Approved
        Stan końcowy.
        Pełna historia w workflow_log.
    end note
```

## 3. Flowchart — logika uprawnień

![Flowchart](diagrams/03-flowchart.png)

### Kod źródłowy (Mermaid)

```mermaid
flowchart TD
    Start([Żądanie HTTP]) --> Login{Zalogowany?}
    Login -- nie --> Logowanie[/Przekieruj na /login/]
    Login -- tak --> Trasa{Trasa?}

    Trasa -- /dashboard --> Dash[Pulpit zależny od roli]
    Dash --> Rola{Jaka rola?}
    Rola -- student --> DStud[dashboard_student.html]
    Rola -- opiekun --> DOp[dashboard_opiekun.html]
    Rola -- dziekanat --> DDziek[dashboard_dziekanat.html]

    Trasa -- /dokument/:id --> Dok{Ma dostęp?}
    Dok -- nie --> E403[/HTTP 403/]
    Dok -- tak --> Akcja{Akcja?}

    Akcja -- podgląd --> Widok[Renderuj dokument]
    Akcja -- edycja --> Edyt{moze_edytowac?}
    Edyt -- nie --> E403
    Edyt -- tak --> Form[Formularz edycji]

    Akcja -- recenzja --> Rec{moze_recenzowac?}
    Rec -- nie --> E403
    Rec -- tak --> RecForm[Formularz recenzji]

    Trasa -- /api/* --> API{Token sesji?}
    API -- nie --> E401[/HTTP 401/]
    API -- tak --> APIRola{Wymaga roli?}
    APIRola -- tak/nie --> APIOdp[JSON]
```

## 4. Diagram ERD — model danych

![ERD](diagrams/04-erd.png)

### Kod źródłowy (Mermaid)

```mermaid
erDiagram
    USERS ||--o{ PRAKTYKI : "student_id"
    USERS ||--o{ PRAKTYKI : "opiekun_uczelniany_id"
    USERS ||--o{ PRAKTYKI : "opiekun_zakladowy_id"
    FIRMY ||--o{ PRAKTYKI : "firma_id"
    PRAKTYKI ||--o{ DOKUMENTY : "praktyka_id"
    DOKUMENTY ||--o{ WORKFLOW_LOG : "dokument_id"
    USERS ||--o{ DOKUMENTY : "autor_id"
    USERS ||--o{ WORKFLOW_LOG : "uzytkownik_id"

    USERS {
        int id PK
        text email UK
        text haslo_hash
        text imie
        text nazwisko
        text rola "CHECK 4 wartości"
        text nr_albumu
        text oauth_provider
        text oauth_sub
        int pierwszy_login
        text utworzono
    }

    FIRMY {
        int id PK
        text nazwa
        text adres
        text nip
    }

    EFEKTY {
        int id PK
        text kod UK "01..13"
        text opis
    }

    PRAKTYKI {
        int id PK
        int student_id FK
        int opiekun_uczelniany_id FK
        int opiekun_zakladowy_id FK
        int firma_id FK
        text specjalnosc
        text rok_akademicki
        text data_od
        text data_do
        int liczba_dni "default 120"
        text porozumienie_nr
        text status
    }

    DOKUMENTY {
        int id PK
        int praktyka_id FK
        text typ "6 wartości"
        text status "5 wartości"
        text dane_json "JSON"
        int autor_id FK
        int recenzent_id FK
        text ocena
        text komentarz_recenzenta
        text utworzono
        text zaktualizowano
    }

    WORKFLOW_LOG {
        int id PK
        int dokument_id FK
        text status_z
        text status_na
        int uzytkownik_id FK
        text komentarz
        text kiedy
    }
```

## Eksport diagramów

Diagramy zostały już wyrenderowane do plików PNG w folderze `docs/diagrams/`.
Aby je zregenerować po edycji:

```bash
cd docs/diagrams
python render.py
```

Skrypt używa bibliotek `graphviz` (już zainstalowanej z `requirements.txt`
przez zależność reportlab — `pip install graphviz` jeśli trzeba osobno)
i `matplotlib`.

Diagramy można też wyeksportować z kodu Mermaid za pomocą:
- **Mermaid Live Editor** — https://mermaid.live (wklej zawartość pliku `.mmd` → Export PNG/SVG),
- **VS Code** — rozszerzenie *Markdown Preview Mermaid Support*,
- **CLI** — `mmdc -i diagram.mmd -o diagram.png` (wymaga Chromium).
