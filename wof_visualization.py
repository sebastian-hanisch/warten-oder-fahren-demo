"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import wof_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_timeline(res, K, orders=None, title_time="Zeit in Minuten"):
    """Zeitstrahl der Fahrzeuge: je Fahrzeug eine Zeile, jede Fahrt ein Balken von der Abfahrt bis zur Rückkehr (Beschriftung: Kunden); gestrichelte Linie: späteste Abfahrt der Route.
    Optional (orders): Eingänge als Rauten in der Zeile „Eingang“ (unten)."""
    fig = go.Figure()
    for i, (start, v, customers, dur, latest) in enumerate(res["dispatches"]):
        color = C.ROUTE_COLORS[i % len(C.ROUTE_COLORS)]
        fig.add_trace(go.Bar(x=[dur], base=[start], y=[f"Fahrzeug {v + 1}"], orientation="h", marker=dict(color=color, line=dict(color="#333", width=0.5)), text=[" ".join(str(c) for c in customers)],
                             textposition="inside", insidetextanchor="middle", showlegend=False, hovertemplate=f"Abfahrt %{{base:.0f}}, Dauer {dur:.0f}; späteste Abfahrt {latest:.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[latest], y=[f"Fahrzeug {v + 1}"], mode="markers", marker=dict(symbol="line-ns", size=12, color="#222", line=dict(width=2, color="#222")), showlegend=False,
                                 hovertemplate=f"späteste Abfahrt {latest:.0f}<extra></extra>"))
    if orders is not None:
        acc = {oid: ok for _, oid, ok in res["decisions"]}
        fig.add_trace(go.Scatter(x=[o["t"] for o in orders], y=["Eingang"] * len(orders), mode="markers+text", text=[str(o["id"]) for o in orders], textposition="top center",
                                 marker=dict(symbol="diamond", size=9, color=["#2F6B65" if acc.get(o["id"]) else "#c0504d" for o in orders]), showlegend=False,
                                 hovertemplate="Auftrag %{text} bei %{x:.0f}<extra></extra>"))
    rows = [f"Fahrzeug {k + 1}" for k in range(K)] + (["Eingang"] if orders is not None else [])
    fig.update_yaxes(categoryorder="array", categoryarray=rows[::-1])
    fig.update_xaxes(title_text=title_time, range=[0, max(C.HORIZON + 120, 1.0)] if orders is not None and len(orders) > 12 else None)
    fig.update_layout(barmode="overlay")
    return _base(fig, 120 + 45 * len(rows))


def build_stack(stack):
    """Zahl der wartenden (angenommenen, noch nicht gestarteten) Aufträge über die Zeit."""
    fig = go.Figure()
    xs, ys = [0.0], [0]
    for t, n in stack:
        xs += [t, t]
        ys += [ys[-1], n]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#2F6B65", width=2, shape="linear"), fill="tozeroy", fillcolor="rgba(47,107,101,0.15)", hovertemplate="Zeit %{x:.0f}: %{y} wartend<extra></extra>"))
    fig.update_xaxes(title_text="Zeit in Minuten")
    fig.update_yaxes(title_text="Wartende Aufträge", rangemode="tozero")
    return _base(fig, 240)


def build_map(inst, res, legend=True):
    """Karte: Depot (Quadrat), angenommene Aufträge (Kreise, Größe = Last), abgelehnte (Kreuze); jede gefahrene Route eine Farbe."""
    xs = [inst.depot[0]] + [o["x"] for o in inst.orders]
    ys = [inst.depot[1]] + [o["y"] for o in inst.orders]
    pad = 0.08 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    for i, (start, v, customers, dur, latest) in enumerate(res["dispatches"]):
        pts = [inst.depot] + [(inst.orders[c - 1]["x"], inst.orders[c - 1]["y"]) for c in customers] + [inst.depot]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color=C.ROUTE_COLORS[i % len(C.ROUTE_COLORS)], width=2), hoverinfo="skip",
                                 name=f"Fahrt {i + 1} (ab {start:.0f})", showlegend=legend and len(res["dispatches"]) <= 8))
    acc = {oid: ok for _, oid, ok in res["decisions"]}
    ok_ = [o for o in inst.orders if acc.get(o["id"])]
    no_ = [o for o in inst.orders if not acc.get(o["id"])]
    fig.add_trace(go.Scatter(x=[o["x"] for o in ok_], y=[o["y"] for o in ok_], mode="markers", marker=dict(size=[6 + 2.5 * o["q"] for o in ok_], color="rgba(150,150,150,0.6)", line=dict(color="#555", width=1)),
                             customdata=[[o["id"], o["q"], o["t"]] for o in ok_], hovertemplate="Auftrag %{customdata[0]}: Last %{customdata[1]}, Eingang %{customdata[2]:.0f}<extra>angenommen</extra>", name="angenommen", showlegend=legend))
    if no_:
        fig.add_trace(go.Scatter(x=[o["x"] for o in no_], y=[o["y"] for o in no_], mode="markers", marker=dict(symbol="x", size=9, color="#c0504d"),
                                 customdata=[[o["id"], o["q"], o["t"]] for o in no_], hovertemplate="Auftrag %{customdata[0]}: Eingang %{customdata[2]:.0f}<extra>abgelehnt</extra>", name="abgelehnt", showlegend=legend))
    fig.add_trace(go.Scatter(x=[inst.depot[0]], y=[inst.depot[1]], mode="markers", marker=dict(symbol="square", size=14, color="#222"), name="Depot", hoverinfo="skip", showlegend=legend))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig = _base(fig, 400 if legend else 300)
    if not legend:
        fig.update_layout(showlegend=False)
    return fig


def build_tau_lines(cell_stats: dict, cells):
    """Gewinn je Tag nach der Wartezeit tau (ohne Schwelle) für jede Zelle."""
    fig = go.Figure()
    labels = ["0", "10", "20", "40", "∞"]
    for i, cell in enumerate(cells):
        st_ = cell_stats[cell]
        fig.add_trace(go.Scatter(x=labels, y=[st_[k]["profit"] for k in C.TAU_KEYS], mode="lines+markers", name=f"{cell[0]} je Stunde, K = {cell[1]}",
                                 line=dict(color=C.ROUTE_COLORS[i % len(C.ROUTE_COLORS)], width=3), hovertemplate="tau %{x}: Gewinn %{y:.0f}<extra></extra>"))
    fig.update_xaxes(title_text="Wartezeit tau in Minuten (0 = Sofort, ∞ = Spätestens)")
    fig.update_yaxes(title_text="Mittlerer Gewinn je Tag")
    fig = _base(fig, 380)
    fig.update_layout(legend=dict(orientation="h", y=-0.35))
    return fig
