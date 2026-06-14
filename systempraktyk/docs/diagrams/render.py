"""Renderowanie 4 diagramów projektu jako wysokiej jakości PNG.

Diagramy odpowiadają tym z docs/02-diagramy.md (które są w formacie Mermaid
dla GitHuba). Tutaj produkujemy stałe obrazki PNG do osadzenia w README,
w prezentacjach, w wydruku.

Paleta zgodna z designem aplikacji:
  papier:  #fffdf8     ink:    #1a1f2b
  akcent:  #e8552d     muted:  #8b8275
"""

from pathlib import Path
import graphviz

OUT = Path(__file__).parent
PAPER = "#fffdf8"
INK = "#1a1f2b"
ACCENT = "#e8552d"
ACCENT_DEEP = "#c2410c"
MUTED = "#8b8275"
LINE = "#ddd6c8"
BG_BOX = "#f4f1ea"


def base_graph(name, **kwargs):
    """Wspólne ustawienia stylu dla wszystkich grafów."""
    g = graphviz.Digraph(name, format="png")
    g.attr(bgcolor=PAPER, rankdir="TB",
           fontname="DejaVu Sans", fontsize="11",
           pad="0.6", nodesep="0.4", ranksep="0.6")
    g.attr("node", shape="box", style="rounded,filled",
           fillcolor=PAPER, color=INK, fontcolor=INK,
           fontname="DejaVu Sans", fontsize="11", penwidth="1.2")
    g.attr("edge", color=INK, fontname="DejaVu Sans", fontsize="9",
           fontcolor=MUTED, arrowsize="0.7", penwidth="1.0")
    for k, v in kwargs.items():
        g.attr(**{k: v})
    return g


# ---------------------------------------------------------------------------
# 1) Diagram stanów — workflow dokumentu
# ---------------------------------------------------------------------------
def stany():
    g = base_graph("stany", rankdir="LR")
    g.attr("node", shape="box", style="rounded,filled")

    # Stan początkowy (czarna kropka)
    g.node("start", label="", shape="circle", style="filled",
           fillcolor=INK, width="0.25", height="0.25")
    # Stan końcowy (podwójna obwódka)
    g.node("end", label="", shape="doublecircle", style="filled",
           fillcolor=INK, width="0.25", height="0.25")

    # Stany główne
    g.node("Draft",     "Draft\n(Szkic)",        fillcolor="#f4f1ea")
    g.node("Submitted", "Submitted\n(Złożony)",  fillcolor="#f0f9ff", color="#0369a1", fontcolor="#0369a1")
    g.node("Review",    "Under Review\n(W recenzji)", fillcolor="#fffbeb", color="#b45309", fontcolor="#b45309")
    g.node("Approved",  "Approved\n(Zatwierdzony)",   fillcolor="#f0fdf4", color="#15803d", fontcolor="#15803d")
    g.node("Rejected",  "Rejected\n(Odrzucony)",      fillcolor="#fef2f2", color="#b91c1c", fontcolor="#b91c1c")

    # Przejścia
    g.edge("start", "Draft", label="utworzenie")
    g.edge("Draft", "Submitted", label="student\n„Złóż”", color=ACCENT, fontcolor=ACCENT_DEEP)
    g.edge("Submitted", "Review", label="opiekun\nrozpoczyna")
    g.edge("Submitted", "Rejected", label="odrzuca", color="#b91c1c", fontcolor="#b91c1c")
    g.edge("Review", "Approved", label="zatwierdza", color="#15803d", fontcolor="#15803d")
    g.edge("Review", "Rejected", label="odrzuca", color="#b91c1c", fontcolor="#b91c1c")
    g.edge("Rejected", "Draft", label="poprawki", style="dashed")
    g.edge("Approved", "end")

    g.render(filename=str(OUT / "02-stany"), cleanup=True)
    print("  ✓ 02-stany.png")


