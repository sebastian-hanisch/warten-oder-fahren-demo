"""Die Bänder: Aufbau, Vollständigkeit, Stichproben gegen eine frische Rechnung mit dem Modell dieser Demo (keine Zeiten: die Zeit im Modell ist Modellzeit)."""

import math

import pytest

import wof_constants as C
import wof_evaluation as E
import wof_model as M

B = E.load_bands()


def test_counts_and_cells():
    assert len(B["rows"]) == 600
    for cell in C.CELLS:
        for which in C.BAND_SETS:
            rows = E.band_rows(cell, which)
            assert [r["seed"] for r in rows] == list(C.BAND_SEEDS[which])
    assert {(r["rate"], r["K"]) for r in B["rows"]} == set(C.CELLS)


def test_every_row_has_every_policy_with_plausible_values():
    for r in B["rows"]:
        assert set(r["res"]) == set(C.POLICIES)
        for key, (acc, dist, routes, load) in r["res"].items():
            assert 0 <= acc <= r["n"] and dist >= 0 and routes >= (1 if acc else 0) and 0 <= load <= C.CAPACITY and (acc == 0) == (dist == 0)


def test_the_seed_sets_do_not_overlap():
    fest = {r["seed"] for r in B["rows"] if r["set"] == "fest"}
    fresh = {r["seed"] for r in B["rows"] if r["set"] == "frisch"}
    assert not fest & fresh and max(fest) < 100 and min(fresh) >= 200000


def test_the_number_of_orders_depends_on_seed_and_rate_only():
    for r in B["rows"]:
        assert r["n"] == len(M.make_instance(r["seed"], r["rate"]).orders)


@pytest.mark.parametrize("cell,which,idx", [((6, 3), "fest", 0), ((3, 3), "fest", 7), ((12, 3), "frisch", 3), ((6, 2), "fest", 41), ((9, 3), "frisch", 59)])
def test_a_sample_of_rows_is_reproduced_exactly(cell, which, idx):
    row = E.band_rows(cell, which)[idx]
    inst = M.make_instance(row["seed"], row["rate"])
    for key, (name, tau, thr) in C.POLICIES.items():
        r = M.simulate(inst, row["K"], tau, thr)
        assert [r["accepted"], r["routes"]] == [row["res"][key][0], row["res"][key][2]]
        assert r["dist"] == pytest.approx(row["res"][key][1], abs=1e-9) and r["load"] == pytest.approx(row["res"][key][3], abs=1e-9)


def test_no_timings_are_stored():
    assert all(set(r) == {"set", "rate", "K", "seed", "n", "res"} for r in B["rows"]) and "time" not in str(B["meta"]).lower().replace("modellzeit", "")


def test_the_standard_error_and_the_pair_counts_are_consistent():
    rows = E.band_rows((6, 3))
    p = E.paired(rows, "Winf", "W0")
    d = [E.profit(r, "Winf") - E.profit(r, "W0") for r in rows]
    mean = sum(d) / len(d)
    sd = math.sqrt(sum((x - mean) ** 2 for x in d) / (len(d) - 1))
    assert p["mean"] == pytest.approx(mean) and p["se"] == pytest.approx(sd / math.sqrt(len(d))) and p["better"] + p["equal"] + p["worse"] == 60
