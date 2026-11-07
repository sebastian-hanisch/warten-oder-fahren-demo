"""Handwerte, Orakel und Eigenschaften des Modells (Stück 14): Split mit Fristen, Zuteilung, Annahme, Politiken W_tau."""

import itertools
import math
import random

import pytest

import wof_constants as C
import wof_model as M

INF = math.inf


# --- Handwerte -----------------------------------------------------------------------------------------------------------------------------

def test_split_with_deadlines_by_hand(line):
    cost, routes = M.split_deadlines(line, [1, 2], 15.0)
    # Route (1 2): 0 -> 10 -> 20 -> 0 = 10 + 10 + 20 = 40, späteste Abfahrt min(60 - 10, 75 - 20) = 50
    assert cost == pytest.approx(40.0) and routes == [((1, 2), pytest.approx(50.0), pytest.approx(40.0))]
    cost, routes = M.split_deadlines(line, [2, 1], 15.0)
    # Route (2 1): 0 -> 20 -> 10 -> 0 = 20 + 10 + 10 = 40, späteste Abfahrt min(75 - 20, 60 - 30) = 30
    assert cost == pytest.approx(40.0) and routes[0][1] == pytest.approx(30.0)


def test_line_example_sofort_against_spaetestens(line):
    a, b = M.simulate(line, 1, 0.0, trace=True), M.simulate(line, 1, INF, trace=True)
    assert (a["accepted"], a["dist"], a["routes"], a["profit"]) == (2, pytest.approx(60.0), 2, pytest.approx(60.0))
    assert [(s, c) for s, v, c, d, l in a["dispatches"]] == [(0.0, (1,)), (20.0, (2,))]            # zweite Fahrt erst, wenn das Fahrzeug zurück ist (Rückkehr bei 20)
    assert (b["accepted"], b["dist"], b["routes"], b["profit"]) == (2, pytest.approx(40.0), 1, pytest.approx(80.0))
    start, v, customers, dur, latest = b["dispatches"][0]
    assert customers in ((1, 2), (2, 1)) and start == pytest.approx(latest) and latest == pytest.approx(50.0 if customers == (1, 2) else 30.0)
    assert customers == (2, 1)                                                                      # Gleichstand der Länge: der Split nimmt die Einfügestelle ganz vorn, Abfahrt 30


def test_tight_deadline_sofort_rejects_spaetestens_accepts(line_tight):
    a, b = M.simulate(line_tight, 1, 0.0, trace=True), M.simulate(line_tight, 1, INF, trace=True)
    assert (a["accepted"], a["dist"], a["profit"]) == (1, pytest.approx(20.0), pytest.approx(40.0)) and a["decisions"] == [(0.0, 1, True), (15.0, 2, False)]
    assert (b["accepted"], b["dist"], b["profit"]) == (2, pytest.approx(40.0), pytest.approx(80.0))
    assert b["dispatches"][0][0] == pytest.approx(15.0) and b["dispatches"][0][2] == (2, 1)        # beide Aufträge in einer Route, Abfahrt bei der Frist von Auftrag 2 minus Weg


def test_a_second_vehicle_removes_the_rejection(line_tight):
    assert M.simulate(line_tight, 2, 0.0)["accepted"] == 2


def test_threshold_by_hand(line):
    # Spätestens: Auftrag 1 allein Strecke 20, Auftrag 2 zusätzlich 20 (gemeinsame Route 40): mit Schwelle 60 werden beide angenommen, mit Schwelle 10 schon Auftrag 1 nicht (Zusatz 20 > 10)
    assert M.simulate(line, 1, INF, thr=60.0)["accepted"] == 2
    r = M.simulate(line, 1, INF, thr=10.0, trace=True)
    assert r["decisions"] == [(0.0, 1, False), (15.0, 2, False)]


def test_deadline_equal_to_distance_is_accepted_when_the_vehicle_is_free():
    inst = M.from_orders([{"id": 1, "t": 5.0, "x": 30.0, "y": 0.0, "q": 1, "d": 35.0}], (0.0, 0.0))
    r = M.simulate(inst, 1, 0.0, trace=True)
    assert r["accepted"] == 1 and r["dispatches"][0][0] == pytest.approx(5.0) and r["dispatches"][0][4] == pytest.approx(5.0)


# --- Orakel: unabhängiger Rechenweg ----------------------------------------------------------------------------------------------------------

def _tiny(seed, n, delta_lo=25.0, delta_hi=90.0):
    rnd = random.Random(seed)
    orders = []
    for i in range(1, n + 1):
        t = rnd.uniform(0, 60)
        x, y = rnd.uniform(0, 40), rnd.uniform(0, 40)
        dist = math.hypot(x, y)
        orders.append({"id": i, "t": t, "x": x, "y": y, "q": rnd.randint(1, 3), "d": t + max(rnd.uniform(delta_lo, delta_hi), dist + 0.5)})
    orders.sort(key=lambda o: o["t"])
    for i, o in enumerate(orders, start=1):
        o["id"] = i
    return M.from_orders(orders, (0.0, 0.0))