# ---------------------------------------------------------------------------
# 2) Flowchart — logika uprawnień
# ---------------------------------------------------------------------------
def flowchart():
    g = base_graph("flow", rankdir="TB")

    # Decyzje (diamond) i akcje (box)
    g.node("start",   "Żądanie HTTP",     shape="oval", fillcolor=INK, fontcolor=PAPER)
    g.node("login",   "Zalogowany?",      shape="diamond", fillcolor="#f4f1ea")
    g.node("redirect","Przekierowanie\n/login")
    g.node("route",   "Trasa?",           shape="diamond", fillcolor="#f4f1ea")

    g.node("dash",    "/dashboard")
    g.node("role",    "Rola?",            shape="diamond", fillcolor="#f4f1ea")
    g.node("dstud",   "dashboard_student",   fillcolor="#fef9c3")
    g.node("dop",     "dashboard_opiekun",   fillcolor="#fef9c3")
    g.node("ddziek",  "dashboard_dziekanat", fillcolor="#fef9c3")

    g.node("dok",     "/dokument/:id")
    g.node("acc",     "Ma dostęp?",       shape="diamond", fillcolor="#f4f1ea")
    g.node("e403",    "HTTP 403",         fillcolor="#fef2f2", color="#b91c1c", fontcolor="#b91c1c")
    g.node("akcja",   "Akcja?",           shape="diamond", fillcolor="#f4f1ea")
    g.node("view",    "Podgląd",          fillcolor="#fef9c3")
    g.node("edit",    "Edycja",           fillcolor="#fef9c3")
    g.node("rec",     "Recenzja",         fillcolor="#fef9c3")

    g.node("api",     "/api/*")
    g.node("sesja",   "Sesja OK?",        shape="diamond", fillcolor="#f4f1ea")
    g.node("e401",    "HTTP 401",         fillcolor="#fef2f2", color="#b91c1c", fontcolor="#b91c1c")
    g.node("json",    "JSON",             fillcolor="#fef9c3")

    g.edge("start", "login")
    g.edge("login", "redirect", label="nie")
    g.edge("login", "route",    label="tak", color=ACCENT, fontcolor=ACCENT_DEEP)

    g.edge("route", "dash", label="/dashboard")
    g.edge("dash", "role")
    g.edge("role", "dstud",  label="student")
    g.edge("role", "dop",    label="opiekun")
    g.edge("role", "ddziek", label="dziekanat")

    g.edge("route", "dok", label="/dokument/:id")
    g.edge("dok", "acc")
    g.edge("acc", "e403",  label="nie", color="#b91c1c", fontcolor="#b91c1c")
    g.edge("acc", "akcja", label="tak", color=ACCENT, fontcolor=ACCENT_DEEP)
    g.edge("akcja", "view", label="GET")
    g.edge("akcja", "edit", label="POST edit")
    g.edge("akcja", "rec",  label="POST recenzja")

    g.edge("route", "api", label="/api/*")
    g.edge("api", "sesja")
    g.edge("sesja", "e401", label="nie", color="#b91c1c", fontcolor="#b91c1c")
    g.edge("sesja", "json", label="tak", color=ACCENT, fontcolor=ACCENT_DEEP)

    g.render(filename=str(OUT / "03-flowchart"), cleanup=True)
    print("  ✓ 03-flowchart.png")


