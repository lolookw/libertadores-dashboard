"""Tests del dashboard.

Mockea la capa HTTP (client._get) con datos con forma real de la API, y usa
streamlit.testing.v1.AppTest para correr el script completo (sin browser) y
verificar que renderiza sin excepciones y que los datos llegan a los
componentes esperados. La API en sí ya tiene su propia suite de tests en su
repo — acá se valida el dashboard, no se repite esa cobertura.
"""
from __future__ import annotations

from unittest.mock import patch

from streamlit.testing.v1 import AppTest

FAKE_SUMMARY = {
    "total_matches": 10,
    "total_teams": 4,
    "total_seasons": 2,
    "first_season": 2000,
    "last_season": 2001,
    "total_goals": 25,
    "avg_goals_per_match": 2.5,
    "home_win_pct": 50.0,
}

FAKE_SEASON_SUMMARY = [
    {
        "season": 2000, "matches": 5, "avg_goals": 2.2,
        "home_win_pct": 40.0, "draw_pct": 40.0, "away_win_pct": 20.0,
    },
    {
        "season": 2001, "matches": 5, "avg_goals": 2.8,
        "home_win_pct": 60.0, "draw_pct": 20.0, "away_win_pct": 20.0,
    },
]

FAKE_STANDINGS = [
    {"position": 1, "team": "Boca", "country": "Argentina", "played": 4, "points": 10,
     "wins": 3, "draws": 1, "losses": 0, "goals_for": 8, "goals_against": 3, "goal_diff": 5},
    {"position": 2, "team": "River", "country": "Argentina", "played": 4, "points": 6,
     "wins": 2, "draws": 0, "losses": 2, "goals_for": 6, "goals_against": 5, "goal_diff": 1},
]

FAKE_TOP_SCORERS = [
    {"team": "Boca", "country": "Argentina", "goals_for": 8, "played": 4, "goals_per_match": 2.0},
    {"team": "River", "country": "Argentina", "goals_for": 6, "played": 4, "goals_per_match": 1.5},
]

FAKE_ELO_RANKING = [
    {"team": "Boca", "country": "Argentina", "elo": 1520.0},
    {"team": "River", "country": "Argentina", "elo": 1490.0},
]

FAKE_TEAMS = [
    {"id": 1, "name": "Boca", "country": "Argentina", "matches_played": 4},
    {"id": 2, "name": "River", "country": "Argentina", "matches_played": 4},
]

FAKE_ELO_TIMELINE = [
    {"match_date": "2000-03-01", "season": 2000, "match_id": 1, "opponent": "River",
     "is_home": True, "elo_before": 1500.0, "elo_after": 1510.0, "delta": 10.0},
    {"match_date": "2000-03-08", "season": 2000, "match_id": 2, "opponent": "Peñarol",
     "is_home": False, "elo_before": 1510.0, "elo_after": 1520.0, "delta": 10.0},
]

FAKE_H2H = {
    "matches": 2, "team1_wins": 1, "draws": 1, "team2_wins": 0,
    "team1_goals": 3, "team2_goals": 1,
}


def fake_get(path, params=None):
    if path == "/health":
        return {"status": "ok", "database": True, "version": "1.0.0"}
    if path == "/summary":
        return FAKE_SUMMARY
    if path == "/stats/season-summary":
        return FAKE_SEASON_SUMMARY
    if path == "/stats/standings":
        return FAKE_STANDINGS
    if path == "/stats/top-scorers":
        return FAKE_TOP_SCORERS
    if path == "/stats/elo":
        return FAKE_ELO_RANKING
    if path == "/teams":
        return FAKE_TEAMS
    if path.startswith("/stats/elo/"):
        return FAKE_ELO_TIMELINE
    if path == "/stats/head-to-head":
        return FAKE_H2H
    raise AssertionError(f"path no mockeado: {path}")


def _run_app():
    with patch("client._get", side_effect=fake_get):
        at = AppTest.from_file("app.py")
        at.run(timeout=30)
    return at


def test_dashboard_renders_without_exceptions():
    at = _run_app()
    assert not at.exception


def test_kpi_metrics_show_summary_data():
    at = _run_app()
    values = {m.label: m.value for m in at.metric}
    assert values["Partidos"] == "10"
    assert values["Equipos"] == "4"
    assert values["Goles / partido"] == "2.5"
    assert values["Localía"] == "50.0%"


def test_standings_and_elo_tables_render():
    at = _run_app()
    assert not at.exception
    # standings + ranking Elo -> al menos 2 dataframes en pantalla
    assert len(at.dataframe) >= 2


def test_charts_render():
    at = _run_app()
    assert not at.exception
    # goles/temporada, resultado por localía, goleadores, evolución Elo
    assert len(at.get("plotly_chart")) == 4


def test_head_to_head_section_computes_metrics():
    at = _run_app()
    assert not at.exception
    values = {m.label: m.value for m in at.metric}
    assert values["Partidos jugados"] == "2"
    assert values["Victorias Boca"] == "1"
    assert values["Victorias River"] == "0"
    assert values["Goles (1 vs 2)"] == "3–1"
