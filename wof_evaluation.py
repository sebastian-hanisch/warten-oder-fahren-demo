"""Formate, Bänder, Live-Tag und Verdikte. Verdikte sind reine Funktionen (Art, Text): die App ruft st.<Art>(Text), die Tests prüfen jede Zahl im Text."""

import json
import math
import statistics as st
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import wof_constants as C
import wof_model as M


@dataclass(frozen=True)
class Settings:
    rate: int = C.DEFAULT_RATE          # Aufträge je Stunde
    K: int = C.DEFAULT_K
    seed: int = C.DEFAULT_SEED
    tau: int = C.DEFAULT_TAU            # Index in C.TAUS
    thr: int = C.DEFAULT_THR            # 0 ohne, 1 mit Annahmeschwelle

    @property
    def tau_value(self) -> float:
        return C.TAUS[self.tau]

    @property
    def threshold(self):
        return C.THRESHOLD if self.thr else None


# ----------------------------------------------------------------------------------------------------------------------------------- Formate

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    return f"{de(x, digits)} %"


def signed(x: float, digits: int = 0) -> str:
    """Mit Vorzeichen (echtes Minus); -0 wird zu 0."""
    text = de(abs(x), digits)
    if float(text.replace(",", ".")) == 0.0:
        return text
    return f"{'+' if x > 0 else '−'}{text}"


def tau_text(tau: float) -> str:
    return "∞" if tau == C.INF else str(int(tau))


def policy_name(key: str) -> str:
    return C.POLICIES[key][0]


def instances_word(k: int) -> str:
    return f"{k} Instanz" if k == 1 else f"{k} Instanzen"


def cell_text(cell) -> str:
    rate, K = cell
    return f"{rate} Aufträge je Stunde, {K} Fahrzeuge"


def cell_phrase(cell) -> str:
    """Dativ für Sätze: „6 Aufträgen je Stunde und 3 Fahrzeugen“."""
    rate, K = cell
    return f"{rate} Aufträgen je Stunde und {K} {'Fahrzeug' if K == 1 else 'Fahrzeugen'}"


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

@lru_cache(maxsize=1)
def load_bands() -> dict:
    path = Path(__file__).with_name(C.BAND_FILE)
    if not path.exists():
        return {"meta": {}, "rows": []}
    return json.loads(path.read_text(encoding="utf-8"))


def band_rows(cell, which: str = "fest") -> list[dict]:
    return [r for r in load_bands()["rows"] if r["set"] == which and (r["rate"], r["K"]) == tuple(cell)]


def profit(row: dict, key: str) -> float:
    return C.REVENUE * row["res"][key][0] - row["res"][key][1]


def policy_stats(rows: list[dict]) -> dict:
    """Je Politik die Mittel über die Instanzen: Annahmen in %, Strecke, Strecke je angenommenem Auftrag, Gewinn, Routen, Last je Route."""
    out = {}
    for key in C.POLICIES:
        out[key] = {
            "accepted": 100 * st.mean(r["res"][key][0] / r["n"] for r in rows),
            "dist": st.mean(r["res"][key][1] for r in rows),
            "per_order": st.mean(r["res"][key][1] / max(1, r["res"][key][0]) for r in rows),
            "profit": st.mean(profit(r, key) for r in rows),
            "routes": st.mean(r["res"][key][2] for r in rows),
            "load": st.mean(r["res"][key][3] for r in rows),
        }
    out["n"] = st.mean(r["n"] for r in rows)
    out["count"] = len(rows)
    return out


def paired(rows: list[dict], a: str, b: str) -> dict:
    """Gewinn von a minus Gewinn von b je Instanz: Mittel, Standardfehler (Stichprobenstreuung / Wurzel n), besser / gleich / schlechter."""
    d = [profit(r, a) - profit(r, b) for r in rows]
    se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
    return {"mean": st.mean(d), "se": se, "better": sum(1 for x in d if x > 1e-9), "equal": sum(1 for x in d if abs(x) <= 1e-9), "worse": sum(1 for x in d if x < -1e-9), "count": len(d)}


def pair_text(p: dict) -> str:
    return f"{signed(p['mean'])} ± {de(p['se'], 0)} ({p['better']}/{p['equal']}/{p['worse']})"


def level(p: dict) -> str:
    """„besser“, „schlechter“ oder „gleichauf“ (Differenz innerhalb von zwei Standardfehlern)."""
    if abs(p["mean"]) <= C.LEVEL_SE * p["se"]:
        return "gleichauf"
    return "besser" if p["mean"] > 0 else "schlechter"


# ----------------------------------------------------------------------------------------------------------------------------------- Live-Tag

@dataclass(frozen=True, eq=False)
class Day:
    inst: M.Instance
    results: dict            # Politik-Schlüssel -> Ergebnis (simulate); die gewählte Politik mit Spur
    chosen: str              # Schlüssel der gewählten Politik in results


def chosen_key(s: Settings) -> str:
    base = C.TAU_KEYS[s.tau]
    return base + "S" if s.thr and base + "S" in C.POLICIES else base


def run_day(s: Settings) -> Day:
    """Ein Tag mit der gewählten Politik (mit Spur) und, zum Vergleich, allen Politiken der Bänder (ohne Spur)."""
    inst = M.make_instance(s.seed, s.rate)
    chosen = chosen_key(s)
    results = {}
    for key, (name, tau, thr) in C.POLICIES.items():
        results[key] = M.simulate(inst, s.K, tau, thr)
    results["_chosen"] = M.simulate(inst, s.K, s.tau_value, s.threshold, trace=True)
    return Day(inst, results, chosen)


