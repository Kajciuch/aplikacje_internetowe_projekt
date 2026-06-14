"""
Metadane domenowe systemu praktyk — w jednym miejscu, żeby formularze,
PDF i walidacja korzystały z tych samych danych źródłowych.

Treści efektów uczenia się i pytań ankiety pochodzą wprost z oryginalnych
załączników Instytutu Informatyki Stosowanej ANS w Elblągu.
"""

# --- 13 efektów uczenia się (Załącznik nr 4) --------------------------------
EFEKTY = [
    ("01", "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących "
           "informatyki z zachowaniem standardów i norm technicznych"),
    ("02", "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce"),
    ("03", "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki "
           "oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy"),
    ("04", "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka"),
    ("05", "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego "
           "do realizacji powierzonego zadania, posługując się rozmaitymi źródłami "
           "literaturowymi i zasobami publikowanymi w języku polskim jak i angielskim"),
    ("06", "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść "
           "swoje kompetencje, wiedzę i umiejętności co najmniej z dwóch zakresów: zadania "
           "dotyczące sprzętu i oprogramowania (np. programowanie, administrowanie siecią, "
           "konserwacja sprzętu i oprogramowania, usuwanie usterek, administrowanie zasobami "
           "informatycznymi zakładu, (e)usługami)"),
    ("07", "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach "
           "praktyki, a także referuje ustnie prezentowane w niej zagadnienia"),
    ("08", "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy / "
           "instytucji, opisać go, przedstawić koncepcję rozwiązania i ją zrealizować"),
    ("09", "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności "
           "informatycznej zakładu pracy / instytucji stosując normy i standardy stosowane "
           "w informatyce oraz biorąc pod uwagę aspekty środowiskowe i etyczne"),
    ("10", "Pracuje w zespole zajmującym się zawodowo branżą IT"),
    ("11", "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy "
           "i pomocy doświadczonych kolegów"),
    ("12", "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne "
           "informacje do realizacji planowanego zadania, jak i przekazać im w sposób "
           "zrozumiały informacje i opinie z zakresu informatyki"),
    ("13", "Dostrzega w praktyce tempo dezaktualizacji wiedzy informatycznej oraz skutki "
           "działalności informatyków, w szczególności ekonomiczne i społeczne"),
]

# --- 14 pytań ankiety oceniającej praktykę (Załącznik nr 5) ------------------
ANKIETA_PYTANIA = [
    "Poznałam/poznałem zasady funkcjonowania instytucji, w której odbywałam/odbywałem praktyki.",
    "Poznałam/poznałem strukturę oraz regulamin organizacyjny instytucji.",
    "Praktyki umożliwiły mi pełną realizację ramowego programu praktyk dla mojego kierunku.",
    "Podczas praktyk zwracano uwagę na przestrzeganie zasad etyki i tajemnicy zawodowej.",
    "Podczas praktyk miałam/miałem możliwość praktycznego zastosowania wiedzy teoretycznej.",
    "Praktyki przyczyniły się do pogłębienia mojej wiedzy i umiejętności.",
    "Mogłem liczyć na wsparcie merytoryczne Opiekuna zakładowego praktyk.",
    "Mogłem liczyć na wsparcie merytoryczne Opiekuna uczelnianego praktyk.",
    "Opiekun zakładowy potrafił prawidłowo zorganizować przebieg praktyk.",
    "Miałam/miałem możliwość pozyskiwania materiałów do pracy dyplomowej.",
    "Praktyki rozwinęły moje umiejętności komunikacji i pracy w zespole.",
    "Praktyki nauczyły mnie samodzielności i odpowiedzialności w pracy.",
    "Liczba godzin realizowana w ramach praktyk jest wystarczająca.",
    "Czy po zakończeniu praktyki chciałaby/chciałby Pani/Pan współpracować z tą instytucją?",
]

ANKIETA_SKALA = [
    "zdecydowanie tak",
    "raczej tak",
    "trudno powiedzieć",
    "raczej nie",
    "zdecydowanie nie",
]

# --- Definicje typów dokumentów ---------------------------------------------
# Każdy dokument ma: ładną nazwę, numer załącznika, ikonę (emoji), szablon
# formularza oraz kto jest jego autorem.
DOKUMENTY = {
    "karta":        {"nazwa": "Karta praktyki zawodowej",        "zalacznik": "3",  "ikona": "🪪", "autor": "student"},
    "program":      {"nazwa": "Program i harmonogram praktyki",  "zalacznik": "2a", "ikona": "🗓️", "autor": "student"},
    "dziennik":     {"nazwa": "Dziennik praktyki zawodowej",     "zalacznik": "6",  "ikona": "📔", "autor": "student"},
    "efekty":       {"nazwa": "Potwierdzenie efektów uczenia się","zalacznik": "4", "ikona": "✅", "autor": "opiekun_zakladowy"},
    "sprawozdanie": {"nazwa": "Sprawozdanie z praktyki",         "zalacznik": "7",  "ikona": "📝", "autor": "student"},
    "ankieta":      {"nazwa": "Kwestionariusz ankiety",          "zalacznik": "5",  "ikona": "📊", "autor": "student"},
}

# Kolejność wyświetlania dokumentów.
DOKUMENTY_KOLEJNOSC = ["karta", "program", "dziennik", "efekty", "sprawozdanie", "ankieta"]

# --- Dane uczelni -----------------------------------------------------------
UCZELNIA = "Akademia Nauk Stosowanych w Elblągu"
INSTYTUT = "Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego"
KIERUNEK = "Informatyka"

# --- Specjalizacje na 3. roku informatyki -----------------------------------
SPECJALIZACJE = [
    "Projektowanie baz danych i oprogramowanie użytkowe",
    "Modelowanie 3D w zastosowaniach medycznych, prototypowaniu i mediach interaktywnych",
    "Administracja systemów i sieci komputerowych",
]

# --- Role -------------------------------------------------------------------
ROLE_NAZWY = {
    "student":            "Student",
    "opiekun_uczelniany": "Opiekun uczelniany",
    "opiekun_zakladowy":  "Opiekun zakładowy",
    "dziekanat":          "Dziekanat (administrator)",
}

# --- Workflow dokumentu (etap 5: Draft → Submitted → Under Review → ...) -----
STATUSY = ["Draft", "Submitted", "Under Review", "Approved", "Rejected"]

STATUS_PL = {
    "Draft":        "Szkic",
    "Submitted":    "Złożony",
    "Under Review": "W recenzji",
    "Approved":     "Zatwierdzony",
    "Rejected":     "Odrzucony",
}

# Dozwolone przejścia statusów (z czego → na co).
PRZEJSCIA = {
    "Draft":        ["Submitted"],
    "Submitted":    ["Under Review", "Rejected"],
    "Under Review": ["Approved", "Rejected"],
    "Rejected":     ["Draft"],          # odrzucony wraca do poprawy
    "Approved":     [],                  # stan końcowy
}

# Role, które mogą recenzować (zmieniać status poza wysłaniem przez studenta).
ROLE_RECENZUJACE = {"opiekun_uczelniany", "opiekun_zakladowy", "dziekanat"}
