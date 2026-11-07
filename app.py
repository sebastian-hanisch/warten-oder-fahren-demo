"""Warten oder Fahren, Annehmen oder Ablehnen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 14 (Abschluss der Linie) der Reihe „Tourenbildung“: Aufträge treffen über den Tag ein, jeder mit Lieferfrist, wenige Fahrzeuge fahren vom Depot. Wann startet eine geplante Route (sofort, nach tau Minuten
oder spätestens), und nimmt man jeden Auftrag an oder nur, wenn die Zusatzstrecke den Erlös nicht übersteigt? Die Demo zeigt ein Linienbeispiel von Hand, einen Tag mit Zeitstrahl und Karte, den Gewinn des Wartens und
der Annahmeschwelle über 60 Instanzen je Zelle und wo es kippt. Deterministische Fahrzeiten, ein Lauf je Politik.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import wof_constants as C
from wof_evaluation import (
    Settings,
    band_rows,
    cell_text,
    de,
    hand_example,
    instances_word,
    level,
    paired,
    pair_text,
    pct,
    policy_name,
    policy_stats,
    run_day,
    signed,
    tau_text,
    verdict_day,
    verdict_grid,
    verdict_hand,
    verdict_threshold,
    verdict_wait,
)
from wof_layout import dunkles_design, kopf_css
from wof_pdf_export import build_pdf
from wof_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from wof_visualization import build_map, build_stack, build_tau_lines, build_timeline

st.set_page_config(page_title="Warten oder Fahren – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _day(settings):
    return run_day(settings)


@st.cache_data(show_spinner=False)
def _hand(d2):
    return hand_example(d2)


@st.cache_data(show_spinner=False)
def _stats(cell, which):
    return policy_stats(band_rows(cell, which))


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in wof_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("⏱️ Warten oder Fahren")
st.markdown(
    """
**Soll eine Route sofort losfahren oder warten?** Aufträge treffen über den Tag ein, jeder mit **Lieferfrist**; wenige Fahrzeuge fahren vom Depot. Wartet man, sammeln sich Aufträge und die Routen werden voller, aber das Fahrzeug fehlt
für spätere Aufträge. Dazu die zweite Entscheidung: **annehmen oder ablehnen**, wenn die Zusatzstrecke den Erlös übersteigt. Die Wartenden bilden eine **Riesentour**; der **Split mit Fristen** (Stück 8) zerlegt sie in Routen und
liefert die späteste Abfahrt, der neue Auftrag kommt an die Stelle mit dem kleinsten Split (Stück 13).

