"""Jede Zahl der README und der Preset-Hilfen wird aus den Bändern nachgerechnet und muss im Text stehen (DEMO-PLAYBOOK §1b); der Rechenweg ist unabhängig von wof_evaluation (eigene Mittel und Standardfehler)."""

import math
import statistics as st
from pathlib import Path

import wof_constants as C
import wof_evaluation as E
import wof_model as M

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
B = E.load_bands()["rows"]


def rows(cell, which="fest"):
    return [r for r in B if r["set"] == which and (r["rate"], r["K"]) == cell]


def d(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def sg(x):
    t = d(abs(x), 0)
    return t if t == "0" else ("+" if x > 0 else "−") + t


def prof(r, k):
    return 60 * r["res"][k][0] - r["res"][k][1]


def diff(rs, a, b):
    v = [prof(r, a) - prof(r, b) for r in rs]
    se = st.stdev(v) / math.sqrt(len(v))
    return f"{sg(st.mean(v))} ± {d(se, 0)} ({sum(1 for x in v if x > 1e-9)}/{sum(1 for x in v if abs(x) <= 1e-9)}/{sum(1 for x in v if x < -1e-9)})", st.mean(v), se, sum(1 for x in v if x > 1e-9)


def mean(rs, f):
    return st.mean(f(r) for r in rs)


def test_the_two_cell_tables():
    for which, label in (("fest", "Feste"), ("frisch", "Frische")):
        assert f"{label} Instanzen (60 je Zelle):" in README
        for cell in C.CELLS:
            rs = rows(cell, which)
            n = mean(rs, lambda r: r["n"])
            line = (f"| {cell[0]} je Stunde, K = {cell[1]} (im Mittel {d(n, 0)} Aufträge) | {sg(mean(rs, lambda r: prof(r, 'W0')))} | {diff(rs, 'Winf', 'W0')[0]} | "
                    f"{diff(rs, 'W0S', 'W0')[0]} | {diff(rs, 'WinfS', 'Winf')[0]} |")
            assert line in README, line
    assert len(rows((6, 3))) == 60


def test_the_waiting_time_table():
    rs = rows((6, 3))
    names = {"W0": "Sofort (0)", "W10": "Warten 10 (10)", "W20": "Warten 20 (20)", "W40": "Warten 40 (40)", "Winf": "Spätestens (∞)"}
    for k, name in names.items():
        acc = 100 * mean(rs, lambda r: r["res"][k][0] / r["n"])
        per = mean(rs, lambda r: r["res"][k][1] / max(1, r["res"][k][0]))
        line = f"| {name} | {d(acc)} % | {d(per)} | {d(mean(rs, lambda r: prof(r, k)), 0)} | {diff(rs, k, 'W0')[0] if k != 'W0' else '–'} | {d(mean(rs, lambda r: r['res'][k][2]))} | {d(mean(rs, lambda r: r['res'][k][3]), 2)} |"
        assert line in README, line


def test_the_acceptance_table():
    for cell in C.CELLS:
        rs = rows(cell)
        acc = {k: d(100 * mean(rs, lambda r: r["res"][k][0] / r["n"])) + " %" for k in ("W0", "Winf", "W0S", "WinfS")}
        line = f"| {E.cell_text(cell)} | {acc['W0']} / {acc['Winf']} | {acc['W0S']} / {acc['WinfS']} |"
        assert line in README, line


def test_the_collecting_numbers_of_finding_1():
    rs = rows((3, 3))
    r0, ri = mean(rs, lambda r: r["res"]["W0"][2]), mean(rs, lambda r: r["res"]["Winf"][2])
    l0, li = mean(rs, lambda r: r["res"]["W0"][3]), mean(rs, lambda r: r["res"]["Winf"][3])
    p0, pi = mean(rs, lambda r: r["res"]["W0"][1] / r["res"]["W0"][0]), mean(rs, lambda r: r["res"]["Winf"][1] / r["res"]["Winf"][0])
    a0, ai = 100 * mean(rs, lambda r: r["res"]["W0"][0] / r["n"]), 100 * mean(rs, lambda r: r["res"]["Winf"][0] / r["n"])
    text = (f"fährt Spätestens {d(ri)} statt {d(r0)} Routen je Tag mit {d(li, 2)} statt {d(l0, 2)} Last je Route; die Strecke je angenommenem Auftrag sinkt von {d(p0)} auf {d(pi)}. "
            f"Der Preis sind weniger Annahmen ({d(ai)} % gegen {d(a0)} %). Warten 20 Minuten liegt dazwischen ({diff(rs, 'W20', 'W0')[0]} gegen Sofort)")
    assert text in README, text


def test_finding_2_fresh_instances_at_twelve_per_hour():
    fest, frisch = diff(rows((12, 3)), "Winf", "W0"), diff(rows((12, 3), "frisch"), "Winf", "W0")
    assert abs(fest[1]) <= 2 * fest[2] and frisch[1] > 2 * frisch[2]                                      # fest gleichauf, frisch besser
    assert f"auf {sg(fest[1])} ± {d(fest[2], 0)} (12 je Stunde, gleichauf)" in README and f"bei {frisch[0]} (besser)" in README
    assert f"({diff(rows((6, 2)), 'Winf', 'W0')[0]} fest, {diff(rows((6, 2), 'frisch'), 'Winf', 'W0')[0]} frisch)" in README
    up = [sg(diff(rows(c), "WinfS", "Winf")[1]) for c in ((6, 3), (9, 3), (12, 3))]
    assert f"von {up[0]} (6 je Stunde) über {up[1]} (9) auf {up[2]} (12)" in README


def test_the_hand_example_numbers():
    for d2, sofort, spaet in ((75.0, (2, 60.0, 60.0), (2, 40.0, 80.0)), (35.0, (1, 20.0, 40.0), (2, 40.0, 80.0))):
        inst = M.line_example(d2)
        a, b = M.simulate(inst, 1, 0.0), M.simulate(inst, 1, float("inf"), trace=True)
        assert (a["accepted"], round(a["dist"], 6), round(a["profit"], 6)) == sofort and (b["accepted"], round(b["dist"], 6), round(b["profit"], 6)) == spaet
    text = ("Sofort fährt 2 Routen mit Strecke 60, Spätestens 1 Route mit Strecke 40 und Abfahrt 30 (Gewinn 60 gegen 80). Mit Frist 35 für Auftrag 2 lehnt Sofort den Auftrag ab (das Fahrzeug ist noch unterwegs), "
            "Spätestens nimmt beide an (Abfahrt 15; Gewinn 40 gegen 80).")
    assert text in README


def test_the_plan_correction_numbers():
    fresh = diff(rows((12, 3), "frisch"), "Winf", "W0")
    assert f"bei 12 je Stunde bei {sg(fresh[1])} ± {d(fresh[2], 0)}" in README
    assert "Schwelle bei Sofort, dünnste Zelle: ± 16 statt ± 15" in README and d(diff(rows((3, 3)), "W0S", "W0")[2], 0) == "16"


# --- Presets -----------------------------------------------------------------------------------------------------------------------------

def test_default_preset():
    h = C.PRESET_HELP["Spätestens statt Sofort (6 je Stunde, 3 Fahrzeuge)"]
    t, m, se, better = diff(rows((6, 3)), "Winf", "W0")
    worse = sum(1 for r in rows((6, 3)) if prof(r, "Winf") - prof(r, "W0") < -1e-9)
    for text in (f"{sg(m)} ± {d(se, 0)} Gewinn je Tag", f"in {better} von 60 Instanzen besser", f"in {worse} schlechter", "Seed 0", "rund 50 Aufträgen"):
        assert text in h, text
    assert round(mean(rows((6, 3)), lambda r: r["n"])) == 50


def test_thin_stream_preset():
    h = C.PRESET_HELP["Dünner Strom: Warten sammelt (3 je Stunde)"]
    rs = rows((3, 3))
    r0, ri = mean(rs, lambda r: r["res"]["W0"][2]), mean(rs, lambda r: r["res"]["Winf"][2])
    l0, li = mean(rs, lambda r: r["res"]["W0"][3]), mean(rs, lambda r: r["res"]["Winf"][3])
    t, m, se, better = diff(rs, "Winf", "W0")
    fr = diff(rows((3, 3), "frisch"), "Winf", "W0")
    a0, ai = 100 * mean(rs, lambda r: r["res"]["W0"][0] / r["n"]), 100 * mean(rs, lambda r: r["res"]["Winf"][0] / r["n"])
    for text in (f"{d(ri)} statt {d(r0)} Routen", f"{d(li, 2)} statt {d(l0, 2)} Last", f"{sg(m)} ± {d(se, 0)} gegen Sofort", f"in {better} von 60 Instanzen besser", f"(frische Instanzen {sg(fr[1])} ± {d(fr[2], 0)})", f"{d(ai)} gegen {d(a0)} %", "rund 25 am Tag"):
        assert text in h, text
    assert round(mean(rs, lambda r: r["n"])) == 25


def test_dense_stream_preset():
    h = C.PRESET_HELP["Dichter Strom: der Vorteil schrumpft (12 je Stunde)"]
    t, m, se, better = diff(rows((12, 3)), "Winf", "W0")
    fr = diff(rows((12, 3), "frisch"), "Winf", "W0")
    for text in (f"gleichauf ({sg(m)} ± {d(se, 0)}, {better} von 60 besser)", f"{sg(fr[1])} ± {d(fr[2], 0)}", "rund 98 am Tag"):
        assert text in h, text
    assert abs(m) <= 2 * se and round(mean(rows((12, 3)), lambda r: r["n"])) == 98


def test_threshold_hurts_preset():
    h = C.PRESET_HELP["Die Schwelle schadet bei Sofort (9 je Stunde)"]
    t, m, se, better = diff(rows((9, 3)), "W0S", "W0")
    for text in (f"{sg(m)} ± {d(se, 0)} Gewinn je Tag", f"nur {better} von 60 Instanzen besser", "höchstens 60"):
        assert text in h, text
    assert C.THRESHOLD == 60.0


def test_threshold_helps_preset():
    h = C.PRESET_HELP["Die Schwelle nützt beim Warten (12 je Stunde)"]
    t, m, se, better = diff(rows((12, 3)), "WinfS", "Winf")
    fr = diff(rows((12, 3), "frisch"), "WinfS", "Winf")
    for text in (f"{sg(m)} ± {d(se, 0)} Gewinn je Tag", f"in {better} von 60 Instanzen besser", f"(frische Instanzen {sg(fr[1])} ± {d(fr[2], 0)})"):
        assert text in h, text


def test_the_presets_pick_the_intended_policies():
    for name, key in (("Spätestens statt Sofort (6 je Stunde, 3 Fahrzeuge)", "Winf"), ("Die Schwelle schadet bei Sofort (9 je Stunde)", "W0S"), ("Die Schwelle nützt beim Warten (12 je Stunde)", "WinfS")):
        p = C.PRESETS[name]
        assert E.chosen_key(E.Settings(p["rate"], p["K"], p["seed"], p["tau"], p["thr"])) == key
