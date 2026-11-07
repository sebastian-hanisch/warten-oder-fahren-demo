"""Die fünf Experimente der App per AppTest: Frist von Hand, Tag, Warten gegen Sofort, Annahmeschwelle, Wo es kippt; dazu das PDF."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import wof_constants as C
import wof_evaluation as ev
from wof_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
SETTING_KEYS = {"rate": "rate_slider", "K": "k_slider", "seed": "seed_input", "tau": "tau_select", "thr": "thr_select"}


def _app(preset=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    if preset:
        at.session_state["permalink_loaded"] = True
        for key, state_key in SETTING_KEYS.items():
            at.session_state[state_key] = C.PRESETS[preset][key]
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join([x.value for x in at.success] + [x.value for x in at.info] + [x.value for x in at.warning] + [x.value for x in at.error])


def test_the_default_shows_a_day_with_the_chosen_policy():
    at = _app()
    text = _texts(at)
    assert "nimmt Spätestens" in text and "Sofort fährt 2 Routen mit Strecke 60" in text and "in 3 von 5 Zellen besser" in text


def test_the_hand_example_both_deadlines():
    at = _app()
    at.radio(key="hand_d2").set_value(35).run()
    assert not at.exception and "Sofort nimmt nur 1 von 2 Aufträgen an" in _texts(at)
    at.radio(key="hand_d2").set_value(75).run()
    assert not at.exception and "spart 20 Strecke" in _texts(at)


def test_every_waiting_time_and_both_acceptance_rules_run():
    at = _app()
    for tau in range(len(C.TAUS)):
        for thr in (0, 1):
            at.select_slider(key="tau_select").set_value(tau).run()
            at.radio(key="thr_select").set_value(thr).run()
            assert not at.exception, (tau, thr)
            assert any(c.label == "Aufträge am Tag" for c in at.metric)


def test_the_extreme_settings_run():
    at = _app()
    for rate, K in ((C.RATE_MIN, C.K_MIN), (C.RATE_MAX, C.K_MIN), (C.RATE_MAX, C.K_MAX), (C.RATE_MIN, C.K_MAX)):
        at.slider(key="rate_slider").set_value(rate).run()
        at.slider(key="k_slider").set_value(K).run()
        assert not at.exception, (rate, K)


def test_the_band_selection_for_every_cell_and_set():
    at = _app()
    for which in C.BAND_SETS:
        at.radio(key="band_set").set_value(which).run()
        for i, cell in enumerate(C.CELLS):
            at.selectbox(key="band_cell").set_value(i).run()
            assert not at.exception, (which, cell)
            assert f"Bei {ev.cell_phrase(cell)} ist Spätestens gegenüber Sofort" in _texts(at)


def test_the_threshold_table_and_the_tipping_table_are_shown():
    text = " ".join(m.value for m in _app().markdown)
    assert "Schwelle bei Sofort" in text and "Spätestens − Sofort, fest" in text and ev.pair_text(ev.paired(ev.band_rows((12, 3), "frisch"), "Winf", "W0")) in text


def test_pdf_download_button_exists_and_the_pdf_is_built_for_every_preset():
    assert len(_app().get("download_button")) == 1
    for preset in C.PRESETS.values():
        s = ev.Settings(preset["rate"], preset["K"], preset["seed"], preset["tau"], preset["thr"])
        data = build_pdf(s, ev.run_day(s))
        assert data[:5] == b"%PDF-" and len(data) > 1500