Weiter unten: **🔬 Eine Frist von Hand**, **🔬 Ein Tag**, **🔬 Warten gegen Sofort**, **🔬 Die Annahmeschwelle**, **🔬 Wo es kippt**, **🚧 Wo die Annahmen enden**, der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und der
Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So arbeitet die Politik", expanded=True):
    st.markdown(
        """
1. **Späteste Abfahrt:** Eine Route muss jeden Kunden bis zu seiner Frist erreichen; die späteste Abfahrt ist das Minimum über die Stopps von (Frist minus Fahrstrecke bis zum Stopp). Danach ist das Fahrzeug bis zur Rückkehr belegt.
2. **Wartezeit tau:** Eine geplante Route startet zum Zeitpunkt min(späteste Abfahrt, Eingang ihres ältesten Auftrags + tau), frühestens bei freiem Fahrzeug. **tau = 0 ist „Sofort“, tau = ∞ ist „Spätestens“.**
3. **Annehmen:** Ein neuer Auftrag wird nur angenommen, wenn es einen Plan gibt, der alle noch nicht gestarteten angenommenen Aufträge samt ihm rechtzeitig bedient; sonst abgelehnt. **Schwelle:** zusätzlich nur, wenn die Zusatzstrecke höchstens 60 (der Erlös) ist.
4. **Gewinn:** 60 je angenommenem Auftrag minus gefahrene Strecke. Alles ist deterministisch; Differenzen stehen mit Standardfehlern über 60 Instanzen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    rate = st.slider("Aufträge je Stunde", *bounds("rate_slider"), key="rate_slider", help="Rate des Poisson-Stroms; rund Rate mal 8 Aufträge am Tag (480 Minuten). Die Bänder rechnen 3, 6, 9 und 12 je Stunde.")
    K = st.slider("Fahrzeuge", *bounds("k_slider"), key="k_slider", help="Fahrzeuge der Kapazität 8 im Depot. Die Bänder rechnen 3 Fahrzeuge (bei 6 je Stunde auch 2).")
    tau = st.select_slider("Wartezeit tau (Minuten)", list(range(len(C.TAUS))), key="tau_select", format_func=lambda i: {0: "0 (Sofort)", 4: "∞ (Spätestens)"}.get(i, tau_text(C.TAUS[i])),
                           help="Wunschstart einer Route = min(späteste Abfahrt, Eingang des ältesten Auftrags + tau).")
    thr = st.radio("Annahme", [0, 1], key="thr_select", format_func=lambda i: "alles annehmen, was planbar ist" if i == 0 else "nur mit Schwelle (Zusatzstrecke ≤ 60)", horizontal=False,
                   help="Mit Schwelle: ein Auftrag wird abgelehnt, wenn die Zusatzstrecke des neuen Plans über dem Erlös von 60 liegt.")
    seed = st.number_input("Zufalls-Seed des Tages", *bounds("seed_input"), key="seed_input", step=1, help="Der Seed legt die Eingänge, Orte, Lasten und Fristen des Tages fest.")
    st.button("🎲 Neuen Tag generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"rate_slider": int(rate), "k_slider": int(K), "seed_input": int(seed), "tau_select": int(tau), "thr_select": int(thr)})

settings = Settings(int(rate), int(K), int(seed), int(tau), int(thr))
day = _day(settings)
res = day.results["_chosen"]
inst = day.inst
sofort, spaet = day.results["W0"], day.results["Winf"]

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: ein Tag")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Aufträge am Tag", f"{res['n']}")
m2.metric(f"{policy_name(day.chosen)}: Gewinn", signed(res["profit"]), delta=f"{signed(res['profit'] - sofort['profit'])} gegen Sofort", delta_color="normal")
m3.metric("Angenommen", f"{res['accepted']} von {res['n']}")
m4.metric("Routen · Strecke", f"{res['routes']} · {de(res['dist'], 0)}")
st.caption(f"{settings.rate} Aufträge je Stunde, {settings.K} Fahrzeuge, Lieferfrist {de(C.DELTA, 0)}, Erlös {de(C.REVENUE, 0)} je Auftrag. Vergleich (ohne Schwelle): Sofort {signed(sofort['profit'])}, Spätestens {signed(spaet['profit'])}.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, day), file_name="warten-oder-fahren.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Warten oder Fahren, und was ändert die Annahmeschwelle?")
kind, text = verdict_grid("fest")
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Eine Frist von Hand")
st.caption("Zwei Kunden auf einer Geraden, ein Fahrzeug: Auftrag 1 bei x = 10 (Eingang 0, Frist 60), Auftrag 2 bei x = 20 (Eingang 15). Sofort fährt jeden Auftrag einzeln, Spätestens wartet bis zur spätesten Abfahrt und nimmt beide mit. "
           "Mit Frist 35 für Auftrag 2 ist das Fahrzeug unter Sofort noch von der ersten Fahrt belegt: Sofort lehnt Auftrag 2 ab.")
d2 = float(st.radio("Frist von Auftrag 2", [75, 35], key="hand_d2", horizontal=True, format_func=lambda v: f"{v} (Standard)" if v == 75 else f"{v} (knapp)"))
hand = _hand(d2)
h1, h2 = st.columns(2)
for col, name in ((h1, "Sofort"), (h2, "Spätestens")):
    with col:
        r = hand[name]
        st.markdown(f"**{name}:** angenommen {r['accepted']} von {r['n']}, Strecke {de(r['dist'], 0)}, Gewinn {signed(r['profit'])}")
        st.plotly_chart(build_timeline(r, 1, hand["inst"].orders), width="stretch", key=f"timeline_hand_{name}")
kind, text = verdict_hand(hand, d2)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Ein Tag")
st.caption("Der Tag der Seitenleiste mit der gewählten Politik: der Zeitstrahl zeigt je Fahrzeug die Fahrten (Balken von der Abfahrt bis zur Rückkehr, Strich = späteste Abfahrt) und die Eingänge (grün angenommen, rot abgelehnt); darunter die Wartenden über die Zeit "
           "und die Karte der gefahrenen Routen.")
st.plotly_chart(build_timeline(res, settings.K, inst.orders), width="stretch", key="timeline_day")
d1, d2c = st.columns(2)
with d1:
    st.markdown("**Wartende Aufträge über die Zeit**")
    st.plotly_chart(build_stack(res["stack"]), width="stretch", key="stack_day")
with d2c:
    st.markdown("**Karte der gefahrenen Routen**")
    st.plotly_chart(build_map(inst, res, legend=False), width="stretch", key="map_day")
tab = ["| Politik | Angenommen | Strecke | Gewinn | Routen | Last je Route |", "|---|---|---|---|---|---|"]
for key in C.POLICIES:
    r = day.results[key]
    mark = "**" if key == day.chosen else ""
    tab.append(f"| {mark}{policy_name(key)}{mark} | {r['accepted']} von {r['n']} | {de(r['dist'], 0)} | {signed(r['profit'])} | {r['routes']} | {de(r['load'])} |")
st.markdown("\n".join(tab))
kind, text = verdict_day(day, settings)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Warten gegen Sofort")
st.caption("Feste Instanzen, vorberechnet (generate_precomputed.py): 60 Tage je Zelle (Rate und Flotte), ein Lauf je Politik. Verglichen wird der Gewinn je Tag gepaart (gleiche Aufträge); ± Standardfehler, in Klammern: Instanzen mit besserem / gleichem / schlechterem Gewinn.")
which = st.radio("Instanzen", list(C.BAND_SETS), horizontal=True, key="band_set", format_func=lambda k: {"fest": "fest (Seeds 0 bis 59)", "frisch": "frisch (Seeds ab 200000)"}[k])
cell = st.selectbox("Zelle", list(range(len(C.CELLS))), key="band_cell", format_func=lambda i: cell_text(C.CELLS[i]), index=1)
cell_t = C.CELLS[cell]
stats = _stats(cell_t, which)
rows = band_rows(cell_t, which)
tab = ["| Politik | Annahmen | Strecke je Auftrag | Gewinn je Tag | gegen Sofort | Routen | Last je Route |", "|---|---|---|---|---|---|---|"]
for key in C.TAU_KEYS:
    p = paired(rows, key, "W0") if key != "W0" else None
    tab.append(f"| {policy_name(key)} (tau = {tau_text(C.POLICIES[key][1])}) | {pct(stats[key]['accepted'])} | {de(stats[key]['per_order'], 1)} | {de(stats[key]['profit'], 0)} | {pair_text(p) if p else '–'} | {de(stats[key]['routes'], 1)} | {de(stats[key]['load'])} |")
st.markdown("\n".join(tab))
st.caption(f"{instances_word(stats['count'])}, im Mittel {de(stats['n'], 0)} Aufträge je Tag. Gewinn = 60 · Annahmen − Strecke.")
st.plotly_chart(build_tau_lines({c: _stats(c, which) for c in C.CELLS}, C.CELLS), width="stretch", key="tau_lines")
kind, text = verdict_wait(cell_t, which)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Die Annahmeschwelle")
st.caption("Schwelle (Zusatzstrecke des neuen Plans höchstens 60) gegen „alles annehmen“, jeweils mit Sofort, mit Warten 20 und mit Spätestens; gepaart über 60 Tage je Zelle. Die Wechselwirkung steht in der letzten Spalte.")
tab = ["| Zelle | Schwelle bei Sofort | bei Warten 20 | bei Spätestens | Spätestens + Schwelle gegen Sofort + Schwelle |", "|---|---|---|---|---|"]
for c_ in C.CELLS:
    r_ = band_rows(c_, which)
    tab.append(f"| {cell_text(c_)} | {pair_text(paired(r_, 'W0S', 'W0'))} | {pair_text(paired(r_, 'W20S', 'W20'))} | {pair_text(paired(r_, 'WinfS', 'Winf'))} | {pair_text(paired(r_, 'WinfS', 'W0S'))} |")
st.markdown("\n".join(tab))
kind, text = verdict_threshold(cell_t, which)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wo es kippt")
st.caption("Gewinn von Spätestens gegen Sofort (ohne Schwelle) und der Annahmeschwelle gegen „alles annehmen“ (mit Spätestens) je Zelle, feste und frische Instanzen nebeneinander. Standardfehler in der Tabelle; „gleichauf“ = innerhalb von zwei Standardfehlern.")
tab = ["| Zelle | Spätestens − Sofort, fest | gleichauf? | Spätestens − Sofort, frisch | gleichauf? | Schwelle beim Warten, fest | Schwelle beim Warten, frisch |", "|---|---|---|---|---|---|---|"]
for c_ in C.CELLS:
    a, b = paired(band_rows(c_, "fest"), "Winf", "W0"), paired(band_rows(c_, "frisch"), "Winf", "W0")
    ta, tb = paired(band_rows(c_, "fest"), "WinfS", "Winf"), paired(band_rows(c_, "frisch"), "WinfS", "Winf")
    tab.append(f"| {cell_text(c_)} | {pair_text(a)} | {level(a)} | {pair_text(b)} | {level(b)} | {pair_text(ta)} | {pair_text(tb)} |")
st.markdown("\n".join(tab))
st.info("Der Vorteil des Wartens fällt auf den festen Instanzen mit der Rate (bei 12 Aufträgen je Stunde gleichauf), auf den frischen bleibt er dort bei rund +111: die Aussage „Warten bringt bei dichtem Strom nichts“ ist nicht robust.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Deterministische Fahrzeiten** | Mit Verspätungsrisiko kostet „Spätestens“ eine Reserve; der Vorteil des Wartens schrumpft (nicht gemessen) | Robuste Planung, Szenarioplanung |
| **Eine kleine Flotte, ein Erlös, eine Frist** | Die Rangfolge hängt an Rate und Flottengröße; fünf Zellen tragen keine allgemeine Aussage | Mehr Zellen, Regler für Frist und Erlös |
| **Annahmetest hinreichend** | Zulässige Mengen können abgelehnt werden; die Annahmen sind eine untere Schranke | exakte Zulässigkeitsprüfung |
| **Schwelle auf dem aktuellen Plan** | Die Zusatzstrecke ist die des jetzigen Plans, nicht des endgültigen | Rollout, Schattenpreise (Messreihe Same-Day) |
| **Kein Hindsight-Orakel** | Die Lücke zum Optimum ist unbekannt, nur die Politiken stehen gegeneinander | Hindsight-Heuristik mit Eingangszeiten |
| **Keine Neuzuteilung unterwegs** | Fahrzeuge im Einsatz werden nicht umgeleitet | Dynamische VRP-Literatur |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Depot $0$, Aufträge $i$ mit Eingang $t_i$, Ort, Last $q_i$ und Frist $d_i = t_i + 120$, Fahrzeit gleich Strecke $c_{ij}$, $K$ Fahrzeuge der Kapazität $Q = 8$.

**Späteste Abfahrt.** Eine Route $(i_1, \dots, i_m)$ mit Fahrstrecke $o_k = c_{0 i_1} + \dots + c_{i_{k-1} i_k}$ bis zum Stopp $k$ ist zulässig bei Abfahrt $s$, wenn $s + o_k \le d_{i_k}$ für alle $k$, also $s \le \ell = \min_k (d_{i_k} - o_k)$.
Der Split (Stück 8) wählt auf der Riesentour die Zerlegung mit der kürzesten Strecke, deren Blöcke $\ell \ge$ jetzt und Last $\le Q$ erfüllen (die Zulässigkeit ist monoton in der Blockgröße).

**Politik $W_\tau$.** Wunschstart $w_r = \min(\ell_r, t_{\text{älteste}}(r) + \tau)$; Routen werden in der Reihenfolge $(w_r, \ell_r)$ dem Fahrzeug mit der frühesten Rückkehr zugeteilt, Start $= \max(\text{jetzt}, w_r, \text{Rückkehr})$, zulässig nur, wenn Start $\le \ell_r$.

**Annehmen.** Der neue Auftrag wird an jeder Stelle der Riesentour probiert (Split mit Fristen, Zuteilung); gewählt wird die zulässige Stelle mit der kleinsten Strecke; mit Schwelle nur, wenn (neue Strecke − alte Strecke) $\le 60$.

**Gewinn.** $60 \cdot (\text{angenommen}) - \text{gefahrene Strecke}$; Differenzen zweier Politiken gepaart je Instanz, Standardfehler = Stichprobenstreuung geteilt durch $\sqrt{60}$.

**Literatur.** Zeitfenster und Wartestrategien: Mitrović-Minić und Laporte (2004), dynamische VRP-Übersicht: Pillac u. a. (2013), Riesentour und Split: Prins (2004). Nur als Titel oder Abstract gesehen; die Demo übernimmt keine Zahl daraus.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
