"""
Generowanie dokumentów PDF (etap 11) — biblioteka reportlab.

Każdy typ dokumentu ma własny układ, wzorowany na oryginalnych załącznikach
ANS w Elblągu. Polskie znaki działają dzięki dołączonej czcionce DejaVu Sans
(folder fonts/), więc PDF generuje się poprawnie na każdym systemie.
"""

import io
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import forms_meta as meta
import models

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
ATRAMENT = colors.HexColor("#1a1f2b")
AKCENT = colors.HexColor("#c2410c")
LINIA = colors.HexColor("#d8d2c4")

_fonts_loaded = False


def _zaladuj_fonty():
    global _fonts_loaded
    if _fonts_loaded:
        return "DejaVu", "DejaVu-Bold"
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", str(FONTS_DIR / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONTS_DIR / "DejaVuSans-Bold.ttf")))
        _fonts_loaded = True
        return "DejaVu", "DejaVu-Bold"
    except Exception:
        # Awaryjnie standardowa czcionka (polskie znaki mogą nie wyjść idealnie).
        return "Helvetica", "Helvetica-Bold"


def _style():
    font, font_b = _zaladuj_fonty()
    ss = getSampleStyleSheet()
    s = {
        "uczelnia": ParagraphStyle("uczelnia", fontName=font_b, fontSize=11,
                                   alignment=TA_CENTER, textColor=ATRAMENT, leading=14),
        "instytut": ParagraphStyle("instytut", fontName=font, fontSize=9,
                                   alignment=TA_CENTER, textColor=colors.grey, leading=12),
        "tytul": ParagraphStyle("tytul", fontName=font_b, fontSize=16,
                                alignment=TA_CENTER, textColor=ATRAMENT,
                                spaceBefore=12, spaceAfter=4),
        "zalacznik": ParagraphStyle("zalacznik", fontName=font, fontSize=8,
                                    alignment=2, textColor=colors.grey),
        "naglowek": ParagraphStyle("naglowek", fontName=font_b, fontSize=11,
                                   textColor=AKCENT, spaceBefore=14, spaceAfter=4),
        "etykieta": ParagraphStyle("etykieta", fontName=font_b, fontSize=9,
                                   textColor=ATRAMENT),
        "tekst": ParagraphStyle("tekst", fontName=font, fontSize=9.5,
                                textColor=ATRAMENT, leading=14, alignment=TA_JUSTIFY),
        "maly": ParagraphStyle("maly", fontName=font, fontSize=8,
                               textColor=colors.grey, leading=11),
        "cell": ParagraphStyle("cell", fontName=font, fontSize=8.5,
                               textColor=ATRAMENT, leading=11),
        "cell_b": ParagraphStyle("cell_b", fontName=font_b, fontSize=8.5,
                                 textColor=ATRAMENT, leading=11),
    }
    return s, font, font_b


def _naglowek_uczelni(story, s):
    story.append(Paragraph("Akademia Nauk Stosowanych w Elblągu", s["uczelnia"]))
    story.append(Paragraph("Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego", s["instytut"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.2, color=ATRAMENT))


def _info_studenta(story, s, prakt):
    """Wspólny blok z danymi studenta i praktyki."""
    dane = [
        ["Student:", f"{prakt['student_imie']} {prakt['student_nazwisko']}",
         "Nr albumu:", prakt["nr_albumu"] or "—"],
        ["Kierunek:", "Informatyka", "Specjalność:", prakt["specjalnosc"] or "—"],
        ["Firma:", prakt["firma_nazwa"] or "—", "Rok ak.:", prakt["rok_akademicki"] or "—"],
        ["Termin:", f"{prakt['data_od'] or '—'} – {prakt['data_do'] or '—'}",
         "Liczba dni:", str(prakt["liczba_dni"])],
    ]
    t = Table(dane, colWidths=[2.6*cm, 6.8*cm, 2.4*cm, 4.2*cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), s["cell"].fontName),
        ("FONTNAME", (0, 0), (0, -1), s["cell_b"].fontName),
        ("FONTNAME", (2, 0), (2, -1), s["cell_b"].fontName),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), ATRAMENT),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINIA),
    ]))
    story.append(Spacer(1, 8))
    story.append(t)


def _podpisy(story, s, podpisy):
    story.append(Spacer(1, 30))
    kom = [[Paragraph("." * 38 + "<br/>" + p, s["maly"]) for p in podpisy]]
    t = Table(kom, colWidths=[(17.0/len(podpisy))*cm] * len(podpisy))
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"),
                           ("TOPPADDING", (0, 0), (-1, -1), 6)]))
    story.append(t)


