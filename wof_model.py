"""Modell und Simulation (Stück 14 der Linie Tourenbildung): Aufträge treffen über den Tag ein, jeder mit Lieferfrist; K Fahrzeuge fahren vom Depot.

Ein Plan ist eine Riesentour (Folge der noch nicht gestarteten angenommenen Aufträge), die der Split mit Fristen in Routen zerlegt (Stück 8: Vorwärtsprüfung der spätesten Abfahrt l, Abbruch beim ersten Verstoß).
Eine Route fährt zum Zeitpunkt s los (s <= l), ihr Fahrzeug ist danach bis zur Rückkehr (Rundreise) belegt. Politik W_tau: Wunschstart einer Route = min(l, Eingang ihres ältesten Auftrags + tau); tau = 0 ist „Sofort“,
tau = unendlich „Spätestens“. Annehmen: ein neuer Auftrag wird nur angenommen, wenn es einen Plan gibt, der alle noch nicht gestarteten angenommenen Aufträge samt ihm rechtzeitig bedient (neuer Auftrag an der Stelle der
Riesentour mit dem kleinsten Split; Routen den Fahrzeugen nach (Wunschstart, l) zugeteilt, Fahrzeug mit der frühesten Rückkehr). Optional eine Schwelle: nur annehmen, wenn die Zusatzstrecke des neuen Plans höchstens thr ist."""

import math
import random
import statistics as st
from dataclasses import dataclass

import wof_constants as C

INF = math.inf


@dataclass(frozen=True, eq=False)
class Instance:
    orders: tuple          # je Auftrag ein Wörterbuch: id (ab 1), t (Eingang), x, y, q (Last), d (Frist)
    D: tuple               # Entfernungsmatrix (Index 0 = Depot, i = Auftrag i)
    depot: tuple


def make_instance(seed: int, rate_per_hour: float, delta: float = C.DELTA, horizon: float = C.HORIZON) -> Instance:
    """Poisson-Strom mit Rate rate_per_hour / 60 je Minute in [0, horizon]; Ort gleichverteilt im 100 x 100 Gebiet, Last 1 bis 3, Frist = Eingang + delta; Depot in der Mitte."""
    lam = rate_per_hour / 60.0
    rnd = random.Random(seed)
    t, orders = 0.0, []
    while True:
        t += rnd.expovariate(lam)
        if t > horizon:
            break
        orders.append({"id": len(orders) + 1, "t": t, "x": rnd.uniform(0, 100), "y": rnd.uniform(0, 100), "q": rnd.randint(1, 3), "d": t + delta})
    return from_orders(orders, C.DEPOT)


def from_orders(orders, depot) -> Instance:
    pts = [tuple(depot)] + [(o["x"], o["y"]) for o in orders]
    D = tuple(tuple(math.dist(a, b) for b in pts) for a in pts)
    return Instance(tuple(dict(o) for o in orders), D, tuple(depot))


def line_example(d2: float = 75.0) -> Instance:
    """Linienbeispiel (Handrechnung): Depot bei 0, Auftrag 1 bei x = 10 (Eingang 0, Frist 60), Auftrag 2 bei x = 20 (Eingang 15, Frist d2), Last je 1."""
    orders = [{"id": 1, "t": 0.0, "x": 10.0, "y": 0.0, "q": 1, "d": 60.0}, {"id": 2, "t": 15.0, "x": 20.0, "y": 0.0, "q": 1, "d": float(d2)}]
    return from_orders(orders, (0.0, 0.0))


def split_deadlines(inst: Instance, seq, now: float, cap: int = C.CAPACITY):
    """Split mit Fristen: ein Block (i..j) ist zulässig, wenn die Last <= cap und die späteste Abfahrt l >= jetzt (l = Minimum über die Stopps von Frist - Fahrstrecke bis zum Stopp); die Zulässigkeit ist monoton in j (Abbruch).
    Rückgabe (Kosten, [(Kunden, l, Dauer)]) oder (INF, None). Gleichstand: der kleinste Startknoten des letzten Bogens gewinnt."""
    orders, D = inst.orders, inst.D
    n = len(seq)
    best, pred = [INF] * (n + 1), [0] * (n + 1)
    best[0] = 0.0
    for i in range(n):
        if best[i] == INF:
            continue
        load, off, l, prev = 0, 0.0, INF, 0
        for j in range(i, n):
            o = orders[seq[j] - 1]
            load += o["q"]
            if load > cap:
                break
            off += D[prev][seq[j]]
            prev = seq[j]
            l = min(l, o["d"] - off)
            if l < now - 1e-9:
                break
            cost = off + D[prev][0]
            if best[i] + cost < best[j + 1] - 1e-12:
                best[j + 1], pred[j + 1] = best[i] + cost, i
    if best[n] == INF:
        return INF, None
    routes, node = [], n
    while node > 0:
        i = pred[node]
        blk = tuple(seq[i:node])
        off, prev, l = 0.0, 0, INF
        for c in blk:
            off += D[prev][c]
            prev = c
            l = min(l, orders[c - 1]["d"] - off)
        routes.append((blk, l, off + D[prev][0]))
        node = i
    routes.reverse()
    return best[n], routes