# ---------------------------------------------------------------------------
# 3) ERD — model danych
# ---------------------------------------------------------------------------
def erd():
    g = base_graph("erd", rankdir="LR")
    g.attr(nodesep="0.5", ranksep="0.8")
    g.attr("node", shape="plaintext")
    g.attr("edge", arrowhead="crow", arrowtail="none", dir="both", penwidth="1.1")

    def tabela(name, tytul, kolumny):
        rows = [
            f'<TR><TD BGCOLOR="{INK}" PORT="hdr">'
            f'<FONT COLOR="{PAPER}"><B>{tytul}</B></FONT></TD></TR>'
        ]
        for kol, typ, klucz in kolumny:
            klucz_html = ""
            if klucz == "PK":
                klucz_html = f' <FONT COLOR="{ACCENT_DEEP}"><B>PK</B></FONT>'
            elif klucz == "FK":
                klucz_html = f' <FONT COLOR="{MUTED}">FK</FONT>'
            elif klucz == "UK":
                klucz_html = f' <FONT COLOR="{ACCENT_DEEP}">UK</FONT>'
            rows.append(
                f'<TR><TD ALIGN="LEFT" PORT="{kol}" BGCOLOR="{PAPER}">'
                f'<FONT FACE="DejaVu Sans" COLOR="{INK}">{kol}</FONT>'
                f' <FONT FACE="DejaVu Sans Mono" COLOR="{MUTED}" POINT-SIZE="9">{typ}</FONT>'
                f'{klucz_html}'
                f'</TD></TR>'
            )
        label = (
            f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" '
            f'CELLPADDING="4" COLOR="{INK}">'
            + "".join(rows) + "</TABLE>>"
        )
        g.node(name, label=label)

    tabela("USERS", "USERS", [
        ("id", "int", "PK"),
        ("email", "text", "UK"),
        ("haslo_hash", "text", ""),
        ("imie", "text", ""),
        ("nazwisko", "text", ""),
        ("rola", "text", ""),
        ("nr_albumu", "text", ""),
        ("pierwszy_login", "int", ""),
    ])

    tabela("FIRMY", "FIRMY", [
        ("id", "int", "PK"),
        ("nazwa", "text", ""),
        ("adres", "text", ""),
        ("nip", "text", ""),
    ])

    tabela("EFEKTY", "EFEKTY", [
        ("id", "int", "PK"),
        ("kod", "text", "UK"),
        ("opis", "text", ""),
    ])

    tabela("PRAKTYKI", "PRAKTYKI", [
        ("id", "int", "PK"),
        ("student_id", "int", "FK"),
        ("opiekun_uczelniany_id", "int", "FK"),
        ("opiekun_zakladowy_id", "int", "FK"),
        ("firma_id", "int", "FK"),
        ("specjalnosc", "text", ""),
        ("rok_akademicki", "text", ""),
        ("data_od", "date", ""),
        ("data_do", "date", ""),
        ("liczba_dni", "int", ""),
    ])

    tabela("DOKUMENTY", "DOKUMENTY", [
        ("id", "int", "PK"),
        ("praktyka_id", "int", "FK"),
        ("typ", "text", ""),
        ("status", "text", ""),
        ("dane_json", "text", ""),
        ("autor_id", "int", "FK"),
        ("recenzent_id", "int", "FK"),
        ("ocena", "text", ""),
    ])

    tabela("WORKFLOW_LOG", "WORKFLOW_LOG", [
        ("id", "int", "PK"),
        ("dokument_id", "int", "FK"),
        ("status_z", "text", ""),
        ("status_na", "text", ""),
        ("uzytkownik_id", "int", "FK"),
        ("komentarz", "text", ""),
        ("kiedy", "datetime", ""),
    ])

    # Relacje (FK)
    g.edge("PRAKTYKI:student_id",            "USERS:id",     color=ACCENT,      label="student")
    g.edge("PRAKTYKI:opiekun_uczelniany_id", "USERS:id",     color="#0369a1",   label="op. uczeln.")
    g.edge("PRAKTYKI:opiekun_zakladowy_id",  "USERS:id",     color="#15803d",   label="op. zakł.")
    g.edge("PRAKTYKI:firma_id",              "FIRMY:id",     color=MUTED)
    g.edge("DOKUMENTY:praktyka_id",          "PRAKTYKI:id",  color=ACCENT)
    g.edge("DOKUMENTY:autor_id",             "USERS:id",     color=MUTED, style="dashed")
    g.edge("WORKFLOW_LOG:dokument_id",       "DOKUMENTY:id", color=ACCENT)
    g.edge("WORKFLOW_LOG:uzytkownik_id",     "USERS:id",     color=MUTED, style="dashed")

    g.render(filename=str(OUT / "04-erd"), cleanup=True)
    print("  ✓ 04-erd.png")


