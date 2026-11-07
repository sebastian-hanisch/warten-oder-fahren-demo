"""Erzeugt wof_bands.json: die Bänder der Warte- und Annahmepolitiken (Stück 14 der Linie Tourenbildung).

Je Zelle (Rate je Stunde, Fahrzeuge: (3, 3), (6, 3), (6, 2), (9, 3), (12, 3)) und je Menge (fest: Seeds 0 bis 59; frisch: Seeds 200000 bis 200059) und je Instanz laufen die acht Politiken
(Sofort, Warten 10, 20, 40, Spätestens, dazu Sofort, Warten 20 und Spätestens mit Annahmeschwelle); die Simulation ist deterministisch, ein Lauf je Politik und Instanz. Gespeichert werden je Politik
(angenommen, Strecke, Routen, mittlere Last je Route). Es gibt keine Rechenzeiten: die Zeit im Modell ist Modellzeit.

Aufruf:  python generate_precomputed.py            (rechnet alles parallel und schreibt wof_bands.json)"""

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import wof_constants as C
import wof_model as M

TARGET = Path(__file__).with_name(C.BAND_FILE)


def job(args):
    cell, which = args
    rate, K = cell
    rows = []
    for seed in C.BAND_SEEDS[which]:
        inst = M.make_instance(seed, rate)
        res = {}
        for key, (name, tau, thr) in C.POLICIES.items():
            r = M.simulate(inst, K, tau, thr)
            res[key] = [r["accepted"], r["dist"], r["routes"], r["load"]]
        rows.append({"set": which, "rate": rate, "K": K, "seed": seed, "n": len(inst.orders), "res": res})
    print("fertig", cell, which, flush=True)
    return rows


def main():
    jobs = [(cell, which) for cell in C.CELLS for which in C.BAND_SETS]
    with ProcessPoolExecutor(max_workers=10) as pool:
        out = [row for rows in pool.map(job, jobs) for row in rows]
    meta = {"cells": [list(c) for c in C.CELLS], "policies": {k: [v[0], None if v[1] == C.INF else v[1], v[2]] for k, v in C.POLICIES.items()},
            "seeds": {"fest": [0, 59], "frisch": [200000, 200059]}, "delta": C.DELTA, "capacity": C.CAPACITY, "revenue": C.REVENUE, "horizon": C.HORIZON,
            "source": "Generator und Simulation: wof_model.py; ein Lauf je Politik und Instanz (deterministisch)"}
    TARGET.write_text(json.dumps({"meta": meta, "rows": out}, ensure_ascii=False), encoding="utf-8")
    print("geschrieben:", TARGET.name, len(out), "Instanzzeilen")


if __name__ == "__main__":
    main()