def _route_window(inst, route):
    """(früheste Abfahrt, späteste Abfahrt, Dauer) einer Route in dieser Reihenfolge; die späteste aus den Ankunftszeiten einzeln gerechnet."""
    pts = [inst.depot] + [(inst.orders[c - 1]["x"], inst.orders[c - 1]["y"]) for c in route] + [inst.depot]
    legs = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    e = max(inst.orders[c - 1]["t"] for c in route)
    latest, off = math.inf, 0.0
    for k, c in enumerate(route):
        off += legs[k]
        latest = min(latest, inst.orders[c - 1]["d"] - off)
    return e, latest, sum(legs)


def _partitions(items):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for part in _partitions(rest):
        yield [[first]] + part
        for i in range(len(part)):
            yield part[:i] + [[first] + part[i]] + part[i + 1:]


def oracle_schedulable(inst, ids, K, cap=C.CAPACITY):
    """Gibt es einen Plan für die Aufträge ids (alle schon bekannt): Zerlegung in Routen, Reihenfolge je Route, Fahrzeuge, Abfahrten? Aufzählung (höchstens 5 Aufträge)."""
    for part in _partitions(list(ids)):
        if any(sum(inst.orders[c - 1]["q"] for c in blk) > cap for blk in part):
            continue
        options = []
        for blk in part:
            opts = []
            for perm in itertools.permutations(blk):
                e, l, dur = _route_window(inst, perm)
                if e <= l + 1e-9:
                    opts.append((e, l, dur))
            options.append(opts)
        if any(not o for o in options):
            continue
        for choice in itertools.product(*options):
            R = len(choice)
            for vehicles in itertools.product(range(K), repeat=R):
                ok = True
                for v in range(K):
                    mine = [choice[i] for i in range(R) if vehicles[i] == v]
                    best = False
                    for order in itertools.permutations(mine):
                        t_free, good = 0.0, True
                        for e, l, dur in order:
                            s = max(e, t_free)
                            if s > l + 1e-9:
                                good = False
                                break
                            t_free = s + dur
                        if good:
                            best = True
                            break
                    if not best:
                        ok = False
                        break
                if ok:
                    return True
    return False


POLICY_SET = [(0.0, None), (20.0, None), (INF, None), (0.0, 20.0), (INF, 20.0)]


def _check_execution(inst, r, K, accepted):
    """Neu gerechnet: jeder angenommene Auftrag genau einmal gefahren, nach seinem Eingang, vor seiner Frist, Kapazität, kein Fahrzeug doppelt belegt, Strecke und Gewinn."""
    served = sorted(c for _, _, cs, _, _ in r["dispatches"] for c in cs)
    assert served == sorted(accepted)
    total = 0.0
    busy = {}
    for start, v, cs, dur, latest in r["dispatches"]:
        e, l, d_ = _route_window(inst, cs)
        assert start >= e - 1e-9 and start <= l + 1e-9 and d_ == pytest.approx(dur) and latest == pytest.approx(l)
        assert sum(inst.orders[c - 1]["q"] for c in cs) <= C.CAPACITY
        busy.setdefault(v, []).append((start, start + dur))
        total += d_
    for spans in busy.values():
        spans.sort()
        assert all(b[0] >= a[1] - 1e-9 for a, b in zip(spans, spans[1:]))
    assert r["dist"] == pytest.approx(total) and r["profit"] == pytest.approx(C.REVENUE * len(accepted) - total) and r["accepted"] == len(accepted)


@pytest.mark.parametrize("K", (1, 2))
def test_every_policy_accepts_only_schedulable_sets_and_keeps_every_rule(K):
    for seed in range(12):
        inst = _tiny(seed, 5)
        for tau, thr in POLICY_SET:
            r = M.simulate(inst, K, tau, thr, trace=True)
            accepted = [oid for _, oid, ok in r["decisions"] if ok]
            assert oracle_schedulable(inst, accepted, K), (seed, tau, thr)
            _check_execution(inst, r, K, accepted)


def test_oracle_itself_on_two_cases(line, line_tight):
    assert oracle_schedulable(line, [1, 2], 1) and oracle_schedulable(line_tight, [1, 2], 1)       # beide planbar (gemeinsame Route)
    inst = M.from_orders([{"id": 1, "t": 0.0, "x": 10.0, "y": 0.0, "q": 1, "d": 10.0}, {"id": 2, "t": 0.0, "x": -10.0, "y": 0.0, "q": 1, "d": 10.0}], (0.0, 0.0))
    assert not oracle_schedulable(inst, [1, 2], 1) and oracle_schedulable(inst, [1, 2], 2)