# ---------------------------------------------------------------------------
# 4) Sequence diagram — proces weryfikacji (matplotlib, bo dot tego nie umie)
# ---------------------------------------------------------------------------
def sekwencja():
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Rectangle

    fig, ax = plt.subplots(figsize=(14, 11))
    ax.set_facecolor(PAPER)
    fig.patch.set_facecolor(PAPER)

    actors = [
        ("Student",       1.5,  ACCENT),
        ("Aplikacja Flask", 4.5, INK),
        ("Baza danych",    7.5,  "#0369a1"),
        ("Opiekun",       10.5, "#15803d"),
        ("Generator PDF", 13.5, MUTED),
    ]

    TOP = 16
    BOT = 0.5

    # Pasy aktorów
    for nazwa, x, kolor in actors:
        # nagłówek
        ax.add_patch(Rectangle((x - 1.2, TOP - 0.4), 2.4, 0.8,
                               facecolor=kolor, edgecolor=kolor, zorder=3))
        ax.text(x, TOP, nazwa, color=PAPER, fontsize=11, fontweight="bold",
                ha="center", va="center", zorder=4)
        # pionowa linia życia
        ax.plot([x, x], [TOP - 0.4, BOT], color=LINE, linewidth=1.2, zorder=1)

    def arrow(from_x, to_x, y, label, kolor=INK, styl="-"):
        a = FancyArrowPatch((from_x, y), (to_x, y),
                            arrowstyle="-|>", mutation_scale=14,
                            color=kolor, linewidth=1.4, zorder=2,
                            linestyle=styl)
        ax.add_patch(a)
        mid = (from_x + to_x) / 2
        ax.text(mid, y + 0.15, label, fontsize=9, color=INK,
                ha="center", va="bottom", zorder=4,
                bbox=dict(boxstyle="round,pad=0.25", facecolor=PAPER,
                          edgecolor="none"))

    # Skrypt (numer, od, do, etykieta, kolor opcjonalny)
    kroki = [
        (15,    1.5,  4.5, "1. POST /dokument/.../edytuj"),
        (14,    4.5,  4.5, "2. Walidacja CSRF + danych", MUTED),
        (13,    4.5,  7.5, "3. UPDATE dokumenty SET dane_json=…"),
        (12,    4.5,  1.5, "4. Flash: Zapisano zmiany", "#15803d"),
        (11,    1.5,  4.5, "5. Klika „Złóż do recenzji”", ACCENT),
        (10,    4.5,  4.5, "6. Walidacja kompletności (120 dni, 13 efektów)", MUTED),
        ( 9,    4.5,  7.5, "7. UPDATE status='Submitted' + INSERT workflow_log"),
        ( 8,    4.5,  1.5, "8. Flash: Status: Złożony", "#15803d"),
        ( 7,   10.5,  4.5, "9. Opiekun otwiera „Do recenzji”"),
        ( 6,    4.5,  7.5, "10. SELECT dokumenty WHERE status='Submitted'"),
        ( 5,    4.5, 10.5, "11. Lista dokumentów do recenzji"),
        ( 4,   10.5,  4.5, "12. Klika „Pobierz PDF”", ACCENT),
        ( 3,    4.5, 13.5, "13. generuj_pdf(dok, prakt)"),
        ( 2,   13.5,  4.5, "14. BytesIO z PDF", "#15803d"),
        ( 1,    4.5, 10.5, "15. Plik PDF do pobrania", "#15803d"),
    ]
    for k in kroki:
        if len(k) == 4:
            y, fx, tx, lbl = k
            kolor = INK
        else:
            y, fx, tx, lbl, kolor = k
        styl = "--" if "Walidacja" in lbl else "-"
        arrow(fx, tx, y, lbl, kolor, styl)

    ax.set_xlim(-0.5, 15.5)
    ax.set_ylim(0, 17)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(OUT / "01-sekwencja.png", dpi=160,
                facecolor=PAPER, bbox_inches="tight")
    plt.close()
    print("  ✓ 01-sekwencja.png")


if __name__ == "__main__":
    print("Renderuję diagramy do PNG:")
    sekwencja()
    stany()
    flowchart()
    erd()
    print("\nGotowe.")
