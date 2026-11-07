"""Verdikte sind reine Funktionen: jede Zahl im Text stammt aus der Rechnung, Art und Wortlaut folgen den Schwellen."""

import pytest

import wof_constants as C
import wof_evaluation as ev


def test_formats():
    assert ev.de(3.14159) == "3,14" and ev.pct(12.345) == "12,3 %" and ev.signed(-0.4) == "0" and ev.signed(235.2) == "+235" and ev.signed(-103.4) == "−103"
    assert ev.tau_text(0.0) == "0" and ev.tau_text(C.INF) == "∞" and ev.instances_word(1) == "1 Instanz" and ev.instances_word(60) == "60 Instanzen"
    assert ev.cell_text((3, 3)) == "3 Aufträge je Stunde, 3 Fahrzeuge" and ev.cell_phrase((6, 2)) == "6 Aufträgen je Stunde und 2 Fahrzeugen" and ev.cell_phrase((6, 1)) == "6 Aufträgen je Stunde und 1 Fahrzeug"


def test_level_thresholds():
    assert ev.level({"mean": 10.0, "se": 4.0}) == "besser" and ev.level({"mean": 7.0, "se": 4.0}) == "gleichauf" and ev.level({"mean": -9.0, "se": 4.0}) == "schlechter"
    assert ev.level({"mean": -8.0, "se": 4.0}) == "gleichauf"                                                    # genau zwei Standardfehler: gleichauf


def test_hand_verdict_both_cases():
    for d2 in (75.0, 35.0):
        ex = ev.hand_example(d2)
        kind, text = ev.verdict_hand(ex, d2)
        a, b = ex["Sofort"], ex["Spätestens"]
        assert kind == "success" and ev.de(a["profit"], 0) in text and ev.de(b["profit"], 0) in text
        if d2 == 75.0:
            assert "Sofort fährt 2 Routen mit Strecke 60, Spätestens 1 Route mit Strecke 40" in text and "startet bei 30" in text and "spart 20 Strecke" in text
        else:
            assert "Sofort nimmt nur 1 von 2 Aufträgen an" in text and "Spätestens nimmt alle 2 an" in text and "Abfahrt 15" in text


def test_day_verdict():
    s = ev.Settings()
    day = ev.run_day(s)
    kind, text = ev.verdict_day(day, s)
    r = day.results["_chosen"]
    assert f"Von {r['n']} Aufträgen nimmt Spätestens {r['accepted']} an und fährt {r['routes']} Routen" in text and ev.de(r["profit"], 0) in text and kind in ("success", "info")
    assert ev.de(day.results["W0"]["profit"], 0) in text and ev.de(day.results["Winf"]["profit"], 0) in text


def test_run_day_chosen_matches_the_policy_of_the_settings():
    s = ev.Settings(rate=9, K=3, seed=2, tau=2, thr=1)
    day = ev.run_day(s)
    assert day.chosen == "W20S" and day.results["_chosen"]["profit"] == pytest.approx(day.results["W20S"]["profit"]) and day.results["_chosen"]["accepted"] == day.results["W20S"]["accepted"]
    s2 = ev.Settings(rate=9, K=3, seed=2, tau=1, thr=1)                                                        # Warten 10 + Schwelle gibt es in den Bändern nicht: die Spur rechnet es trotzdem
    d2 = ev.run_day(s2)
    assert d2.chosen == "W10" and d2.results["_chosen"]["accepted"] <= d2.results["W10"]["accepted"]


def test_wait_verdict_per_cell():
    for cell in C.CELLS:
        kind, text = ev.verdict_wait(cell)
        p = ev.paired(ev.band_rows(cell), "Winf", "W0")
        assert f"Bei {ev.cell_phrase(cell)} ist Spätestens gegenüber Sofort {ev.level(p)}" in text and ev.pair_text(p) in text and kind == {"besser": "success", "schlechter": "warning", "gleichauf": "info"}[ev.level(p)]
    assert ev.verdict_wait((12, 3))[0] == "info" and ev.verdict_wait((3, 3))[0] == "success"


def test_threshold_verdict():
    kind, text = ev.verdict_threshold((12, 3))
    a, b = ev.paired(ev.band_rows((12, 3)), "W0S", "W0"), ev.paired(ev.band_rows((12, 3)), "WinfS", "Winf")
    assert f"bei Sofort {ev.level(a)} ({ev.pair_text(a)}), beim Warten (Spätestens) {ev.level(b)} ({ev.pair_text(b)})" in text and kind == "success"
    assert ev.verdict_threshold((3, 3))[0] == "info"                                                           # in der dünnsten Zelle nützt die Schwelle auch bei Sofort


def test_grid_verdict_counts_and_range():
    kind, text = ev.verdict_grid("fest")
    gains = {c: ev.paired(ev.band_rows(c), "Winf", "W0") for c in C.CELLS}
    wins = sum(1 for p in gains.values() if ev.level(p) == "besser")
    ties = sum(1 for p in gains.values() if ev.level(p) == "gleichauf")
    assert f"in {wins} von 5 Zellen besser, in {ties} gleichauf" in text and ev.signed(gains[(3, 3)]["mean"]) in text and ev.signed(gains[(12, 3)]["mean"]) in text and kind == "info"
    assert (wins, ties) == (3, 2)


def test_fresh_instances_change_the_picture_at_the_highest_rate():
    fest, frisch = ev.paired(ev.band_rows((12, 3), "fest"), "Winf", "W0"), ev.paired(ev.band_rows((12, 3), "frisch"), "Winf", "W0")
    assert ev.level(fest) == "gleichauf" and ev.level(frisch) == "besser"
