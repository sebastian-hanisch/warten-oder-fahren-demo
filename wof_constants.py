"""Konstanten: Modell, Politiken, Zellen der Bänder, Regler-Grenzen, Farben, Presets, Annahmentext."""

import math

# Modell (Stück 14 der Linie Tourenbildung)
DEPOT = (50.0, 50.0)
HORIZON = 480.0                      # Eingänge in [0, 480] Minuten
DELTA = 120.0                        # Lieferfrist = Eingang + 120
CAPACITY = 8                         # Last je Fahrzeug (Aufträge haben Last 1 bis 3)
REVENUE = 60.0                       # Erlös je angenommenem Auftrag
THRESHOLD = 60.0                     # Schwelle: Zusatzstrecke höchstens so hoch wie der Erlös
INF = math.inf

# Politiken: Schlüssel -> (Name, tau, Schwelle). Wunschstart einer Route = min(späteste Abfahrt, Eingang des ältesten Auftrags + tau)
POLICIES = {
    "W0": ("Sofort", 0.0, None),
    "W10": ("Warten 10", 10.0, None),
    "W20": ("Warten 20", 20.0, None),
    "W40": ("Warten 40", 40.0, None),
    "Winf": ("Spätestens", INF, None),
    "W0S": ("Sofort + Schwelle", 0.0, THRESHOLD),
    "W20S": ("Warten 20 + Schwelle", 20.0, THRESHOLD),
    "WinfS": ("Spätestens + Schwelle", INF, THRESHOLD),
}
TAUS = (0.0, 10.0, 20.0, 40.0, INF)
TAU_KEYS = ("W0", "W10", "W20", "W40", "Winf")

# Zellen der Bänder: (Rate je Stunde, Fahrzeuge); Rate/60 = lambda je Minute (0,05 / 0,10 / 0,15 / 0,20)
CELLS = ((3, 3), (6, 3), (6, 2), (9, 3), (12, 3))
BAND_FILE = "wof_bands.json"
BAND_SETS = ("fest", "frisch")
BAND_SEEDS = {"fest": tuple(range(60)), "frisch": tuple(range(200000, 200060))}

# Regler der Seitenleiste
RATE_MIN, RATE_MAX, DEFAULT_RATE = 1, 15, 6      # Aufträge je Stunde
K_MIN, K_MAX, DEFAULT_K = 1, 4, 3
SEED_MAX, DEFAULT_SEED = 999999, 0
DEFAULT_TAU = 4                                  # Index in TAUS: Spätestens
DEFAULT_THR = 0                                  # 0 = ohne Schwelle, 1 = mit Schwelle
LEVEL_SE = 2.0                                   # „gleichauf“: Differenz innerhalb von zwei Standardfehlern

COLORS = {"W0": "#c0504d", "W10": "#d8a13a", "W20": "#b5a14a", "W40": "#6b9a5b", "Winf": "#2F6B65"}
ROUTE_COLORS = ("#2F6B65", "#c0504d", "#4c78a8", "#d8a13a", "#7b5ea7", "#8c564b", "#17becf", "#e377c2")