# ----------------------------------------------------------------------------------------------------------------------------------- Linienbeispiel

def hand_example(d2: float = 75.0) -> dict:
    """Linienbeispiel mit einem Fahrzeug: Sofort gegen Spätestens."""
    inst = M.line_example(d2)
    return {"inst": inst, "Sofort": M.simulate(inst, 1, 0.0, trace=True), "Spätestens": M.simulate(inst, 1, C.INF, trace=True)}


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_hand(ex: dict, d2: float) -> tuple[str, str]:
    a, b = ex["Sofort"], ex["Spätestens"]
    if a["accepted"] == b["accepted"]:
        text = (f"Sofort fährt {a['routes']} Routen mit Strecke {de(a['dist'], 0)}, Spätestens {b['routes']} Route mit Strecke {de(b['dist'], 0)}; beide nehmen beide Aufträge an. "
                f"Spätestens startet bei {de(b['dispatches'][0][0], 0)} (späteste Abfahrt) statt bei {de(a['dispatches'][0][0], 0)} und spart {de(a['dist'] - b['dist'], 0)} Strecke: Gewinn {de(a['profit'], 0)} gegen {de(b['profit'], 0)}.")
        return "success", text
    text = (f"Sofort nimmt nur {a['accepted']} von {a['n']} Aufträgen an (Auftrag 2 mit Frist {de(d2, 0)}: das Fahrzeug ist von der ersten Fahrt noch belegt), Spätestens nimmt alle {b['accepted']} an, weil das Fahrzeug noch im Depot steht "
            f"und beide Aufträge in einer Route fahren (Abfahrt {de(b['dispatches'][0][0], 0)}). Gewinn {de(a['profit'], 0)} gegen {de(b['profit'], 0)}.")
    return "success", text


def verdict_day(day: Day, s: Settings) -> tuple[str, str]:
    r = day.results["_chosen"]
    sofort, spaet = day.results["W0"], day.results["Winf"]
    name = policy_name(day.chosen)
    text = (f"Von {r['n']} Aufträgen nimmt {name} {r['accepted']} an und fährt {r['routes']} Routen mit Strecke {de(r['dist'], 0)}: Gewinn {de(r['profit'], 0)} (Last je Route {de(r['load'])}). "
            f"Sofort (ohne Schwelle): {de(sofort['profit'], 0)}, Spätestens (ohne Schwelle): {de(spaet['profit'], 0)}. Das ist ein einzelner Tag; die Zahlen über 60 Tage stehen in den Experimenten 3 bis 5.")
    best = max(r["profit"], sofort["profit"], spaet["profit"])
    return ("success" if r["profit"] >= best - 1e-9 else "info"), text


def verdict_wait(cell, which: str = "fest") -> tuple[str, str]:
    rows = band_rows(cell, which)
    p = paired(rows, "Winf", "W0")
    stats = policy_stats(rows)
    kind = "success" if level(p) == "besser" else ("warning" if level(p) == "schlechter" else "info")
    text = (f"Bei {cell_phrase(cell)} ist Spätestens gegenüber Sofort {level(p)}: Gewinn {pair_text(p)} je Tag über {instances_word(p['count'])}. Routen je Tag {de(stats['W0']['routes'], 1)} gegen {de(stats['Winf']['routes'], 1)}, "
            f"Last je Route {de(stats['W0']['load'])} gegen {de(stats['Winf']['load'])}, Annahmen {pct(stats['W0']['accepted'])} gegen {pct(stats['Winf']['accepted'])}.")
    return kind, text


def verdict_threshold(cell, which: str = "fest") -> tuple[str, str]:
    rows = band_rows(cell, which)
    a, b = paired(rows, "W0S", "W0"), paired(rows, "WinfS", "Winf")
    text = (f"Bei {cell_phrase(cell)}: die Annahmeschwelle gegen „alles annehmen“ ist bei Sofort {level(a)} ({pair_text(a)}), beim Warten (Spätestens) {level(b)} ({pair_text(b)}). "
            f"Die Zusatzstrecke hängt an der Abfahrtspolitik: unter Sofort fährt fast jeder Auftrag allein.")
    kind = "success" if level(b) == "besser" and level(a) != "besser" else "info"
    return kind, text


def verdict_grid(which: str = "fest") -> tuple[str, str]:
    gains = {cell: paired(band_rows(cell, which), "Winf", "W0") for cell in C.CELLS}
    wins = [c for c, p in gains.items() if level(p) == "besser"]
    ties = [c for c, p in gains.items() if level(p) == "gleichauf"]
    text = (f"Spätestens ist gegenüber Sofort in {len(wins)} von {len(C.CELLS)} Zellen besser, in {len(ties)} gleichauf; der Gewinn fällt von {signed(gains[C.CELLS[0]]['mean'])} bei {cell_phrase(C.CELLS[0])} "
            f"auf {signed(gains[C.CELLS[-1]]['mean'])} bei {cell_phrase(C.CELLS[-1])}. Deterministische Fahrzeiten, ein Erlös, Frist 120, kein Hindsight-Orakel.")
    return "info", text
