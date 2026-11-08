# Warten oder Fahren – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-warten-oder-fahren-demo.streamlit.app/)** -->

Letztes Stück der **Tourenbildung**-Linie (Stück 14) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Verfahren: **Riesentour und Split**, ein Verfahren mit wachsendem Beispiel). Stück 13 ([neue-auftraege-split-demo](https://github.com/sebastian-hanisch/neue-auftraege-split-demo)) hat Aufträge **vor** der Abfahrt fortgeschrieben, ohne Zeitachse; dort blieb offen, was das Sammeln kostet. Hier die **Zeit**: Aufträge treffen über den Tag ein, jeder mit Lieferfrist, wenige Fahrzeuge fahren vom Depot. Zwei Entscheidungen: **Warten oder Fahren** (wann startet eine geplante Route?) und **Annehmen oder Ablehnen** (bei Eintreffen). Der Split mit Fristen kommt aus [zeitfenster-split-demo](https://github.com/sebastian-hanisch/zeitfenster-split-demo) (Stück 8).

## Kernfrage

Soll eine Route sofort losfahren oder warten, und nimmt man jeden planbaren Auftrag an oder nur, wenn die Zusatzstrecke den Erlös nicht übersteigt? Die Demo zeigt ein **Linienbeispiel von Hand**, einen **Tag** mit Zeitstrahl der Fahrzeuge, Wartestapel und Karte, den **Gewinn des Wartens** und der **Annahmeschwelle** über 60 Instanzen je Zelle (Rate und Flotte) und wo es kippt, mit festen und frischen Instanzen nebeneinander.

## Modell

Depot in der Mitte eines 100 × 100 Gebiets, K Fahrzeuge der Kapazität 8, Fahrzeit gleich Strecke. Aufträge treffen als Poisson-Strom (Rate je Stunde, in den Bändern 3, 6, 9, 12) in [0, 480] Minuten ein, mit gleichverteiltem Ort, Last 1 bis 3 und **Lieferfrist Eingang + 120**; Erlös 60 je angenommenem Auftrag. Eine Route fährt zum Zeitpunkt s los und muss jeden Stopp bis zu seiner Frist erreichen (s ≤ ℓ, spätester Abfahrt = Minimum über die Stopps von Frist − Fahrstrecke bis zum Stopp); das Fahrzeug ist danach bis zur Rückkehr belegt. **Die Wartenden bilden eine Riesentour**, der Split mit Fristen zerlegt sie in Routen (Vorwärtsprüfung, Abbruch beim ersten Verstoß), der neue Auftrag kommt an die Stelle mit dem kleinsten Split (Stück 13). **Warten:** Politik W_τ startet eine geplante Route zum Zeitpunkt min(ℓ, Eingang ihres ältesten Auftrags + τ), frühestens bei freiem Fahrzeug; τ = 0 ist „Sofort“, τ = ∞ „Spätestens“. **Annehmen:** nur, wenn ein Plan alle noch nicht gestarteten angenommenen Aufträge samt dem neuen rechtzeitig bedient (Routen den Fahrzeugen nach Wunschstart zugeteilt); sonst abgelehnt. **Schwelle:** zusätzlich nur, wenn die Zusatzstrecke des neuen Plans höchstens 60 beträgt.

## Methodik

- **Gewinn:** 60 · Annahmen − gefahrene Strecke, je Tag; Politiken werden **gepaart** verglichen (gleiche Aufträge): Differenz im Mittel ± Standardfehler (Stichprobenstreuung durch Wurzel 60), in Klammern die Instanzen mit besserem / gleichem / schlechterem Gewinn. „Gleichauf“ heißt innerhalb von zwei Standardfehlern.
- **Zellen und Politiken vor der Messung festgelegt:** (3, 3), (6, 3), (6, 2), (9, 3), (12, 3) Aufträge je Stunde und Fahrzeuge; τ = 0, 10, 20, 40, ∞ ohne Schwelle, dazu Sofort, Warten 20 und Spätestens mit Schwelle.
- **Instanzen:** **60 feste** (Seeds 0 bis 59) und **60 frische** (Seeds ab 200000) je Zelle; ein Lauf je Politik und Instanz (die Simulation ist deterministisch). Keine Rechenzeiten.
- **Kein Hindsight-Orakel:** die Politiken werden nur untereinander verglichen.

## Befunde (gemessen, keine Behauptungen)

**1. Warten sammelt: weniger, vollere Routen.** Bei 3 Aufträgen je Stunde und 3 Fahrzeugen fährt Spätestens 9,9 statt 15,8 Routen je Tag mit 4,55 statt 2,96 Last je Route; die Strecke je angenommenem Auftrag sinkt von 63,8 auf 53,2. Der Preis sind weniger Annahmen (89,5 % gegen 92,0 %). Warten 20 Minuten liegt dazwischen (+102 ± 10 (54/0/6) gegen Sofort).

Feste Instanzen (60 je Zelle):

| Zelle (Aufträge je Stunde, Fahrzeuge) | Sofort: Gewinn | Spätestens − Sofort | Schwelle − alles annehmen, bei Sofort | Schwelle − alles annehmen, bei Spätestens |
|---|---|---|---|---|
| 3 je Stunde, K = 3 (im Mittel 25 Aufträge) | −68 | +235 ± 14 (59/0/1) | +209 ± 16 (57/0/3) | +76 ± 14 (47/0/13) |
| 6 je Stunde, K = 3 (im Mittel 50 Aufträge) | +384 | +158 ± 21 (50/0/10) | −103 ± 19 (14/0/46) | +28 ± 22 (33/0/27) |
| 6 je Stunde, K = 2 (im Mittel 50 Aufträge) | +392 | +37 ± 21 (35/0/25) | −73 ± 16 (19/0/41) | +80 ± 17 (45/0/15) |
| 9 je Stunde, K = 3 (im Mittel 74 Aufträge) | +715 | +111 ± 22 (45/0/15) | −253 ± 23 (6/0/54) | +94 ± 27 (41/0/19) |
| 12 je Stunde, K = 3 (im Mittel 98 Aufträge) | +1003 | +7 ± 28 (32/0/28) | −286 ± 34 (9/0/51) | +225 ± 26 (54/0/6) |

Frische Instanzen (60 je Zelle):

| Zelle (Aufträge je Stunde, Fahrzeuge) | Sofort: Gewinn | Spätestens − Sofort | Schwelle − alles annehmen, bei Sofort | Schwelle − alles annehmen, bei Spätestens |
|---|---|---|---|---|
| 3 je Stunde, K = 3 (im Mittel 24 Aufträge) | −90 | +253 ± 15 (60/0/0) | +227 ± 15 (57/0/3) | +80 ± 14 (46/0/14) |
| 6 je Stunde, K = 3 (im Mittel 48 Aufträge) | +389 | +141 ± 17 (51/0/9) | −115 ± 19 (13/0/47) | +64 ± 20 (42/0/18) |
| 6 je Stunde, K = 2 (im Mittel 48 Aufträge) | +390 | +41 ± 17 (37/0/23) | −68 ± 14 (17/0/43) | +117 ± 17 (48/0/12) |
| 9 je Stunde, K = 3 (im Mittel 72 Aufträge) | +728 | +112 ± 25 (45/0/15) | −262 ± 22 (3/0/57) | +97 ± 28 (37/0/23) |
| 12 je Stunde, K = 3 (im Mittel 95 Aufträge) | +999 | +111 ± 26 (45/0/15) | −250 ± 30 (8/0/52) | +131 ± 23 (46/0/14) |

**2. Der Gewinn des Wartens sinkt mit der Auslastung; ob er bei 12 je Stunde null ist, entscheiden die beiden Instanzmengen nicht gleich.** Auf den festen Instanzen fällt Spätestens gegen Sofort von +235 (3 je Stunde) auf +7 ± 28 (12 je Stunde, gleichauf); auf den **frischen** Instanzen bleibt er dort bei +111 ± 26 (45/0/15) (besser). Auf den festen Instanzen ist der Unterschied bei 12 je Stunde nicht nachweisbar, auf den frischen deutlich positiv; die Aussage „Warten bringt bei dichtem Strom nichts“ stützen nur die festen Instanzen, und „gleichauf“ heißt nicht „nichts“. Bei K = 2 und 6 je Stunde ist der Vorteil klein (+37 ± 21 (35/0/25) fest, +41 ± 17 (37/0/23) frisch).

**3. Die Annahmeschwelle schadet bei „Sofort“ ab 6 Aufträgen je Stunde und nützt beim Warten (fest in vier von fünf Zellen nachweisbar).** Unter „Sofort“ fährt oft ein Auftrag allein, die Zusatzstrecke eines neuen Auftrags ist dann hoch, und die Schwelle lehnt viele Aufträge ab (Annahmen bei 6 je Stunde: 70,5 % ohne, 27,3 % mit Schwelle); dass es Aufträge sind, die nach dem Sammeln billig wären, ist plausibel, aber nicht direkt gemessen. Gegen „alles annehmen“ verliert sie bei Sofort in vier von fünf Zellen (dritte Zahlenspalte der Tabelle oben; in der dünnsten Zelle, 3 je Stunde, gewinnt sie dort +209 ± 16) und gewinnt beim Warten in allen fünf Zellen, auf den festen Instanzen in vier davon nachweisbar (vierte Spalte; bei 6 je Stunde mit K = 3 gleichauf). Bei K = 3 steigt ihr Gewinn beim Warten ab 6 je Stunde mit der Rate von +28 (6 je Stunde) über +94 (9) auf +225 (12). Der Fachkanon, Schwellen schlügen „alles annehmen“ erst bei knapper Kapazität, wird in dieser Reihe nicht bestätigt: auch bei dünnem Strom (3 je Stunde, 92,0 % angenommen) nützt die Schwelle schon unter Sofort, vermutlich weil ein angenommener Auftrag unter Sofort im Mittel 63,8 Strecke kostet bei Erlös 60. Annahmen je Zelle:

| Zelle | Annahmen alles angenommen: Sofort / Spätestens | Annahmen mit Schwelle: Sofort / Spätestens |
|---|---|---|
| 3 Aufträge je Stunde, 3 Fahrzeuge | 92,0 % / 89,5 % | 27,1 % / 38,4 % |
| 6 Aufträge je Stunde, 3 Fahrzeuge | 70,5 % / 68,0 % | 27,3 % / 43,5 % |
| 6 Aufträge je Stunde, 2 Fahrzeuge | 52,3 % / 49,5 % | 29,6 % / 38,7 % |
| 9 Aufträge je Stunde, 3 Fahrzeuge | 55,9 % / 54,5 % | 28,9 % / 44,5 % |
| 12 Aufträge je Stunde, 3 Fahrzeuge | 47,4 % / 45,1 % | 31,6 % / 42,8 % |

**4. Die Wartezeit im Einzelnen** (6 je Stunde, 3 Fahrzeuge, feste Instanzen):

| Politik (Wartezeit tau) | Annahmen | Strecke je Auftrag | Gewinn je Tag | gegen Sofort | Routen | Last je Route |
|---|---|---|---|---|---|---|
| Sofort (0) | 70,5 % | 49,3 | 384 | – | 16,2 | 4,33 |
| Warten 10 (10) | 70,3 % | 47,8 | 433 | +48 ± 20 (37/0/23) | 15,2 | 4,59 |
| Warten 20 (20) | 70,5 % | 47,0 | 462 | +77 ± 17 (44/0/16) | 14,3 | 4,89 |
| Warten 40 (40) | 69,4 % | 45,8 | 495 | +111 ± 18 (47/0/13) | 13,5 | 5,05 |
| Spätestens (∞) | 68,0 % | 44,1 | 543 | +158 ± 21 (50/0/10) | 12,2 | 5,48 |

**5. Das Rückgrat trägt.** Der Wartestapel ist eine Riesentour; Split mit Fristen und späteste Abfahrten sind Stück 8, Einfügen an der Stelle mit dem kleinsten Split ist Stück 13. Neu ist die Zeit: wann eine Route startet, ist eine Entscheidung auf dem Plan, nicht im Plan.

**Linienbeispiel** (Depot bei 0, Auftrag 1 bei x = 10 mit Eingang 0 und Frist 60, Auftrag 2 bei x = 20 mit Eingang 15, ein Fahrzeug): Sofort fährt 2 Routen mit Strecke 60, Spätestens 1 Route mit Strecke 40 und Abfahrt 30 (Gewinn 60 gegen 80). Mit Frist 35 für Auftrag 2 lehnt Sofort den Auftrag ab (das Fahrzeug ist noch unterwegs), Spätestens nimmt beide an (Abfahrt 15; Gewinn 40 gegen 80).

## Ehrliche Grenzen

- **Deterministisches Modell:** Fahrzeit gleich Strecke, keine Verspätungen, keine unsicheren Fahrzeiten. Ohne Unsicherheit kostet „Spätestens“ kein Risiko; mit Verspätungsrisiko würde der Vorteil des Wartens schrumpfen (nicht gemessen). Das ist die größte Grenze.
- **Ein Depot, eine kleine Flotte:** K = 1 bis 4 Fahrzeuge der Kapazität 8, Aufträge mit Last 1 bis 3, Ort gleichverteilt im 100 × 100 Gebiet, Eingänge als Poisson-Strom in [0, 480] Minuten, Lieferfrist gleich Eingang plus 120, Erlös 60 je angenommenem Auftrag. Die Rangfolge hängt an Rate und Flotte; die fünf Zellen der Bänder zeigen das, tragen aber keine allgemeine Aussage.
- **Annahmetest hinreichend, nicht notwendig:** Ein Auftrag wird nur angenommen, wenn die Zuteilung der Routen nach Wunschstart zulässig ist; das kann zulässige Mengen ablehnen. Die Annahmen sind eine untere Schranke jeder Politik.
- **Schwelle auf der Planungsdifferenz:** Die Zusatzstrecke ist die des aktuellen Plans (Riesentour mit Split), nicht die des endgültigen; das erklärt einen Teil des Befunds, dass die Schwelle bei „Sofort“ schadet.
- **Kein Hindsight-Orakel:** Die Politiken werden nur untereinander verglichen; die Lücke zum Optimum ist unbekannt. Differenzen stehen mit Standardfehlern (Stichprobenstreuung durch Wurzel n über 60 Instanzen); „gleichauf“ heißt innerhalb von zwei Standardfehlern.
- **Feste und frische Instanzen:** Die Zellen und Politiken sind vor der Messung festgelegt (feste Seeds 0 bis 59); 60 frische Seeds (ab 200000) prüfen dieselben Aussagen. Auf den frischen Instanzen fällt der Vorteil des Wartens bei 12 Aufträgen je Stunde nicht auf null.
- **Keine Rechenzeiten:** Die Zeit im Modell ist Modellzeit; keine Rechenzeit wird gemessen oder in Tests geprüft.
- **Nicht gebaut:** mehrere Depots, Neuzuteilung unterwegs, Wartestrategien entlang der Route, Szenarioplanung, Lernverfahren, Hindsight-Orakel, Erlös- und Fristregler.

## Befunde und Korrekturen gegenüber dem Plan

- **Abfahrt im Linienbeispiel:** Der Plan nannte die Route (1 2) mit Abfahrt 50. Beide Reihenfolgen haben die Länge 40; der Split nimmt die Einfügestelle ganz vorn und fährt die Route (2 1) mit Abfahrt 30 (späteste Abfahrt min(75 − 20, 60 − 30)). Gleiche Strecke und gleicher Gewinn, nur die Abfahrt liegt früher.
- **Zweites Linienbeispiel:** Der Plan sah ein Beispiel mit „eigener Route“ vor; die Rechnung ergab, dass beide Aufträge auch mit Frist 50 gemeinsam planbar sind. Das Beispiel mit **Ablehnung** (Frist 35, ein Fahrzeug) zeigt die Annahme besser: Sofort lehnt ab, Spätestens nimmt beide an.
- **Standardfehler:** Die Phase 0 rechnete mit der Populationsstreuung, die Demo mit der Stichprobenstreuung (n − 1); die Mittel sind gleich, die Fehler um einen Bruchteil größer (Schwelle bei Sofort, dünnste Zelle: ± 16 statt ± 15).
- **Frische Instanzen ändern ein Ergebnis:** Der Plan formulierte „der Gewinn des Wartens fällt mit der Rate (235 → 7)“; auf 60 frischen Instanzen liegt er bei 12 je Stunde bei +111 ± 26. Die Aussage ist deshalb auf „schrumpft“ abgeschwächt, nicht „verschwindet“.
- **Ereignisreihenfolge und Zuteilung:** Die Zuteilung sortiert die Routen nach (Wunschstart, späteste Abfahrt) unabhängig von der Uhr (die erste Fassung brach mit einer nicht mehr planbaren Zuteilung ab). Das Ergebnis der Phase 0 (alle Mittel) wurde aus dem neuen Code bitgleich reproduziert.
- **Auslastungs-Hook:** Der Fachkanon (Bent und Van Hentenryck) sagt, der Gewinn wachse mit der Dynamik; hier fällt er mit der Rate (Flotte begrenzt). Das ist ein anderes Modell und keine Widerlegung.

## Verifikation

- **Handwerte:** das Linienbeispiel (Sofort 60 gegen Spätestens 40, Abfahrt 30; Ablehnung bei Frist 35), Split mit Fristen und späteste Abfahrten von Hand, die Schwelle von Hand (`tests/test_model.py`).
- **Orakel:** auf Kleinstinstanzen (fünf Aufträge, ein und zwei Fahrzeuge, fünf Politiken, 12 Seeds) ein unabhängiger Rechenweg über alle Zerlegungen, Reihenfolgen, Fahrzeugzuordnungen und Abfahrtszeiten: jede angenommene Menge ist planbar; jede ausgeführte Fahrt hält jede Frist, die Kapazität und die Eingangszeit, kein Fahrzeug ist doppelt belegt, Strecke und Gewinn werden neu gerechnet (`tests/test_model.py`).
- **Eigenschaften:** Spätestens startet jede Route genau bei ihrer spätesten Abfahrt; mit unendlicher Flotte werden alle Aufträge angenommen; gleicher Seed, gleicher Lauf; die Schwelle senkt die Annahmen im Mittel (je Instanz gilt das nicht immer).
- **Randfälle:** keine Aufträge, ein Auftrag, Frist gleich Entfernung, Kapazität gleich Last, gleichzeitige Eingänge, ein Fahrzeug im dichten Strom.
- **Verdikte:** jede Verzweigung und jede Zahl im Text (`tests/test_verdicts.py`).
- **Zahlen der README und der Preset-Hilfen:** `tests/test_claims.py` rechnet sie unabhängig aus den Bändern nach; die Bänder gegen eine frische Rechnung von Stichproben (`tests/test_bands.py`). Keine Rechenzeiten.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), alle Wartezeiten und beide Annahmeregeln, Experimente, PDF (`tests/test_app.py`, `tests/test_experiments.py`), Footer, Layout, Laufzeit-Importe.

## Tests

91 Tests. Laufzeit lokal etwa zwei Minuten.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Zwischenstände der Rechnung |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `generate_precomputed.py` | erzeugt `wof_bands.json` (600 Instanzzeilen, acht Politiken, parallel) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `wof_bands.json` | vorberechnete Bänder (fünf Zellen, feste und frische Instanzen, keine Zeiten) |
| `wof_constants.py` | Modell, Politiken, Zellen, Regler-Grenzen, Presets, Annahmentext |
| `wof_evaluation.py` | Bänder, gepaarte Differenzen, Live-Tag, Formate, Verdikt-Logik |
| `wof_layout.py` | Fester Kopf und Tabellenregel (Stylesheet) |
| `wof_model.py` | Generator, Split mit Fristen, Zuteilung, Annahme, Simulation |
| `wof_pdf_export.py` | PDF-Export des Tages |
| `wof_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `wof_visualization.py` | Plotly-Abbildungen (Zeitstrahl, Wartestapel, Karte; Achsen gesperrt) |
| `tests/` | Linienbeispiel, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Bänder, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Unsichere Fahrzeiten und Verspätungsrisiko:** die größte Grenze; mit Risiko würde „Spätestens“ eine Reserve brauchen.
- **Hindsight-Orakel:** die Lücke zum Optimum bleibt unbekannt.
- **Neuzuteilung unterwegs, Wartestrategien entlang der Route, mehrere Depots, Szenarioplanung, Lernverfahren.**
- **Regler für Frist und Erlös:** fest 120 und 60.
- **Annahmeregeln mit Schattenpreis und Rollout:** gemessen in der Messreihe Same-Day (Nahverkehr), dort nachlesen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
