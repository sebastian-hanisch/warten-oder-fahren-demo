"""PDF-Export des aktuellen Tages (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import wof_constants as C
from wof_evaluation import Day, Settings, de, policy_name, signed, tau_text

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2", "∞": "unendlich", "‖": "|", "←": "<-", "✔": "x"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, day: Day) -> bytes:
    r = day.results["_chosen"]
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Warten oder Fahren"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    thr = f", Annahmeschwelle {de(C.THRESHOLD, 0)}" if s.thr else ", ohne Annahmeschwelle"
    pdf.multi_cell(0, 5, _s(f"{s.rate} Aufträge je Stunde, {s.K} Fahrzeuge (Kapazität {C.CAPACITY}), Lieferfrist {de(C.DELTA, 0)} Minuten, Erlös {de(C.REVENUE, 0)} je angenommenem Auftrag, Seed {s.seed}. "
                           f"Gewählt: {policy_name(day.chosen)} (tau = {tau_text(s.tau_value)}){thr}. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    widths = (58, 24, 24, 24, 22, 22)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, ("Politik", "Angenommen", "Strecke", "Gewinn", "Routen", "Last/Route")):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    rows = [("Gewählt: " + policy_name(day.chosen), r)] + [(policy_name(k), day.results[k]) for k in C.POLICIES]
    for name, res in rows:
        for w, v in zip(widths, (name, f"{res['accepted']} von {res['n']}", de(res["dist"], 0), signed(res["profit"]), str(res["routes"]), de(res["load"]))):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Gewinn = Erlös der angenommenen Aufträge minus gefahrene Strecke. Deterministische Fahrzeiten, ein Lauf je Politik. Quelle: warten-oder-fahren-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