# ----------------------------------------------------------------------------
#  Treść specyficzna dla każdego typu dokumentu
# ----------------------------------------------------------------------------
def _tresc_karta(story, s, dane, prakt):
    story.append(Paragraph("Porozumienie i skierowanie", s["naglowek"]))
    story.append(Paragraph(
        f"Na podstawie porozumienia nr {prakt['porozumienie_nr'] or '…'} kieruję studenta "
        f"na praktykę zawodową do zakładu pracy: <b>{prakt['firma_nazwa'] or '…'}</b>.", s["tekst"]))
    story.append(Paragraph("Opiekunowie praktyki", s["naglowek"]))
    story.append(Paragraph(
        f"Uczelniany: <b>{(prakt['ou_imie'] or '') + ' ' + (prakt['ou_nazwisko'] or '') or '—'}</b><br/>"
        f"Zakładowy: <b>{(prakt['oz_imie'] or '') + ' ' + (prakt['oz_nazwisko'] or '') or '—'}</b>", s["tekst"]))
    if dane.get("ocena_opisowa"):
        story.append(Paragraph("Ocena przebiegu praktyki", s["naglowek"]))
        story.append(Paragraph(dane.get("ocena_opisowa", ""), s["tekst"]))
    _podpisy(story, s, ["Opiekun zakładowy", "Opiekun uczelniany", "Dyrektor Instytutu"])


def _tresc_program(story, s, dane, prakt):
    story.append(Paragraph("Program praktyki zawodowej", s["naglowek"]))
    wiersze = [[Paragraph("Efekt", s["cell_b"]),
                Paragraph("Przykładowe prace wykonywane przez praktykanta", s["cell_b"])]]
    prace = dane.get("prace_efekty", {})
    for kod, opis in meta.EFEKTY:
        wiersze.append([Paragraph(kod, s["cell_b"]),
                        Paragraph(prace.get(kod, "") or "—", s["cell"])])
    t = Table(wiersze, colWidths=[1.2*cm, 15.8*cm], repeatRows=1)
    t.setStyle(_tabela_styl(s))
    story.append(t)

    story.append(Paragraph("Harmonogram praktyki", s["naglowek"]))
    h = [[Paragraph("L.p.", s["cell_b"]), Paragraph("Dział / komórka", s["cell_b"]),
          Paragraph("Liczba dni", s["cell_b"])]]
    suma = 0
    for i, w in enumerate(dane.get("harmonogram", []), start=1):
        dni = int(w.get("dni") or 0)
        suma += dni
        h.append([Paragraph(str(i), s["cell"]), Paragraph(w.get("dzial", ""), s["cell"]),
                  Paragraph(str(dni), s["cell"])])
    h.append([Paragraph("", s["cell"]), Paragraph("Łącznie", s["cell_b"]),
              Paragraph(str(suma), s["cell_b"])])
    h.append([Paragraph("", s["cell"]), Paragraph("Wymagana", s["cell_b"]),
              Paragraph("120", s["cell_b"])])
    th = Table(h, colWidths=[1.5*cm, 12.5*cm, 3.0*cm], repeatRows=1)
    th.setStyle(_tabela_styl(s))
    story.append(th)
    _podpisy(story, s, ["Opiekun uczelniany", "Opiekun zakładowy", "Student"])


def _tresc_dziennik(story, s, dane, prakt):
    story.append(Paragraph("Dziennik praktyki zawodowej", s["naglowek"]))
    wiersze = [[Paragraph("Dzień", s["cell_b"]), Paragraph("Data", s["cell_b"]),
                Paragraph("Opis wykonanych prac", s["cell_b"]),
                Paragraph("Nr efektów", s["cell_b"])]]
    for i, w in enumerate(dane.get("wpisy", []), start=1):
        wiersze.append([Paragraph(str(w.get("dzien") or i), s["cell"]),
                        Paragraph(w.get("data", ""), s["cell"]),
                        Paragraph(w.get("opis", ""), s["cell"]),
                        Paragraph(str(w.get("efekty", "")), s["cell"])])
    t = Table(wiersze, colWidths=[1.2*cm, 2.3*cm, 10.5*cm, 3.0*cm], repeatRows=1)
    t.setStyle(_tabela_styl(s))
    story.append(t)
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Łączna liczba wpisów: {len(dane.get('wpisy', []))} / 120", s["maly"]))
    _podpisy(story, s, ["Zakładowy opiekun praktyki"])