def test_the_policy_can_reject_a_schedulable_set_that_the_oracle_would_take(line_tight):
    """Der Annahmetest ist hinreichend, nicht notwendig: unter Sofort wird Auftrag 2 abgelehnt, obwohl beide Aufträge zusammen planbar sind (das Fahrzeug ist schon unterwegs)."""
    r = M.simulate(line_tight, 1, 0.0, trace=True)
    assert [ok for _, _, ok in r["decisions"]] == [True, False] and oracle_schedulable(line_tight, [1, 2], 1)


# --- Eigenschaften -------------------------------------------------------------------------------------------------------------------------

def test_with_an_unlimited_fleet_every_order_is_accepted():
    for seed in range(5):
        inst = M.make_instance(seed, 12)
        for tau in (0.0, 20.0, INF):
            assert M.simulate(inst, len(inst.orders) + 1, tau)["accepted"] == len(inst.orders)


def test_spaetestens_departs_every_route_at_its_latest_departure_and_sofort_as_early_as_possible():
    for seed in range(8):
        inst = M.make_instance(seed, 9)
        r = M.simulate(inst, 3, INF, trace=True)
        assert all(start == pytest.approx(latest) for start, v, cs, dur, latest in r["dispatches"])
        s = M.simulate(inst, 3, 0.0, trace=True)
        for start, v, cs, dur, latest in s["dispatches"]:
            oldest = min(inst.orders[c - 1]["t"] for c in cs)
            assert oldest - 1e-9 <= start <= latest + 1e-9


def test_determinism_and_profit_identity():
    inst = M.make_instance(3, 6)
    a, b = M.simulate(inst, 3, 20.0, 60.0), M.simulate(inst, 3, 20.0, 60.0)
    assert a == b and a["profit"] == pytest.approx(C.REVENUE * a["accepted"] - a["dist"])


def test_instance_generator_is_deterministic_and_deadline_feasible_alone():
    a, b = M.make_instance(5, 6), M.make_instance(5, 6)
    assert a.orders == b.orders and a.D == b.D
    assert all(o["d"] - o["t"] == pytest.approx(C.DELTA) and o["q"] in (1, 2, 3) and o["t"] <= C.HORIZON and C.DELTA >= math.dist(a.depot, (o["x"], o["y"])) for o in a.orders)


def test_the_threshold_lowers_acceptance_on_average():
    """Ohne Schwelle nimmt eine Politik im Mittel mehr an als mit Schwelle (je Instanz gilt das nicht immer: eine abgelehnte Fahrt lässt dem Fahrzeug Platz)."""
    insts = [M.make_instance(s, 9) for s in range(20)]
    for tau in (0.0, INF):
        no = sum(M.simulate(i, 3, tau)["accepted"] for i in insts)
        yes = sum(M.simulate(i, 3, tau, C.THRESHOLD)["accepted"] for i in insts)
        assert no > yes


# --- Randfälle -----------------------------------------------------------------------------------------------------------------------------

def test_no_orders_no_trip():
    inst = M.from_orders([], C.DEPOT)
    r = M.simulate(inst, 3, INF, trace=True)
    assert (r["accepted"], r["n"], r["dist"], r["routes"], r["profit"]) == (0, 0, 0.0, 0, 0.0) and r["dispatches"] == []


def test_capacity_equal_to_load_forces_single_order_routes(line):
    r = M.simulate(line, 2, INF, cap=1, trace=True)
    assert r["accepted"] == 2 and all(len(cs) == 1 for _, _, cs, _, _ in r["dispatches"]) and r["dist"] == pytest.approx(60.0)
    assert M.simulate(line, 1, INF, cap=1)["accepted"] == 1                                                  # ein Fahrzeug: die zweite Einzelfahrt käme nach ihrer Frist zurück


def test_a_single_order_with_one_vehicle():
    inst = M.from_orders([{"id": 1, "t": 1.0, "x": 3.0, "y": 4.0, "q": 2, "d": 50.0}], (0.0, 0.0))
    for tau in (0.0, 10.0, INF):
        r = M.simulate(inst, 1, tau, trace=True)
        assert r["accepted"] == 1 and r["dist"] == pytest.approx(10.0)
    assert M.simulate(inst, 1, INF, trace=True)["dispatches"][0][0] == pytest.approx(45.0)               # späteste Abfahrt 50 - 5


def test_simultaneous_arrivals_can_share_a_route():
    orders = [{"id": 1, "t": 0.0, "x": 10.0, "y": 0.0, "q": 1, "d": 100.0}, {"id": 2, "t": 0.0, "x": 20.0, "y": 0.0, "q": 1, "d": 100.0}]
    r = M.simulate(M.from_orders(orders, (0.0, 0.0)), 1, INF, trace=True)
    assert r["routes"] == 1 and r["dist"] == pytest.approx(40.0)


def test_one_vehicle_and_dense_stream_still_keeps_all_deadlines():
    inst = M.make_instance(1, 15)
    r = M.simulate(inst, 1, 20.0, trace=True)
    accepted = [oid for _, oid, ok in r["decisions"] if ok]
    _check_execution(inst, r, 1, accepted)