def assign(inst: Instance, routes, now: float, free, tau: float):
    """Routen den Fahrzeugen zuteilen, so wie die Politik sie losschickt: Wunschstart w = min(l, Eingang des ältesten Auftrags + tau), Reihenfolge nach (w, l) (unabhängig von `jetzt`),
    Fahrzeug mit der frühesten Rückkehr, Start = max(jetzt, w, Rückkehr). Rückgabe [(Route, Fahrzeug, Start)] oder None, wenn eine Route ihre späteste Abfahrt verpasst."""
    orders = inst.orders
    f = list(free)
    wish = []
    for r in routes:
        oldest = min(orders[c - 1]["t"] for c in r[0])
        wish.append((min(r[1], oldest + tau), r[1], r))
    out = []
    for w, l, r in sorted(wish, key=lambda x: (x[0], x[1])):
        v = min(range(len(f)), key=lambda k: f[k])
        start = max(now, w, f[v])
        if start > l + 1e-9:
            return None
        f[v] = start + r[2]
        out.append((r, v, start))
    return out


def best_insert(inst: Instance, seq, new: int, now: float, free, tau: float, old_cost: float = 0.0, thr=None, cap: int = C.CAPACITY):
    """Neuen Auftrag an die Stelle der Riesentour mit dem kleinsten zulässigen Split setzen; None, wenn keine Stelle zulässig ist (oder die Zusatzstrecke über thr liegt)."""
    best = None
    for pos in range(len(seq) + 1):
        cand = list(seq[:pos]) + [new] + list(seq[pos:])
        cost, routes = split_deadlines(inst, cand, now, cap)
        if routes is None or assign(inst, routes, now, free, tau) is None:
            continue
        if thr is not None and cost - old_cost > thr + 1e-9:
            continue
        if best is None or cost < best[0] - 1e-12:
            best = (cost, cand, routes)
    return best


def simulate(inst: Instance, K: int, tau: float, thr=None, cap: int = C.CAPACITY, trace: bool = False) -> dict:
    """Ein Tag mit der Politik W_tau (und optional der Annahmeschwelle thr). Rückgabe: accepted, n, dist, routes, load (mittlere Last je Route), profit; mit trace=True zusätzlich dispatches
    [(Start, Fahrzeug, Kunden, Dauer, l)], decisions [(Eingang, Auftrag, angenommen)], stack [(Zeit, Zahl der Wartenden)]."""
    orders = inst.orders
    free = [0.0] * K
    plan, dist, accepted, now = [], 0.0, 0, 0.0
    loads, dispatches, decisions, stack = [], [], [], []

    def advance(until):
        nonlocal plan, dist, now
        while plan:
            asg = assign(inst, plan, now, free, tau)
            assert asg is not None, "Plan nicht mehr zulässig"
            r, v, start = min(asg, key=lambda a: (a[2], a[0][1]))
            if start > until:
                return
            now = max(now, start)
            free[v] = now + r[2]
            dist += r[2]
            loads.append(sum(orders[c - 1]["q"] for c in r[0]))
            dispatches.append((now, v, r[0], r[2], r[1]))
            plan = [p for p in plan if p is not r]
            if trace:
                stack.append((now, sum(len(p[0]) for p in plan)))

    for o in orders:
        advance(o["t"])
        now = max(now, o["t"])
        seq = [c for r in plan for c in r[0]]
        b = best_insert(inst, seq, o["id"], now, free, tau, sum(r[2] for r in plan), thr, cap)
        decisions.append((o["t"], o["id"], b is not None))
        if b is not None:
            plan = b[2]
            accepted += 1
        if trace:
            stack.append((now, sum(len(p[0]) for p in plan)))
    advance(INF)
    out = {"accepted": accepted, "n": len(orders), "dist": dist, "routes": len(dispatches), "load": st.mean(loads) if loads else 0.0, "profit": C.REVENUE * accepted - dist}
    if trace:
        out.update({"dispatches": dispatches, "decisions": decisions, "stack": stack})
    return out
