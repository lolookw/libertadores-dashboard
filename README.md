# Libertadores Dashboard

Dashboard interactivo sobre la Copa Libertadores (1996–2024): tabla de posiciones, evolución
de goles y localía por temporada, goleadores históricos, ranking y evolución de rating Elo, y
comparador cabeza a cabeza entre equipos.

Es el **cuarto capítulo** de una serie de proyectos de datos:

1. **[Libertadores 1996–2024](https://github.com/lolookw/Libertadores-1996-2024)** — construye el dataset desde texto plano (parsing + QA + normalización + EDA).
2. **[Modelo Libertadores](https://github.com/lolookw/Modelo-Libertadores)** — modela el resultado 1X2 (Elo + regresión logística + calibración).
3. **[Libertadores API](https://github.com/lolookw/libertadores-api)** — expone el dataset como servicio REST (SQL crudo, Docker, tests, CI).
4. **Libertadores Dashboard** *(este repo)* — la capa visual: consume la API, no la base de datos.

---

## Por qué consume la API en vez de leer el CSV

Podría haber leído `matches.csv` directo con pandas — es más simple. No lo hice a propósito: el
dashboard llama a la **Libertadores API** por HTTP (ver `client.py`), igual que lo haría
cualquier cliente externo. Eso fuerza una separación real entre la capa de datos/backend y la de
presentación, y es la pieza que convierte cuatro proyectos sueltos en **una arquitectura**.

## Features

- **KPIs generales:** partidos, equipos, temporadas, goles/partido, % de localía.
- **Evolución por temporada:** goles por partido y distribución local/empate/visitante a lo largo
  de 29 temporadas (`/stats/season-summary`).
- **Tabla de posiciones:** histórica o filtrada por temporada.
- **Goleadores históricos** y **ranking Elo actual**.
- **Evolución de Elo** de un equipo elegido, partido a partido.
- **Head-to-head:** comparación directa entre dos equipos.

## Stack

Streamlit · Plotly · pandas · requests · pytest (`streamlit.testing.v1.AppTest`) · ruff

---

## Arranque rápido

Necesita la [Libertadores API](https://github.com/lolookw/libertadores-api) corriendo (local
con `docker compose up`, o la URL desplegada).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export API_BASE_URL=http://localhost:8000   # default si no se setea
streamlit run app.py
```

Abre en `http://localhost:8501`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest        # corre la app completa con streamlit.testing.v1.AppTest, sin browser
ruff check .
```

Los tests mockean la capa HTTP (`client._get`) con respuestas con la forma real de la API y
corren `app.py` de punta a punta verificando que renderiza sin excepciones y que los KPIs,
tablas y gráficos reciben los datos esperados. La API tiene su propia suite de tests en su
repo — acá no se repite esa cobertura, se valida específicamente la capa de presentación.

## Deploy

Gratis en [Streamlit Community Cloud](https://streamlit.io/cloud): conectás el repo de GitHub,
seteás el secret `API_BASE_URL` apuntando a la API desplegada, y listo — redeploya solo en cada
push a `main`.

## Licencia

MIT
