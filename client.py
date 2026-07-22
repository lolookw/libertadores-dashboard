"""Cliente HTTP delgado para la Libertadores API.

El dashboard NO toca la base de datos ni el CSV directamente — todo pasa por
la API REST del proyecto hermano (github.com/lolookw/libertadores-api). Es
la pieza que cierra la serie: dataset -> modelo -> API -> dashboard.
"""
from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 15


class ApiError(RuntimeError):
    pass


def _get(path: str, params: dict | None = None):
    try:
        resp = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        raise ApiError(
            f"No se pudo consultar {API_BASE_URL}{path}. "
            f"Si la API está en un free tier puede tardar ~30-50s en despertar "
            f"tras estar inactiva — probá de nuevo en un momento. ({exc})"
        ) from exc


@st.cache_data(ttl=300, show_spinner=False)
def get_summary() -> dict:
    return _get("/summary")


@st.cache_data(ttl=300, show_spinner=False)
def get_season_summary() -> list[dict]:
    return _get("/stats/season-summary")


@st.cache_data(ttl=300, show_spinner=False)
def get_standings(season: int | None) -> list[dict]:
    params = {"limit": 200}
    if season is not None:
        params["season"] = season
    return _get("/stats/standings", params=params)


@st.cache_data(ttl=300, show_spinner=False)
def get_top_scorers(limit: int = 15) -> list[dict]:
    return _get("/stats/top-scorers", params={"limit": limit})


@st.cache_data(ttl=300, show_spinner=False)
def get_elo_ranking(limit: int = 20) -> list[dict]:
    return _get("/stats/elo", params={"limit": limit})


@st.cache_data(ttl=300, show_spinner=False)
def get_teams(limit: int = 200) -> list[dict]:
    return _get("/teams", params={"limit": limit})


@st.cache_data(ttl=300, show_spinner=False)
def get_elo_timeline(team_id: int) -> list[dict]:
    return _get(f"/stats/elo/{team_id}")


@st.cache_data(ttl=300, show_spinner=False)
def get_head_to_head(team1_id: int, team2_id: int) -> dict:
    return _get("/stats/head-to-head", params={"team1": team1_id, "team2": team2_id})


def api_is_up() -> bool:
    try:
        health = _get("/health")
        return bool(health.get("status") == "ok")
    except ApiError:
        return False