# Presets (die Zahlen in den Hilfetexten prüft tests/test_claims.py); das erste ist die Voreinstellung
PRESETS = {
    "Spätestens statt Sofort (6 je Stunde, 3 Fahrzeuge)": {"rate": 6, "K": 3, "seed": 0, "tau": 4, "thr": 0},
    "Dünner Strom: Warten sammelt (3 je Stunde)": {"rate": 3, "K": 3, "seed": 0, "tau": 4, "thr": 0},
    "Dichter Strom: der Vorteil schrumpft (12 je Stunde)": {"rate": 12, "K": 3, "seed": 0, "tau": 4, "thr": 0},
    "Die Schwelle schadet bei Sofort (9 je Stunde)": {"rate": 9, "K": 3, "seed": 0, "tau": 0, "thr": 1},
    "Die Schwelle nützt beim Warten (12 je Stunde)": {"rate": 12, "K": 3, "seed": 0, "tau": 4, "thr": 1},
}
PRESET_HELP = {
    "Spätestens statt Sofort (6 je Stunde, 3 Fahrzeuge)": "Im Mittel über 60 feste Instanzen (je Instanz ein Tag mit rund 50 Aufträgen): Spätestens gegen Sofort +158 ± 21 Gewinn je Tag, in 50 von 60 Instanzen besser, in 10 schlechter. Die Seite zeigt den Tag mit Seed 0.",
    "Dünner Strom: Warten sammelt (3 je Stunde)": "Bei 3 Aufträgen je Stunde (rund 25 am Tag) fährt Spätestens 9,9 statt 15,8 Routen mit 4,55 statt 2,96 Last je Route: Gewinn +235 ± 14 gegen Sofort, in 59 von 60 Instanzen besser (frische Instanzen +253 ± 15). Annahmen 89,5 gegen 92,0 %.",
    "Dichter Strom: der Vorteil schrumpft (12 je Stunde)": "Bei 12 Aufträgen je Stunde (rund 98 am Tag) ist Spätestens gegen Sofort auf den festen Instanzen gleichauf (+7 ± 28, 32 von 60 besser). Auf 60 frischen Instanzen sind es +111 ± 26: Dass der Vorteil verschwindet, zeigen nur die festen Instanzen (dort ist der Unterschied nicht nachweisbar).",
    "Die Schwelle schadet bei Sofort (9 je Stunde)": "Annahmeschwelle (Zusatzstrecke höchstens 60) gegen „alles annehmen“, beide mit Sofort, 9 Aufträge je Stunde: −253 ± 23 Gewinn je Tag, nur 6 von 60 Instanzen besser. Unter Sofort fährt oft ein Auftrag allein; die Zusatzstrecke ist dann hoch, und die Schwelle lehnt viele Aufträge ab.",
    "Die Schwelle nützt beim Warten (12 je Stunde)": "Annahmeschwelle gegen „alles annehmen“, beide mit Spätestens, 12 Aufträge je Stunde: +225 ± 26 Gewinn je Tag, in 54 von 60 Instanzen besser (frische Instanzen +131 ± 23). Beim Warten ist die Zusatzstrecke die des Sammelns.",
}
ASSUMPTIONS_MARKDOWN = """- **Deterministisches Modell:** Fahrzeit gleich Strecke, keine Verspätungen, keine unsicheren Fahrzeiten. Ohne Unsicherheit kostet „Spätestens“ kein Risiko; mit Verspätungsrisiko würde der Vorteil des Wartens schrumpfen (nicht gemessen). Das ist die größte Grenze.
- **Ein Depot, eine kleine Flotte:** K = 1 bis 4 Fahrzeuge der Kapazität 8, Aufträge mit Last 1 bis 3, Ort gleichverteilt im 100 × 100 Gebiet, Eingänge als Poisson-Strom in [0, 480] Minuten, Lieferfrist gleich Eingang plus 120, Erlös 60 je angenommenem Auftrag. Die Rangfolge hängt an Rate und Flotte; die fünf Zellen der Bänder zeigen das, tragen aber keine allgemeine Aussage.
- **Annahmetest hinreichend, nicht notwendig:** Ein Auftrag wird nur angenommen, wenn die Zuteilung der Routen nach Wunschstart zulässig ist; das kann zulässige Mengen ablehnen. Die Annahmen sind eine untere Schranke jeder Politik.
- **Schwelle auf der Planungsdifferenz:** Die Zusatzstrecke ist die des aktuellen Plans (Riesentour mit Split), nicht die des endgültigen; das erklärt einen Teil des Befunds, dass die Schwelle bei „Sofort“ schadet.
- **Kein Hindsight-Orakel:** Die Politiken werden nur untereinander verglichen; die Lücke zum Optimum ist unbekannt. Differenzen stehen mit Standardfehlern (Stichprobenstreuung durch Wurzel n über 60 Instanzen); „gleichauf“ heißt innerhalb von zwei Standardfehlern.
- **Feste und frische Instanzen:** Die Zellen und Politiken sind vor der Messung festgelegt (feste Seeds 0 bis 59); 60 frische Seeds (ab 200000) prüfen dieselben Aussagen. Auf den frischen Instanzen fällt der Vorteil des Wartens bei 12 Aufträgen je Stunde nicht auf null.
- **Keine Rechenzeiten:** Die Zeit im Modell ist Modellzeit; keine Rechenzeit wird gemessen oder in Tests geprüft.
- **Nicht gebaut:** mehrere Depots, Neuzuteilung unterwegs, Wartestrategien entlang der Route, Szenarioplanung, Lernverfahren, Hindsight-Orakel, Erlös- und Fristregler.
"""
