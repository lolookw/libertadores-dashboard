"""Libertadores Dashboard — front-end interactivo sobre la Libertadores API.

Cuarto capítulo de la serie: dataset -> modelo -> API -> dashboard.
Todo el dato viene de la API (ver client.py); esta app no toca Postgres ni CSVs.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import client

ACCENT = "#E8A233"
MUTED = "#A9B6AC"
SURFACE = "#16211A"

st.set_page_config(
    page_title="Libertadores Dashboard",
    page_icon="⚽",
    layout="wide",
)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#EDEFE6", family="sans-serif"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)


def _apply_layout(fig: go.Figure, **overrides) -> go.Figure:
    fig.update_layout(**{**PLOTLY_LAYOUT, **overrides})
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.08)")
    return fig


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("⚽ Libertadores Dashboard")
st.caption(
    "Copa Libertadores 1996–2024 · datos servidos en vivo por "
    f"[Libertadores API]({client.API_BASE_URL}/docs) — "
    "[dataset](https://github.com/lolookw/Libertadores-1996-2024) · "
    "[modelo](https://github.com/lolookw/Modelo-Libertadores) · "
    "[API](https://github.com/lolookw/libertadores-api)"
)

if not client.api_is_up():
    st.warning(
        "La API todavía no responde. Si está en un free tier (Render) puede tardar "
        "hasta ~1 minuto en despertar la primera vez — recargá la página en un rato.",
        icon="⏳",
    )
    st.stop()

try:
    summary = client.get_summary()
except client.ApiError as e:
    st.error(str(e))
    st.stop()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Partidos", f"{summary['total_matches']:,}".replace(",", "."))
k2.metric("Equipos", summary["total_teams"])
k3.metric("Temporadas", f"{summary['first_season']}–{summary['last_season']}")
k4.metric("Goles / partido", summary["avg_goals_per_match"])
k5.metric("Localía", f"{summary['home_win_pct']}%")

st.divider()

# --------------------------------------------------------------------------- #
# Evolución por temporada
# --------------------------------------------------------------------------- #
st.subheader("Evolución por temporada")
season_df = pd.DataFrame(client.get_season_summary())

col_a, col_b = st.columns(2)

with col_a:
    fig_goals = go.Figure()
    fig_goals.add_trace(
        go.Scatter(
            x=season_df["season"],
            y=season_df["avg_goals"],
            mode="lines+markers",
            line=dict(color=ACCENT, width=2),
            marker=dict(size=5),
            name="Goles/partido",
        )
    )
    _apply_layout(fig_goals, title="Goles por partido", showlegend=False, height=340)
    st.plotly_chart(fig_goals, use_container_width=True)

with col_b:
    fig_res = go.Figure()
    for col, label, color in [
        ("home_win_pct", "Local", ACCENT),
        ("draw_pct", "Empate", MUTED),
        ("away_win_pct", "Visitante", "#5A5F52"),
    ]:
        fig_res.add_trace(
            go.Scatter(
                x=season_df["season"],
                y=season_df[col],
                mode="lines",
                stackgroup="one",
                name=label,
                line=dict(width=0.5, color=color),
            )
        )
    _apply_layout(fig_res, title="Resultado por localía (%)", height=340)
    st.plotly_chart(fig_res, use_container_width=True)

st.divider()

# --------------------------------------------------------------------------- #
# Tabla de posiciones + goleadores
# --------------------------------------------------------------------------- #
col_left, col_right = st.columns([1.3, 1])

with col_left:
    st.subheader("Tabla de posiciones")
    seasons = ["Histórico"] + sorted(season_df["season"].tolist(), reverse=True)
    chosen = st.selectbox("Temporada", seasons, key="standings_season")
    season_filter = None if chosen == "Histórico" else int(chosen)
    standings = pd.DataFrame(client.get_standings(season_filter))
    st.dataframe(
        standings.rename(
            columns={
                "position": "#",
                "team": "Equipo",
                "country": "País",
                "played": "PJ",
                "points": "Pts",
                "wins": "G",
                "draws": "E",
                "losses": "P",
                "goals_for": "GF",
                "goals_against": "GC",
                "goal_diff": "DG",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=460,
    )

with col_right:
    st.subheader("Equipos más goleadores")
    scorers = pd.DataFrame(client.get_top_scorers(limit=15)).sort_values("goals_for")
    fig_scorers = go.Figure(
        go.Bar(
            x=scorers["goals_for"],
            y=scorers["team"],
            orientation="h",
            marker_color=ACCENT,
        )
    )
    _apply_layout(fig_scorers, title=None, height=460)
    st.plotly_chart(fig_scorers, use_container_width=True)

st.divider()

# --------------------------------------------------------------------------- #
# Elo
# --------------------------------------------------------------------------- #
st.subheader("Rating Elo")
col_rank, col_timeline = st.columns([1, 1.4])

teams = pd.DataFrame(client.get_teams(limit=200))
team_by_name = dict(zip(teams["name"], teams["id"], strict=False))

with col_rank:
    st.caption("Ranking actual (top 20)")
    elo_rank = pd.DataFrame(client.get_elo_ranking(limit=20))
    st.dataframe(
        elo_rank.rename(columns={"team": "Equipo", "country": "País", "elo": "Elo"}),
        hide_index=True,
        use_container_width=True,
        height=420,
    )

with col_timeline:
    default_team = "River Plate" if "River Plate" in team_by_name else teams["name"].iloc[0]
    chosen_team = st.selectbox(
        "Evolución de Elo por equipo",
        sorted(team_by_name.keys()),
        index=sorted(team_by_name.keys()).index(default_team),
    )
    timeline = pd.DataFrame(client.get_elo_timeline(team_by_name[chosen_team]))
    if timeline.empty:
        st.info("Sin partidos registrados para este equipo.")
    else:
        fig_elo = go.Figure(
            go.Scatter(
                x=pd.to_datetime(timeline["match_date"]),
                y=timeline["elo_after"],
                mode="lines",
                line=dict(color=ACCENT, width=2),
                fill="tozeroy",
                fillcolor="rgba(232,162,51,0.12)",
            )
        )
        fig_elo.add_hline(y=1500, line_dash="dot", line_color=MUTED, opacity=0.6)
        _apply_layout(fig_elo, title=f"Elo — {chosen_team}", height=420)
        st.plotly_chart(fig_elo, use_container_width=True)

st.divider()

# --------------------------------------------------------------------------- #
# Head to head
# --------------------------------------------------------------------------- #
st.subheader("Historial entre dos equipos")
team_names = sorted(team_by_name.keys())
h2h_col1, h2h_col2, h2h_col3 = st.columns([1, 1, 1])
with h2h_col1:
    t1_name = st.selectbox("Equipo 1", team_names, index=0, key="h2h_t1")
with h2h_col2:
    default_idx = 1 if len(team_names) > 1 else 0
    t2_name = st.selectbox("Equipo 2", team_names, index=default_idx, key="h2h_t2")

if t1_name == t2_name:
    st.info("Elegí dos equipos distintos para comparar.")
else:
    h2h = client.get_head_to_head(team_by_name[t1_name], team_by_name[t2_name])
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Partidos jugados", h2h["matches"])
    c2.metric(f"Victorias {t1_name}", h2h["team1_wins"])
    c3.metric("Empates", h2h["draws"])
    c4.metric(f"Victorias {t2_name}", h2h["team2_wins"])
    c5.metric("Goles (1 vs 2)", f"{h2h['team1_goals']}–{h2h['team2_goals']}")

st.divider()
st.caption(
    "Datos: RSSSF, vía el pipeline de [Libertadores 1996–2024]"
    "(https://github.com/lolookw/Libertadores-1996-2024). "
    "Construido por [Lorenzo Kwiatkowski](https://github.com/lolookw)."
)