def _tresc_efekty(story, s, dane, prakt):
    story.append(Paragraph(
        f"W ramach praktyki zrealizowanej w wymiarze {dane.get('liczba_godzin', '…')} godzin "
        f"student uzyskał następujące efekty uczenia się:", s["tekst"]))
    story.append(Spacer(1, 6))
    potw = dane.get("potwierdzenia", {})
    wiersze = [[Paragraph("Nr", s["cell_b"]), Paragraph("Efekt uczenia się", s["cell_b"]),
                Paragraph("Potwierdzenie", s["cell_b"])]]
    for kod, opis in meta.EFEKTY:
        wynik = potw.get(kod, "—")
        kolor = "#15803d" if wynik == "uzyskał" else ("#b91c1c" if wynik == "nie uzyskał" else "#666")
        wiersze.append([Paragraph(kod, s["cell_b"]), Paragraph(opis, s["cell"]),
                        Paragraph(f'<font color="{kolor}"><b>{wynik}</b></font>', s["cell"])])
    t = Table(wiersze, colWidths=[1.0*cm, 13.0*cm, 3.0*cm], repeatRows=1)
    t.setStyle(_tabela_styl(s))
    story.append(t)
    if dane.get("opinia_uczelniana"):
        story.append(Paragraph("Opinia opiekuna uczelnianego", s["naglowek"]))
        story.append(Paragraph(dane["opinia_uczelniana"], s["tekst"]))
    _podpisy(story, s, ["Opiekun zakładowy", "Opiekun uczelniany"])


def _tresc_sprawozdanie(story, s, dane, prakt):
    sekcje = [
        ("Charakterystyka miejsca odbywania praktyki", "charakterystyka"),
        ("Opis i analiza wykonywanych prac", "opis_prac"),
        ("Wiedza i umiejętności uzyskane w trakcie praktyki (samoocena)", "samoocena"),
    ]
    for tytul, klucz in sekcje:
        story.append(Paragraph(tytul, s["naglowek"]))
        story.append(Paragraph(dane.get(klucz, "") or "—", s["tekst"]))
    _podpisy(story, s, ["Data i podpis studenta"])


def _tresc_ankieta(story, s, dane, prakt):
    story.append(Paragraph("Kwestionariusz ankiety oceniającej przebieg praktyk", s["naglowek"]))
    odp = dane.get("odpowiedzi", {})
    wiersze = [[Paragraph("#", s["cell_b"]), Paragraph("Stwierdzenie", s["cell_b"]),
                Paragraph("Odpowiedź", s["cell_b"])]]
    for i, pyt in enumerate(meta.ANKIETA_PYTANIA, start=1):
        wiersze.append([Paragraph(str(i), s["cell"]), Paragraph(pyt, s["cell"]),
                        Paragraph(odp.get(str(i), "—"), s["cell_b"])])
    t = Table(wiersze, colWidths=[0.8*cm, 12.2*cm, 4.0*cm], repeatRows=1)
    t.setStyle(_tabela_styl(s))
    story.append(t)
    if dane.get("uwagi"):
        story.append(Paragraph("Dodatkowe uwagi", s["naglowek"]))
        story.append(Paragraph(dane["uwagi"], s["tekst"]))


def _tabela_styl(s):
    return TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, LINIA),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f1ea")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ])


_GENERATORY = {
    "karta": _tresc_karta,
    "program": _tresc_program,
    "dziennik": _tresc_dziennik,
    "efekty": _tresc_efekty,
    "sprawozdanie": _tresc_sprawozdanie,
    "ankieta": _tresc_ankieta,
}


def generuj_pdf(dok_row, prakt_row) -> io.BytesIO:
    """Buduje PDF dla danego dokumentu i zwraca bufor bajtów (BytesIO)."""
    s, font, font_b = _style()
    dane = models.dane_dokumentu(dok_row)
    typ = dok_row["typ"]
    info = meta.DOKUMENTY[typ]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=1.6*cm, bottomMargin=1.6*cm,
                            leftMargin=2.0*cm, rightMargin=2.0*cm,
                            title=info["nazwa"])
    story = []
    story.append(Paragraph(f"Załącznik nr {info['zalacznik']}", s["zalacznik"]))
    _naglowek_uczelni(story, s)
    story.append(Paragraph(info["nazwa"].upper(), s["tytul"]))
    status_pl = meta.STATUS_PL.get(dok_row["status"], dok_row["status"])
    story.append(Paragraph(f"Status: {status_pl}", s["maly"]))

    if typ != "ankieta":   # ankieta jest anonimowa
        _info_studenta(story, s, prakt_row)

    _GENERATORY[typ](story, s, dane, prakt_row)

    doc.build(story)
    buf.seek(0)
    return buf
