-- ============================================================================
--  System Obsługi Praktyk — schemat bazy danych (SQLite)
--  Etap 6 i 7 z wymagań projektu.
--  Prototyp: SQLite. Docelowo można przenieść na MariaDB/PostgreSQL.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
--  UŻYTKOWNICY (4 role + logowanie lokalne lub OAuth)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT    NOT NULL UNIQUE,
    haslo_hash      TEXT,                 -- NULL gdy konto tylko-OAuth
    imie            TEXT    NOT NULL,
    nazwisko        TEXT    NOT NULL,
    rola            TEXT    NOT NULL
                            CHECK (rola IN ('student',
                                            'opiekun_uczelniany',
                                            'opiekun_zakladowy',
                                            'dziekanat')),
    nr_albumu       TEXT,                 -- tylko dla studenta
    oauth_provider  TEXT,                 -- np. 'microsoft'
    oauth_sub       TEXT,                 -- identyfikator użytkownika u dostawcy
    pierwszy_login  INTEGER NOT NULL DEFAULT 1,
    utworzono       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------------------
--  FIRMY / ZAKŁADY PRACY
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS firmy (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nazwa   TEXT    NOT NULL,
    adres   TEXT,
    nip     TEXT
);

-- ----------------------------------------------------------------------------
--  EFEKTY UCZENIA SIĘ (13 sztuk — wypełniane przez seed.py)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS efekty (
    id      INTEGER PRIMARY KEY,          -- 1..13
    kod     TEXT    NOT NULL UNIQUE,      -- '01'..'13'
    opis    TEXT    NOT NULL
);

-- ----------------------------------------------------------------------------
--  PRAKTYKI — pojedyncza praktyka studenta (spina studenta, opiekunów, firmę)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS praktyki (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id               INTEGER NOT NULL REFERENCES users(id),
    opiekun_uczelniany_id    INTEGER REFERENCES users(id),
    opiekun_zakladowy_id     INTEGER REFERENCES users(id),
    firma_id                 INTEGER REFERENCES firmy(id),
    specjalnosc              TEXT,
    rok_akademicki           TEXT,
    data_od                  TEXT,
    data_do                  TEXT,
    liczba_dni               INTEGER NOT NULL DEFAULT 120,
    porozumienie_nr          TEXT,
    status                   TEXT    NOT NULL DEFAULT 'aktywna',
    utworzono                TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------------------
--  DOKUMENTY — każdy formularz (karta/program/dziennik/efekty/sprawozdanie/
--  ankieta) jako jeden rekord. Pola specyficzne dla formularza trzymamy w
--  kolumnie dane_json (elastyczność + spełnia wymóg "zapis danych w JSON").
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dokumenty (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    praktyka_id          INTEGER NOT NULL REFERENCES praktyki(id) ON DELETE CASCADE,
    typ                  TEXT    NOT NULL
                                 CHECK (typ IN ('karta','program','dziennik',
                                                'efekty','sprawozdanie','ankieta')),
    status               TEXT    NOT NULL DEFAULT 'Draft'
                                 CHECK (status IN ('Draft','Submitted',
                                                   'Under Review','Approved','Rejected')),
    dane_json            TEXT    NOT NULL DEFAULT '{}',
    autor_id             INTEGER REFERENCES users(id),
    recenzent_id         INTEGER REFERENCES users(id),
    ocena                TEXT,            -- ocena parametryczna 2-5 (karta/sprawozdanie)
    komentarz_recenzenta TEXT,
    utworzono            TEXT    NOT NULL DEFAULT (datetime('now')),
    zaktualizowano       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------------------
--  LOG WORKFLOW — historia zmian statusu dokumentu (audyt / archiwizacja)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workflow_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    dokument_id   INTEGER NOT NULL REFERENCES dokumenty(id) ON DELETE CASCADE,
    status_z      TEXT,
    status_na     TEXT    NOT NULL,
    uzytkownik_id INTEGER REFERENCES users(id),
    komentarz     TEXT,
    kiedy         TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Indeksy pod najczęstsze zapytania
CREATE INDEX IF NOT EXISTS idx_praktyki_student   ON praktyki(student_id);
CREATE INDEX IF NOT EXISTS idx_dokumenty_praktyka ON dokumenty(praktyka_id);
CREATE INDEX IF NOT EXISTS idx_dokumenty_status   ON dokumenty(status);
